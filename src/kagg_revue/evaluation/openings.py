"""Inspect frozen policies' opening concentration with advancing sampling streams."""

import gc
import json
import math
import time
from collections import Counter
from pathlib import Path
from typing import Any

import hydra
import torch
from omegaconf import DictConfig, OmegaConf

from kagg_revue.artifacts.io import digest, write_json
from kagg_revue.datasets.behavior.extraction import normalized_action
from kagg_revue.datasets.coverage.extraction import snapshot
from kagg_revue.native import _revue_core as native
from kagg_revue.policy.checkpoints import load_policy
from kagg_revue.policy.inference import ActorRuntime


def distribution(values: list[Any]) -> dict[str, Any]:
    """Count decoded requests or outcomes, omitting irrelevant program padding."""
    counts = Counter(json.dumps(v, sort_keys=True) for v in values)
    total = len(values)
    entropy = -sum(n / total * math.log(n / total) for n in counts.values())
    return {
        "samples": total,
        "unique": len(counts),
        "mode_fraction": max(counts.values()) / total,
        "effective_alternatives": math.exp(entropy),
        "top": [{"value": json.loads(v), "count": n} for v, n in counts.most_common(5)],
    }


def _decode(session: Any, program: Any, quantities: list[int]) -> dict[str, Any]:
    session.set_program(program, 1, quantities)
    return normalized_action(session.program_action())


