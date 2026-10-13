import zipfile
from pathlib import Path

import numpy as np
import orjson
import pytest

from kagg_revue.datasets.behavior.extraction import (
    action_fingerprints,
    extract_episode,
    normalized_action,
)
from kagg_revue.datasets.behavior.metrics import _history_conflicts, _pair_profile


def test_request_fingerprints_preserve_quantity_and_market_order() -> None:
    action = {"farmer": ["PICKUP", "WHEAT", 2], "hands": [["PASS"]], "market": []}
    padded = {**action, "hands": [["PASS"], ["PASS"]]}
    assert action_fingerprints(action)[0] != action_fingerprints(padded)[0]
    assert action_fingerprints(action)[1] == action_fingerprints(padded)[1]
    different = {**action, "farmer": ["PICKUP", "WHEAT", 3]}
    assert action_fingerprints(action)[1] != action_fingerprints(different)[1]
    assert action_fingerprints(action)[2] == action_fingerprints(different)[2]
    assert normalized_action(None) == {"farmer": ["PASS"], "hands": [], "market": []}


def test_pair_agreement_excludes_self_pairs_and_separate_groups() -> None:
    hashes = np.array([[[11]], [[11]], [[12]], [[13]], [[13]]], dtype=np.uint64)
    profile, pairs = _pair_profile(hashes, [[0, 1, 2], [3, 4]], 0)
    assert pairs == 4
    assert profile == [pytest.approx(0.5)]
    rows = [
        {
            "date": "2026-09-08",
            "seat": seat,
            "configuration_hash": 1,
            "episode_id": str(index),
            "create_time": "2026-09-08T00:00:00",
            "early": [{"step": 0, "history": "same", "action": action, "units": action}],
        }
        for index, (seat, action) in enumerate([(0, 11), (0, 12), (1, 13)])
    ]
    result = _history_conflicts(rows)
    assert result["replicated_history_groups"] == 1
    assert result["conflicting_history_groups"] == 1


def test_initialization_frame_is_not_an_agent_decision(tmp_path: Path) -> None:
    first = {"farmer": ["BUILD_PASTURE"], "hands": [], "market": [[]]}
    noop = {"farmer": ["PASS"], "hands": [], "market": []}
    farm = {"money": 3000, "tiles": [[None]], "hands": [], "unlocked_quadrants": ["NW"]}
    observation = {
        "farms": [farm, farm],
        "private": {"shed": {}},
        "market": {"prices": {}},
        "town": {"unlocked_shops": []},
    }
    replay = {
        "configuration": {"episodeSteps": 720},
        "name": "kaggriculture",
        "module_version": "1.32.7",
        "statuses": ["DONE", "DONE"],
        "rewards": [3000, 3000],
        "info": {"seed": 1, "TeamNames": ["a", "b"]},
        "steps": [
            [
                {
                    "observation": {**observation, "player": seat},
                    "action": first if step == 1 else noop,
                }
                for seat in (0, 1)
            ]
            for step in range(720)
        ],
    }
    archive = tmp_path / "replays.zip"
    with zipfile.ZipFile(archive, "w") as zipped:
        zipped.writestr("1.json", orjson.dumps(replay))
    result = extract_episode(
        (str(archive), "1", "2026-09-08", {"create_time": "now", "average_score": 0})
    )
    assert len(result) == 2
    assert len(result[0]["hashes"]) == 719
    assert result[0]["hashes"][0] == action_fingerprints(first)
    assert result[0]["hashes"][1] == action_fingerprints(noop)
    assert result[0]["market_operations"]["EMPTY_REQUEST"] == 1
