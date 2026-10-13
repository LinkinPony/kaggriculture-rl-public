"""GPU count changes require a recorded checkpoint boundary and preserve surviving RNGs."""

from pathlib import Path
from typing import Any

import pytest
import torch

from kagg_revue.learning import distributed
from kagg_revue.learning.config import Experiment
from kagg_revue.learning.execution import Execution


@pytest.mark.parametrize("before,after,rank", [(2, 1, 0), (1, 2, 0), (1, 2, 1)])
def test_recorded_transition_restores_or_seeds_ranks(
    monkeypatch: pytest.MonkeyPatch, before: int, after: int, rank: int
) -> None:
    """Reuse every surviving stream and deterministically initialize added ranks."""
    execution = Execution(devices=tuple(f"cuda:{i}" for i in range(after)))
    config = Experiment(output_dir=Path("outputs/learning/test"), execution=execution)
    workers = [{"cpu": torch.tensor([i]), "cuda": torch.tensor([i + 10])} for i in range(before)]
    payload = {"update": 7, "rng": {"workers": workers}}
    state = {
        "completed_update": 7,
        "latest": "checkpoint.pt",
        "members": {"checkpoint.pt": "checkpoint-hash"},
        "execution_history": [
            {
                "completed_update": 7,
                "checkpoint_sha256": "checkpoint-hash",
                "previous_protocol": {
                    "execution": {"devices": [f"cuda:{i}" for i in range(before)]}
                },
                "execution": execution.model_dump(mode="json"),
            }
        ],
    }
    observed: dict[str, Any] = {}
    monkeypatch.setattr(distributed, "rank_world", lambda: (rank, after))
    monkeypatch.setattr(torch, "set_rng_state", lambda value: observed.update(cpu=value))
    monkeypatch.setattr(
        torch.cuda, "set_rng_state", lambda value, device: observed.update(cuda=value)
    )
    monkeypatch.setattr(torch, "manual_seed", lambda value: observed.update(seed=value))
    distributed.restore_rng(payload, torch.device(f"cuda:{rank}"), config, state=state)
    if rank < before:
        assert torch.equal(observed["cpu"], workers[rank]["cpu"])
        assert torch.equal(observed["cuda"], workers[rank]["cuda"])
        assert "seed" not in observed
    else:
        assert observed == {"seed": config.seed + 1000000007 * rank + 7}


@pytest.mark.parametrize("field,value", [("completed_update", 6), ("checkpoint_sha256", "wrong")])
def test_transition_cannot_be_reused_for_another_checkpoint(
    monkeypatch: pytest.MonkeyPatch, field: str, value: Any
) -> None:
    """Keep the strict worker-count check outside the exact recorded transition."""
    execution = Execution(devices=("cuda:0",))
    config = Experiment(output_dir=Path("outputs/learning/test"), execution=execution)
    transition = {
        "completed_update": 7,
        "checkpoint_sha256": "checkpoint-hash",
        "previous_protocol": {"execution": {"devices": ["cuda:0", "cuda:1"]}},
        "execution": execution.model_dump(mode="json"),
        field: value,
    }
    state = {
        "completed_update": 7,
        "latest": "checkpoint.pt",
        "members": {"checkpoint.pt": "checkpoint-hash"},
        "execution_history": [transition],
    }
    monkeypatch.setattr(distributed, "rank_world", lambda: (0, 1))
    with pytest.raises(ValueError, match="worker count"):
        distributed.restore_rng(
            {"update": 7, "rng": {"workers": [{}, {}]}},
            torch.device("cuda:0"),
            config,
            state=state,
        )
