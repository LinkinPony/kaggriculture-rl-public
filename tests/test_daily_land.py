from copy import deepcopy
from typing import Any

from kagg_revue.datasets.land.extraction import analyze
from kagg_revue.datasets.land.metadata import episode_records, scores
from kagg_revue.datasets.land.reporting import summarize


def _replay() -> tuple[dict[str, Any], dict[str, Any]]:
    farm = {"unlocked_quadrants": ["NW"], "tiles": [[None] * 4 for _ in range(4)]}
    replay = {
        "name": "kaggriculture",
        "info": {"EpisodeId": 123, "TeamNames": ["a", "b"], "seed": 1},
        "configuration": {"boardSize": 4, "episodeSteps": 4},
        "statuses": ["DONE", "DONE"],
        "module_version": "test",
        "steps": [
            [
                {
                    "observation": {"farms": [deepcopy(farm), deepcopy(farm)]},
                    "status": "ACTIVE" if step < 3 else "DONE",
                }
                for _ in (0, 1)
            ]
            for step in range(4)
        ],
    }
    task = {
        "episode_id": "123",
        "date": "2026-09-21",
        "source": "daily",
        "path": "source.zip",
        "member": "123.json",
    }
    return replay, task


def test_midgame_use_survives_cleared_terminal_and_episodes_deduplicate() -> None:
    replay, task = _replay()
    for seat in (0, 1):
        for step in (1, 2, 3):
            farm = replay["steps"][step][seat]["observation"]["farms"][seat]
            farm["unlocked_quadrants"] = ["NW", "NE", "SW", "SE"]
            if step == 2:
                farm["tiles"][2][2] = {"kind": "PLANT", "crop": "WHEAT"}
    rows = analyze(replay, task)
    assert all(row["first_productive_step"] == 2 for row in rows)
    assert all(row["productive_frames"] == 1 for row in rows)
    assert all(row["unlocked_frames"] == 3 for row in rows)
    assert all(row["unlocked_decision_turns"] == 2 for row in rows)
    result = summarize(rows)
    assert result["productive"]["episodes"] == 1
    assert result["productive"]["trajectories"] == 2


def test_empty_structure_weeds_and_other_quadrants_are_not_productive() -> None:
    replay, task = _replay()
    for step in range(4):
        farm = replay["steps"][step][0]["observation"]["farms"][0]
        farm["unlocked_quadrants"] = ["NW", "NE", "SW", "SE"]
        farm["tiles"][2][1] = {"kind": "PLANT", "crop": "WHEAT"}
        farm["tiles"][1][2] = {"kind": "PASTURE", "animal": "COW"}
        farm["tiles"][2][2] = {"kind": "COOP", "animal": None}
        farm["tiles"][3][3] = {"kind": "WEED"}
    row = analyze(replay, task)[0]
    assert row["se_unlocked"] and row["se_developed"]
    assert not row["se_productive"]
    replay["steps"][-1][0]["observation"]["farms"][0]["tiles"][2][2]["animal"] = "GOOSE"
    row = analyze(replay, task)[0]
    assert row["se_productive"]
    assert row["productive_frames"] == 1
    assert row["productive_decision_turns"] == 0


def test_episode_ratings_do_not_use_cash_or_submission_scores() -> None:
    episode = {
        "id": 1,
        "createTime": "2026-09-21T00:00:00Z",
        "agents": [
            {"index": 1, "reward": 120000, "updatedScore": 3100},
            {"index": 0, "reward": 90000, "updatedScore": 2900},
        ],
    }
    assert list(episode_records({"score": 3200, "episodes": [episode]})) == [episode]
    assert scores(episode["agents"], "updatedScore") == [2900, 3100]
    assert scores(episode["agents"], "initialScore") is None
    assert scores([{"reward": 120000}, {"reward": 90000}], "updatedScore") is None
    assert scores([{"updatedScore": 3000}, {"updatedScore": None}], "updatedScore") is None
