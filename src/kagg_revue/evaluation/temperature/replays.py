"""Audit observed opening branches against the submitted CPU actor and greedy export."""

import hashlib
import json
from collections import Counter
from copy import deepcopy
from pathlib import Path
from typing import Any

import hydra
import numpy as np
import torch
from omegaconf import DictConfig, OmegaConf

from kagg_revue.artifacts.io import digest, write_json
from kagg_revue.evaluation.temperature.cli import Comparison
from kagg_revue.native import _revue_core as native
from kagg_revue.policy.checkpoints import load_policy


def observation(replay: dict[str, Any], turn: int, seat: int) -> dict[str, Any]:
    """Restore the framework's shared step field in a seat's public replay observation."""
    return {**replay["steps"][turn][seat]["observation"], "step": turn}


def snapshot(obs: dict[str, Any], seat: int) -> dict[str, Any]:
    """Summarize owned production assets and cash without inferring hidden inventory."""
    farm = obs["farms"][seat]
    assets = Counter(
        tile.get("crop", tile.get("animal") or tile["kind"])
        for row in farm["tiles"]
        for tile in row
        if isinstance(tile, dict)
    )
    return {
        "turn": obs["step"],
        "cash": farm["money"],
        "hands": len(farm["hands"]),
        "assets": dict(assets),
        "shed": obs["private"]["shed"],
        "seeds": obs["private"]["seeds"],
        "wheat_price": obs["market"]["prices"]["WHEAT"],
        "wheat_market_inventory": obs["market"]["inventory"]["WHEAT"],
    }


def trace_opening(directory: Path, output_dir: Path) -> None:
    """Verify two-turn cash settlement and isolate the opposing opening's effect."""
    target = json.loads((directory / "107807755-replay.json").read_text())
    control = json.loads((directory / "107808764-replay.json").read_text())
    cases = []
    cases_to_run = (
        ("observed", target),
        ("control_opponent_actions", control),
        ("remove_opponent_wheat_roundtrip", target),
    )
    for name, opponent in cases_to_run:
        engine = native.Engine(target["info"]["seed"], target["configuration"])
        traces = []
        for turn in range(2):
            actions = [
                deepcopy(opponent["steps"][turn + 1][0]["action"]),
                target["steps"][turn + 1][1]["action"],
            ]
            if name == "remove_opponent_wheat_roundtrip" and turn == 0:
                actions[0]["market"] = actions[0]["market"][2:]
            traces.append(engine.step_with_trace(*actions))
            if name == "observed":
                actual = engine.observation(1)
                expected = observation(target, turn + 1, 1)
                for key in ("farms", "private", "market", "town", "day", "hour"):
                    if actual[key] != expected[key]:
                        raise ValueError(f"opening native replay differs at {turn + 1}:{key}")
        cases.append(
            {
                "case": name,
                "market_traces": traces,
                "final_snapshot": snapshot(engine.observation(1), 1),
            }
        )
    write_json(
        output_dir / "opening-settlement.json",
        {
            "cases": cases,
            "scope": "Same initial state and own first two actions. Controls alter only the "
            "opponent's opening: replace its first two actions, or remove its first-turn wheat "
            "buy/sell roundtrip. These are not complete counterfactual matches.",
        },
    )


