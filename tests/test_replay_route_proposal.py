import hashlib
from pathlib import Path

import orjson

from kagg_revue.bc.actions import ReplayActionEncoder
from kagg_revue.native import _revue_native as native
from kagg_revue.proposals.replay import discover_replay_routes, load_replay_route


def _action(operation: str, *, hire: bool = False) -> dict[str, object]:
    return {
        "farmer": [operation],
        "hands": [],
        "market": [["HIRE"]] if hire else [],
    }


def _replay(episode_id: int, target_seat: int, first_operation: str) -> dict[str, object]:
    actions = (
        _action(first_operation, hire=True),
        _action("EAST"),
        _action("WEST"),
    )
    steps: list[list[dict[str, object]]] = [
        [
            {"action": _action("PASS")},
            {"action": _action("PASS")},
        ]
    ]
    for action in actions:
        states = [
            {"action": _action("PASS")},
            {"action": _action("PASS")},
        ]
        states[target_seat] = {"action": action}
        steps.append(states)
    names = ["opponent", "opponent"]
    names[target_seat] = "target"
    return {
        "name": "kaggriculture",
        "configuration": {"episodeSteps": 4, "maxMarketOrdersPerTurn": 2},
        "info": {
            "EpisodeId": episode_id,
            "Agents": [{"Name": name} for name in names],
        },
        "steps": steps,
        "statuses": ["DONE", "DONE"],
        "rewards": [episode_id * 1000, -episode_id * 1000],
    }


def test_replay_routes_are_reward_blind_and_align_next_step_actions(tmp_path: Path) -> None:
    repository_root = tmp_path / "repository"
    source_root = repository_root / "data" / "external" / "synthetic"
    source_root.mkdir(parents=True)
    records: list[dict[str, object]] = []
    specifications = ((1, 0, "NORTH"), (2, 1, "NORTH"), (3, 0, "SOUTH"))
    for episode_id, target_seat, operation in specifications:
        relative_path = Path("data/external/synthetic") / f"episode-{episode_id}.json"
        payload = orjson.dumps(_replay(episode_id, target_seat, operation))
        (repository_root / relative_path).write_bytes(payload)
        records.append(
            {
                "id": episode_id,
                "source": {
                    "kind": "kaggle_cli",
                    "path": str(relative_path),
                    "sha256": hashlib.sha256(payload).hexdigest(),
                },
            }
        )
    manifest_path = source_root / "manifest.json"
    manifest_path.write_bytes(orjson.dumps({"episodes": {"records": records}}))

    codec = ReplayActionEncoder(native.action_codec_spec())
    references, selection = discover_replay_routes(
        repository_root,
        manifest_path,
        "target",
        prefix_turns=2,
        route_ids=None,
        episode_steps=4,
        maximum_market_orders=2,
        codec=codec,
    )

    assert [reference.route_id for reference in references] == ["1:0", "3:0"]
    assert references[0].cluster_size == 2
    assert selection["source_agent_routes"] == 3
    assert selection["distinct_prefixes"] == 2
    route = load_replay_route(references[0], episode_steps=4, maximum_market_orders=2)
    assert route.actions[0]["farmer"] == ["NORTH"]
    assert route.actions[1]["farmer"] == ["EAST"]
    assert route.hire_requests == 1