def _initial(runtime: ActorRuntime, settings: dict[str, Any], config: DictConfig) -> Any:
    policy = runtime.policy
    engine = native.Engine(int(config.environment_seed), settings["environment"])
    session = native.ContractSession(settings["environment"], settings["unit_limit"])
    session.update(engine.observation(0))
    session.observe_into(runtime.host.numpy()[:1])
    runtime.host.copy_(runtime.host[:1].expand_as(runtime.host).clone())
    quantities = list(policy.layout.observation.quantities)
    actions: list[dict[str, Any]] = []
    torch.manual_seed(int(config.sampling_seed))
    for _ in range(int(config.draws) // len(runtime.host)):
        runtime.act(0)
        programs = runtime.selected.numpy()
        actions.extend(
            _decode(session, programs[i : i + 1], quantities) for i in range(len(programs))
        )
    return {
        "full": distribution(actions),
        "market": distribution([a["market"] for a in actions]),
        "units": distribution([[a["farmer"], *a["hands"]] for a in actions]),
    }


def _rollouts(
    runtime: ActorRuntime, settings: dict[str, Any], config: DictConfig, output: Path
) -> dict[str, Any]:
    quantities = list(runtime.policy.layout.observation.quantities)
    per_batch = len(runtime.host) // 2
    per_stream = int(config.games) // int(config.streams)
    horizons = [int(h) for h in config.horizons]
    rows = []
    initial_features: set[bytes] = set()
    with output.open("w") as stream:
        for stream_index in range(int(config.streams)):
            sampling_seed = int(config.sampling_seed) + 1000 + stream_index
            torch.manual_seed(sampling_seed)
            for offset in range(0, per_stream, per_batch):
                start = int(config.environment_seed) + stream_index * per_stream + offset
                seeds = list(range(start, start + per_batch))
                batch = native.SelfPlayBatch(
                    settings["environment"],
                    seeds,
                    [0] * per_batch,
                    settings["unit_limit"],
                    2,
                    quantities,
                )
                sessions = [
                    native.ContractSession(settings["environment"], settings["unit_limit"])
                    for _ in range(2 * per_batch)
                ]
                records: list[dict[str, Any]] = [
                    {
                        "seed": seeds[i // 2],
                        "seat": i % 2,
                        "sampling_seed": sampling_seed,
                        "actions": [],
                        "snapshots": {},
                    }
                    for i in range(2 * per_batch)
                ]
                for turn in range(max(horizons)):
                    batch.observe_selfplay_into(runtime.host.numpy())
                    if turn == 0:
                        initial_features.update(row.tobytes() for row in runtime.host.numpy())
                    runtime.act(turn)
                    programs = runtime.selected.numpy()
                    for i, session in enumerate(sessions):
                        session.update(batch.observation(i // 2, i % 2))
                        records[i]["actions"].append(
                            _decode(session, programs[i : i + 1], quantities)
                        )
                    batch.advance_programs(programs, 1, 1, True)
                    if turn + 1 in horizons:
                        for i, record in enumerate(records):
                            record["snapshots"][str(turn + 1)] = snapshot(
                                batch.observation(i // 2, i % 2), i % 2
                            )
                assert batch.step_index == max(horizons)
                for record in records:
                    stream.write(json.dumps(record) + "\n")
                stream.flush()
                rows.extend(records)
    result: dict[str, Any] = {
        "physical_games": len(rows) // 2,
        "initial_unique_features": len(initial_features),
        "seats": {},
    }
    for seat in (0, 1):
        selected = [r for r in rows if r["seat"] == seat]
        result["seats"][str(seat)] = {
            "prefixes": {
                str(h): {
                    "full": distribution([r["actions"][:h] for r in selected]),
                    "market": distribution(
                        [[a["market"] for a in r["actions"][:h]] for r in selected]
                    ),
                }
                for h in horizons
            },
            "assets": {
                str(h): distribution(
                    [
                        {
                            "assets": r["snapshots"][str(h)]["assets"],
                            "hands": r["snapshots"][str(h)]["hands"],
                        }
                        for r in selected
                    ]
                )
                for h in horizons
            },
        }
    return result


@hydra.main(version_base=None, config_path="../../../configs", config_name="evaluation_openings")
def main(config: DictConfig) -> None:
    """Compare declared checkpoints without modifying a live trainer or selecting weights."""
    torch.set_num_threads(2)
    count = int(config.batch_rows)
    if count % 2 or int(config.draws) % count:
        raise ValueError("draw count must divide into complete even inference batches")
    if int(config.games) % (int(config.streams) * count // 2):
        raise ValueError("games must divide into complete stream batches")
    output = Path(config.output)
    output.mkdir(parents=True, exist_ok=True)
    results = []
    for name, entry in config.checkpoints.items():
        started = time.perf_counter()
        path = Path(entry.path)
        policy, payload = load_policy(path, torch.device("cpu"))
        settings = payload["settings"]
        del payload
        if policy.layout.interval != 1 or policy.layout.capacity != 1:
            raise ValueError("opening inspection requires one-turn programs")
        policy.to(str(config.device))
        runtime = ActorRuntime(policy, count, sample=True, temperature=1.0, precision="bf16")
        result = {
            "stage": str(name),
            "checkpoint": str(path),
            "sha256": digest(path),
            "initial": _initial(runtime, settings, config),
        }
        if entry.rollout:
            result["rollout"] = _rollouts(runtime, settings, config, output / f"{name}-games.jsonl")
        result["wall_seconds"] = time.perf_counter() - started
        results.append(result)
        write_json(
            output / "report.json",
            {
                "configuration": OmegaConf.to_container(config, resolve=True),
                "results": results,
                "scope": "Frozen-policy CUDA BF16 T=1 diagnostic, uncompiled CUDA graphs. "
                "Sampling advances within each declared stream; no per-game seed reset. "
                "Not the live training tape, a win-rate test or an ablation. Two seats of a game "
                "are correlated and reported separately. Asset signatures retain owned tile types "
                "and hand counts, excluding locations and cash. Requested-action differences "
                "need not imply different successful actions or competitive strength.",
            },
        )
        print(
            json.dumps(
                {
                    "stage": name,
                    "seconds": result["wall_seconds"],
                    "initial": {k: v for k, v in result["initial"]["full"].items() if k != "top"},
                }
            ),
            flush=True,
        )
        del runtime, policy
        gc.collect()
        torch.cuda.empty_cache()


if __name__ == "__main__":
    main()
