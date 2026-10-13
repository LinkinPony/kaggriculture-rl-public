"""The passive observer preserves completed evidence and reports numerical failure."""

import json
import os
from pathlib import Path

import pytest

from kagg_revue.artifacts.io import digest, write_json
from kagg_revue.monitor import training_watch


@pytest.mark.parametrize("nonfinite", [False, True])
def test_observer_finishes_or_records_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, nonfinite: bool
) -> None:
    """Exercise committed metrics, checkpoint identity and terminal observer status."""
    run = tmp_path / "run"
    workflow = tmp_path / "workflow"
    output = tmp_path / "observation"
    (run / "checkpoints").mkdir(parents=True)
    workflow.mkdir()
    checkpoint = run / "checkpoints/update-000001.pt"
    checkpoint.write_bytes(b"checkpoint fixture")
    write_json(workflow / "status.json", {"pid": os.getpid(), "status": "running", "stage": "rl"})
    write_json(run / "run-status.json", {"pid": os.getpid()})
    row = {
        "update": 1,
        "physical_games": 128,
        "workers": [
            {
                "rank": rank,
                "reward_values": [-1, 1],
                "optimization": {
                    "actor_learning_rate": 1e-7,
                    "critic_learning_rate": 1e-6,
                    "reference_kl_weight": 0.3,
                    "actor_steps": 4,
                    "critic_steps": 4,
                    "value_loss": float("nan") if nonfinite and rank == 1 else 0.5,
                },
            }
            for rank in range(2)
        ],
    }
    write_json(
        run / "state.json",
        {
            "run_id": "fixture",
            "completed_update": 1,
            "records": [row],
            "members": {"checkpoints/update-000001.pt": digest(checkpoint)},
            "protocol": {
                "games": 128,
                "execution": {"devices": ["cuda:0", "cuda:1"]},
                "learning_rate_warmup_updates": 100,
                "actor_learning_rate": 1e-5,
                "critic_learning_rate": 1e-4,
                "reference_kl_weight": 0.3,
            },
        },
    )
    monkeypatch.setattr(
        training_watch,
        "health",
        lambda *args: {
            "training_update": 1,
            "training_heartbeat_age": 0,
            "gpus": [[0, 30000, 100000, 90], [1, 30000, 100000, 90]],
        },
    )
    config = training_watch.Tracking(run=run, workflow=workflow, output=output, target_update=1)
    if nonfinite:
        with pytest.raises(ValueError, match="nonfinite optimization diagnostic"):
            training_watch.track(config)
        assert (output / "alert.json").is_file()
        assert not (output / "completion.json").exists()
    else:
        training_watch.track(config)
        assert digest(output / checkpoint.name) == digest(checkpoint)
        assert json.loads((output / "completion.json").read_text())["verified_update"] == 1
    status = json.loads((output / "status.json").read_text())
    assert status["status"] == ("failed" if nonfinite else "complete")
    assert json.loads((workflow / "status.json").read_text())["status"] == "running"
