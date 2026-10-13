"""BC-only runs retain an epoch axis and complete diagnostics through completion."""

import json
from pathlib import Path
from typing import Any, cast

from kagg_revue.monitor.artifacts import RunRepository
from kagg_revue.monitor.config import MonitorSettings


def test_bc_history_coverage_and_completed_state_are_separate_from_ppo(tmp_path: Path) -> None:
    """Read real artifact shapes, ignoring unrelated PPO points and a partial batch line."""
    run = tmp_path / "outputs/learning/compact"
    (run / "pretraining").mkdir(parents=True)
    artifacts = {
        "resolved-config.json": {
            "pretraining_only": True,
            "initial_weights": {"run": "outputs/learning/parent", "checkpoint": "initial.pt"},
            "updates": 100000,
            "precision": "bf16",
            "demonstrations": {"epochs": 100, "batch_rows": 11504, "learning_rate": 0.0001},
            "execution": {"devices": ["cuda:0", "cuda:1"]},
        },
        "run-status.json": {"status": "complete"},
        "learning-progress.json": {"phase": "complete", "update": 0},
        "pretraining/progress.json": {
            "cursor": 23900,
            "rows": 274263600,
            "optimizer_steps": 23900,
            "records": [{"epoch": i + 1} for i in range(100)],
        },
        "demonstration-qualification.json": {
            "all_array_hashes_verified": True,
            "coverage": {"train": {"usable_rows": 2742636, "context_rows": 2742985}},
            "selected_teacher_trajectories": {"Teacher": 12},
        },
    }
    for name, value in artifacts.items():
        (run / name).write_text(json.dumps(value))
    (run / "metrics.jsonl").write_text(
        json.dumps({"update": 1000, "optimization": {"loss": 9}}) + "\n"
    )
    (run / "pretraining/metrics.jsonl").write_text(
        json.dumps(
            {
                "epoch": 100,
                "training": {"action_nll": 0.5},
                "validation": {"action_nll": 0.6, "unit_target_accuracy": 0.8},
                "system": {
                    "elapsed_seconds": 5000,
                    "training_seconds": 40,
                    "validation_seconds": 2,
                },
            }
        )
        + "\n"
    )
    (run / "pretraining/batches.jsonl").write_text('{"batch":23900,"rows":100}\n{"batch":')
    repository = RunRepository(
        tmp_path,
        MonitorSettings(
            outputs_dir=Path("outputs"),
            port=8765,
            refresh_seconds=5,
            stale_after_seconds=180,
            max_points=400,
        ),
    )
    detail = cast(dict[str, Any], repository.detail("learning/compact", set(), []))
    assert detail["run"]["kind"] == "bc"
    assert detail["run"]["status"] == "trained"
    assert detail["run"]["progress"]["current"] == 100
    assert detail["run"]["progress"]["target"] == 100
    assert detail["run"]["progress"]["eta_seconds"] == 0
    assert detail["metrics"]["latest"]["bc/system/epoch_seconds"] == 42
    assert not any(tag.startswith("rl/") for tag in detail["metrics"]["latest"])
    assert detail["pretraining"]["total_training_rows"] == 274263600
    assert detail["pretraining"]["batches_per_epoch"] == 239
    assert detail["pretraining"]["completed_epochs"] == 100
    assert detail["pretraining"]["initial_weights"]["run"] == "outputs/learning/parent"
    assert detail["pretraining"]["batches"] == [{"batch": 23900, "rows": 100}]
