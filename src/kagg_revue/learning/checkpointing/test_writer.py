"""Asynchronous save isolation, bounded work and publication failure semantics."""

import json
import threading
from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
import torch

from kagg_revue.artifacts import serialization
from kagg_revue.learning import state as artifacts
from kagg_revue.learning.adapter import runtime_settings
from kagg_revue.learning.checkpointing import writer
from kagg_revue.learning.config import Evaluation, Experiment, Population
from kagg_revue.learning.execution import Execution
from kagg_revue.learning.storage.roles import full_members


@dataclass
class Layout:
    """Minimal model metadata for a storage-only test."""

    features: int = 4


def setup(directory: Path) -> tuple[Experiment, dict[str, Any], Any]:
    """Create nonempty Adam state without an environment or a policy rollout."""
    policy = torch.nn.Linear(4, 3)
    policy.layout = Layout()  # type: ignore[assignment]
    critic = torch.nn.Linear(4, 1)
    actor_optimizer = torch.optim.Adam(policy.parameters())
    critic_optimizer = torch.optim.Adam(critic.parameters())
    (policy(torch.ones(2, 4)).sum() + critic(torch.ones(2, 4)).sum()).backward()
    actor_optimizer.step()
    critic_optimizer.step()
    learner = SimpleNamespace(
        policy=policy,
        critic=critic,
        actor_optimizer=actor_optimizer,
        critic_optimizer=critic_optimizer,
        device=torch.device("cpu"),
    )
    config = Experiment(
        output_dir=Path("outputs/learning/test-async-checkpoint"),
        checkpoint_interval=1,
        checkpoint_keep_recent=None,
        updates=20,
        evaluation=Evaluation(interval=20),
        execution=Execution(async_checkpoint=True),
    ).model_copy(update={"output_dir": directory})
    state = {
        "run_id": "test",
        "members": {"initial.pt": "root"},
        "pool": ["initial.pt"],
        "latest": "initial.pt",
        "completed_update": 0,
        "records": [],
        "pfsp": {"last_update": 1},
    }
    return config, state, learner


def test_delayed_writer_is_independent_and_bounded(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Training may mutate every live weight while the queued snapshot remains exact."""
    config, state, learner = setup(tmp_path)
    original = learner.policy.weight.detach().clone()
    entered, release = threading.Event(), threading.Event()
    save = serialization.save

    def delayed(payload: Any, path: Path) -> str:
        entered.set()
        assert release.wait(10)
        return save(payload, path)

    monkeypatch.setattr(writer, "save", delayed)
    with writer.CheckpointWriter(config, runtime_settings(config), state, learner) as output:
        output.record(1, {"update": 1})
        assert entered.wait(10)
        try:
            assert state["completed_update"] == 0
            assert not (tmp_path / "state.json").exists()
            with pytest.raises(RuntimeError, match="bounded"):
                output.submit()
            with torch.no_grad():
                learner.policy.weight.add_(100)
            with pytest.raises(RuntimeError, match="previous checkpoint"):
                output.record(2, {"update": 2})
        finally:
            release.set()
        output.finish()
    payload = torch.load(tmp_path / state["latest"], weights_only=False)
    assert torch.equal(payload["model"]["weight"], original)
    assert payload["lineage"]["parent_sha256"] == "root"
    assert {int(v["step"]) for v in payload["actor_optimizer"]["state"].values()} == {1}
    assert json.loads((tmp_path / "state.json").read_text())["completed_update"] == 1


def test_background_failure_never_publishes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """An I/O failure reaches training while its previous authoritative state stays intact."""
    config, state, learner = setup(tmp_path)
    (tmp_path / "state.json").write_text(json.dumps(state))

    def fail(payload: Any, path: Path) -> str:
        raise OSError("injected write failure")

    monkeypatch.setattr(writer, "save", fail)
    with writer.CheckpointWriter(config, runtime_settings(config), state, learner) as output:
        output.record(1, {"update": 1})
        with pytest.raises(RuntimeError, match="injected write failure"):
            output.finish()
    assert state["completed_update"] == 0
    assert json.loads((tmp_path / "state.json").read_text())["completed_update"] == 0


@pytest.mark.parametrize("asynchronous", [False, True])
def test_permanent_milestones_survive_recent_retention(tmp_path: Path, asynchronous: bool) -> None:
    """Both save paths retain complete U200/U400 even with regular saves every 3 updates."""
    config, state, learner = setup(tmp_path)
    config = config.model_copy(
        update={
            "checkpoint_interval": 3,
            "checkpoint_keep_recent": 2,
            "updates": 406,
            "population": Population(snapshot_interval=6),
            "evaluation": Evaluation(interval=600),
        }
    )
    settings = runtime_settings(config)
    original_rng = torch.get_rng_state().clone()
    with writer.CheckpointWriter(config, settings, state, learner) as output:
        for update in range(1, 407):
            if asynchronous:
                output.record(update, {"update": update})
                output.finish()
            else:
                artifacts.checkpoint(config, settings, state, learner, update, {"update": update})
    expected = {f"checkpoints/update-{i:06d}.pt" for i in (200, 400, 405, 406)}
    assert full_members(config, state) == expected
    assert {
        f"checkpoints/{path.name}" for path in (tmp_path / "checkpoints").glob("*.pt")
    } == expected
    for name in expected:
        assert name not in state.get("inference_artifacts", {})
        payload = torch.load(tmp_path / name, weights_only=False)
        assert torch.equal(payload["model"]["weight"], learner.policy.weight)
        assert {int(v["step"]) for v in payload["actor_optimizer"]["state"].values()} == {1}
        assert {int(v["step"]) for v in payload["critic_optimizer"]["state"].values()} == {1}
        assert torch.equal(payload["rng"]["cpu"], original_rng)
    assert json.loads((tmp_path / "state.json").read_text())["latest"].endswith("000406.pt")
