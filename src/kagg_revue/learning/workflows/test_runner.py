"""Exercise automatic best-weight handoff and suppression on cancelled or failed BC."""

import json
import os
import signal
import time
from pathlib import Path
from typing import Any

import pytest
import torch
from hydra import compose, initialize_config_dir
from omegaconf import OmegaConf

from kagg_revue.artifacts.io import digest, write_json
from kagg_revue.learning.config import Experiment
from kagg_revue.learning.workflows import runner
from kagg_revue.learning.workflows.config import Workflow
from kagg_revue.learning.workflows.process import Supervisor


def _workflow(name: str) -> Workflow:
    with initialize_config_dir(
        version_base=None, config_dir=str(Path(__file__).resolve().parents[4] / "configs")
    ):
        config = compose(config_name=name)
        return Workflow.model_validate(OmegaConf.to_container(config.workflow, resolve=True))


def _finished_bc(workflow: Workflow) -> tuple[str, dict[str, Any]]:
    """Register a BC whose last epoch is worse than its selected validation-best epoch."""
    assert workflow.bc.demonstrations is not None
    directory = workflow.bc.output_dir
    (directory / "pretraining").mkdir(parents=True)
    selected = "pretraining/shard-000002.pt"
    torch.save({"model": {"x": torch.ones(1)}, "lineage": {
        "run_id": "bc-test", "dataset_sha256": workflow.bc.demonstrations.sha256,
    }}, directory / selected)
    state: dict[str, Any] = {
        "run_id": "bc-test", "rl_initial": selected,
        "members": {selected: digest(directory / selected)},
        "pretraining": {
            "completion_reason": "patience",
            "early_stopping": {"best_epoch": 2, "best_nll": 0.5, "best_member": selected},
            "records": [{"epoch": 1, "selection_nll": 0.6},
                        {"epoch": 2, "selection_nll": 0.5},
                        {"epoch": 3, "selection_nll": 0.7}],
        },
    }
    write_json(directory / "state.json", state)
    return selected, state


@pytest.mark.parametrize("outcome", ["complete", "stopped", "failed", "cancelled", "corrupt"])
def test_handoff_requires_normal_completion_and_selects_best_epoch(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, outcome: str,
) -> None:
    """A worsening final epoch cannot replace the best checkpoint or bypass cancellation."""
    workflow = _workflow("workflow_watch6_u2137_bc_to_rl_20260927")
    assert workflow.bc.demonstrations is not None
    assert workflow.bc.demonstrations.loss is not None
    assert workflow.bc.demonstrations.epoch_checkpoint_interval == 4
    assert workflow.rl.learning_rate_warmup_updates == 300
    monkeypatch.chdir(tmp_path)
    directory = workflow.bc.output_dir
    selected, state = _finished_bc(workflow)
    if outcome == "corrupt":
        (directory / selected).write_bytes(b"changed after registration")
    events: list[str] = []

    def child(self: Supervisor, command: list[str], **kwargs: Any) -> int | None:
        assert command[2] == "kagg_revue.learning.workflows.runner"
        stage = Path(command[-1]).name.split("-")[0]
        events.append(stage)
        if stage == "bc" and outcome == "failed":
            return 1
        if stage == "bc" and outcome == "cancelled":
            self.cancelled = True
            return None
        experiment = Experiment.model_validate_json(Path(command[-1]).read_text())
        write_json(experiment.output_dir / "run-status.json", {
            "status": "stopped" if outcome == "stopped" else "complete",
        })
        return 0

    def bootstrap(experiment: Experiment, archive: Any) -> dict[str, Any]:
        events.append("bootstrap")
        assert experiment.initial_weights is not None
        assert experiment.initial_weights.checkpoint == selected
        assert experiment.initial_weights.sha256 == state["members"][selected]
        assert experiment.learning_rate_warmup_updates == 300
        assert archive == workflow.historical_archive
        experiment.output_dir.mkdir(parents=True)
        return {"verified": True}

    monkeypatch.setattr(Supervisor, "run", child)
    monkeypatch.setattr(runner, "prepare", bootstrap)
    if outcome in {"failed", "corrupt"}:
        with pytest.raises((ValueError, RuntimeError)):
            runner.execute(workflow)
    else:
        runner.execute(workflow)
    assert events == (["bc", "bootstrap", "rl"] if outcome == "complete" else ["bc"])
    status = json.loads((workflow.output_dir / "status.json").read_text())
    assert status["status"] == ("failed" if outcome == "corrupt" else outcome)


@pytest.mark.parametrize(
    ("recorded", "expected"),
    [("complete", "complete"), ("stopped", "stopped"), ("running", "stopped"), (None, "cancelled")],
)
def test_attached_bc_is_awaited_and_never_launched(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, recorded: str | None, expected: str,
) -> None:
    """Only a normally completed external BC reaches PPO; a vanished process has failed."""
    workflow = _workflow("workflow_strength_canonical_bc_to_rl_20260928")
    assert workflow.attached_bc and workflow.rl.learning_rate_warmup_updates == 300
    monkeypatch.chdir(tmp_path)
    selected, _ = _finished_bc(workflow)
    write_json(workflow.bc.output_dir / "run-status.json", {
        "status": recorded or "running", "pid": os.getpid() if recorded is None else 1073741824,
    })
    events: list[str] = []

    def child(self: Supervisor, command: list[str], **kwargs: Any) -> int | None:
        events.append(Path(command[-1]).name.split("-")[0])
        experiment = Experiment.model_validate_json(Path(command[-1]).read_text())
        write_json(experiment.output_dir / "run-status.json", {"status": "complete"})
        return 0

    def bootstrap(experiment: Experiment, archive: Any) -> dict[str, Any]:
        events.append("bootstrap")
        assert experiment.initial_weights is not None
        assert experiment.initial_weights.checkpoint == selected
        experiment.output_dir.mkdir(parents=True)
        return {"verified": True}

    monkeypatch.setattr(Supervisor, "run", child)
    monkeypatch.setattr(runner, "prepare", bootstrap)
    # The live "BC" is this process; stopping the workflow while it waits cancels PPO.
    monkeypatch.setattr(time, "sleep", lambda _: os.kill(os.getpid(), signal.SIGTERM))
    runner.execute(workflow)
    assert events == (["bootstrap", "rl"] if expected == "complete" else [])
    status = json.loads((workflow.output_dir / "status.json").read_text())
    assert status["status"] == expected