def audit(config: Comparison, directory: Path, episodes: list[int], turns: int) -> None:
    """Reproduce recorded actions under persistent RNG and verify both exported actors."""
    torch.set_num_threads(1)
    profile = json.loads((config.package / "agent_profile.json").read_text())
    policy, payload = load_policy(config.checkpoint, torch.device("cpu"))
    del payload
    policy.eval()
    sampled = torch.jit.load(  # type: ignore[no-untyped-call]
        str(config.package / "actor.pt"), map_location="cpu"
    ).eval()
    greedy = torch.jit.load(  # type: ignore[no-untyped-call]
        str(config.output_dir / "greedy.pt"), map_location="cpu"
    ).eval()
    replays = {}
    results = []
    for episode in episodes:
        path = directory / f"{episode}-replay.json"
        replay = json.loads(path.read_text())
        seat = replay["info"]["TeamNames"].index("Unknown Mother-Goose")
        replays[episode] = (replay, seat)
        session = native.ContractSession(replay["configuration"], profile["unit_limit"])
        features = np.empty((1, profile["observation_features"]), dtype=np.float16)
        inputs = torch.from_numpy(features)
        step = torch.zeros(1, dtype=torch.long)
        torch.manual_seed(profile["sampling_seed"] + seat)
        mismatches = []
        records = []
        with torch.inference_mode():
            for turn in range(min(turns, len(replay["steps"]) - 1)):
                obs = observation(replay, turn, seat)
                session.update(obs)
                session.observe_into(features)
                step.fill_(turn)
                rng = torch.get_rng_state()
                program = sampled(inputs, step)
                next_rng = torch.get_rng_state()
                # Check independently reconstructed eager model on real, varied histories.
                torch.set_rng_state(rng)
                expected = policy.act(inputs, step, sample=True)[0]
                if not torch.equal(program, expected):
                    raise ValueError(
                        f"submitted actor differs from eager model at {episode}:{turn}"
                    )
                greedy_program = greedy(inputs, step)
                expected_greedy = policy.act(inputs, step, sample=False)[0]
                if not torch.equal(greedy_program, expected_greedy):
                    raise ValueError(f"greedy export differs from eager argmax at {episode}:{turn}")
                torch.set_rng_state(next_rng)
                session.set_program(program.numpy(), 1, profile["quantities"])
                actual = session.program_action()
                logged = replay["steps"][turn + 1][seat]["action"]
                session.set_program(greedy_program.numpy(), 1, profile["quantities"])
                greedy_action = session.program_action()
                # Leave history in the sampled policy state for the next observation.
                session.set_program(program.numpy(), 1, profile["quantities"])
                if actual != logged:
                    mismatches.append({"turn": turn, "local": actual, "logged": logged})
                records.append(
                    {
                        "turn": turn,
                        "feature_sha256": hashlib.sha256(features.tobytes()).hexdigest(),
                        "logged": logged,
                        "local_t1": actual,
                        "t0_on_logged_observation": greedy_action,
                    }
                )
        result = {
            "episode": episode,
            "replay_sha256": digest(path),
            "seat": seat,
            "opponent": replay["info"]["TeamNames"][1 - seat],
            "statuses": replay["statuses"],
            "rewards": replay["rewards"],
            "seed": replay["info"]["seed"],
            "checked_turns": len(records),
            "mismatched_turns": len(mismatches),
            "first_mismatches": mismatches[:3],
            "eager_sampled_and_greedy_export_checks_passed": True,
            "snapshots": [
                snapshot(observation(replay, t, seat), seat)
                for t in (0, 1, 2, 23, 47, 71, 119, 239, 479, 719)
            ],
            "actions": records,
        }
        write_json(config.output_dir / f"replay-{episode}.json", result)
        results.append({k: v for k, v in result.items() if k != "actions"})
        print(
            json.dumps({k: result[k] for k in ("episode", "checked_turns", "mismatched_turns")}),
            flush=True,
        )
    comparisons = []
    first_id = episodes[0]
    left, left_seat = replays[first_id]
    for episode in episodes[1:]:
        right, right_seat = replays[episode]
        differences = [
            t
            for t in range(min(len(left["steps"]), len(right["steps"])) - 1)
            if left["steps"][t + 1][left_seat]["action"]
            != right["steps"][t + 1][right_seat]["action"]
        ]
        t = differences[0] if differences else None
        comparisons.append(
            {
                "episodes": [first_id, episode],
                "first_different_action_turn": t,
                "actions": [
                    left["steps"][t + 1][left_seat]["action"],
                    right["steps"][t + 1][right_seat]["action"],
                ]
                if t is not None
                else [],
                "preceding_snapshots": [
                    snapshot(observation(left, t, left_seat), left_seat),
                    snapshot(observation(right, t, right_seat), right_seat),
                ]
                if t is not None
                else [],
            }
        )
    write_json(
        config.output_dir / "replay-audit.json",
        {
            "episodes": results,
            "opening_comparisons": comparisons,
            "scope": "T0 actions on logged T1 states are diagnostic only; "
            "they are not counterfactual games.",
        },
    )


@hydra.main(
    version_base=None,
    config_path=str(Path(__file__).resolve().parents[4] / "configs"),
    config_name="evaluation_temperature",
)
def main(configuration: DictConfig) -> None:
    """Audit downloaded episodes with the same authenticated evaluation artifacts."""
    config = Comparison.model_validate(
        OmegaConf.to_container(configuration.comparison, resolve=True)
    )
    audit(
        config,
        Path(configuration.replays.directory),
        list(configuration.replays.episodes),
        int(configuration.replays.turns),
    )


if __name__ == "__main__":
    main()
