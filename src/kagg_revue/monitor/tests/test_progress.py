"""Large opponent pools remain visible in monitor API payloads."""

import json
from pathlib import Path

import pytest

from kagg_revue.monitor.artifacts import RunRepository
from kagg_revue.monitor.config import MonitorSettings


@pytest.mark.parametrize("league", [False, True])
def test_large_opponent_pool_reaches_run_details(tmp_path: Path, league: bool) -> None:
    """Preserve full PFSP snapshots after their size exceeds the old 64 KiB cap."""
    run = tmp_path / "outputs/learning/run"
    run.mkdir(parents=True)
    history = [
        {
            "kind": "history",
            "name": f"historical/budget-q100-top10-2d-20260913-s68001/update-{i:06d}.pt",
            "path": f"historical/budget-q100-top10-2d-20260913-s68001/update-{i:06d}.pt",
            "source_run": "outputs/learning/budget-q100-top10-2d-20260913-s68001",
            "sha256": f"{i:064x}",
            "key": f"history:{i:064x}",
            "update": i,
            "games": 128,
            "score": 0.25,
            "probability": 1 / 136,
        }
        for i in range(136)
    ]
    pfsp = {
        "enabled": True,
        "separate_scripts": True,
        "pool_size": len(history),
        "history": history,
        "scripts": {"ahmed_v42": {"score": 0.75, "probability": 1.0}},
    }
    live = {
        "phase": "rl" if league else "reinforcement_learning",
        "update": 1658,
        "completed_update": 1658,
        "pfsp": pfsp,
        "population_games": {"self_play": 40, "historical_self_play": 64, "ahmed_v42": 24},
    }
    encoded = json.dumps(live, indent=2)
    assert len(encoded.encode()) > 65536
    filename = "league-progress.json" if league else "learning-progress.json"
    (run / filename).write_text(encoded)
    (run / "resolved-config.json").write_text(json.dumps({"updates": 100000}))
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

    summary = repository.list_runs({"learning/run"})[0]
    detail = repository.detail("learning/run", {"learning/run"}, [])

    for result in (summary, detail["run"]):
        assert isinstance(result, dict)
        learning = result["learning"]
        assert isinstance(learning, dict)
        assert learning["pfsp"] == pfsp
        assert learning["population_games"] == live["population_games"]
        assert learning["update"] == 1658
