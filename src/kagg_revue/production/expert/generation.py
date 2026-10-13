"""One production-shape black-box optimizer generation over complete policies."""

import time
from typing import Any

import torch

from kagg_revue.artifacts.io import digest, write_json
from kagg_revue.evaluation.neural import NeuralMatches
from kagg_revue.policy.checkpoints import save_policy
from kagg_revue.policy.spatial.model import Policy
from kagg_revue.production.evaluation.matches import ScriptMatches
from kagg_revue.production.expert.config import EvolutionSettings
from kagg_revue.production.expert.mutations import ParameterSearch
from kagg_revue.production.expert.screen import score
from kagg_revue.production.expert.telemetry import candidate_summary, panel_summary, progress


def propose_generation(
    config: EvolutionSettings,
    policy: Policy,
    mutation: ParameterSearch,
    scripts: ScriptMatches,
    neural: NeuralMatches,
    rank: int,
    generation: int,
) -> dict[str, Any]:
    """Rank coherent proposals by WDL, giving scripts and self-play equal game counts."""
    started = time.perf_counter()
    p = config.production
    seed = p.ppo.seed_start + (generation - 1) * p.evaluation_games // 2
    progress(p.output_dir, generation, rank, "control", 0, 1)
    control_scripts, control_neural = scripts.run(seed), neural.run(seed)
    baseline = score(control_scripts) + score(control_neural)
    directions = [
        (config.mutation_seed + generation * config.directions + direction, scale * sign)
        for direction in range(config.directions)
        for scale in config.scales
        for sign in (1, -1)
    ]
    records: list[dict[str, Any]] = []
    finalists: list[dict[str, Any]] = []
    timing = {
        name: control_scripts["timing"][name] + control_neural["timing"][name]
        for name in ("encoding_seconds", "inference_seconds", "native_seconds", "collation_seconds")
    }
    proposal_seconds = checkpoint_seconds = 0.0
    local_count = len(range(rank, len(directions), len(p.devices)))
    progress(p.output_dir, generation, rank, "search", 0, local_count)
    for index in range(rank, len(directions), len(p.devices)):
        direction_seed, scale = directions[index]
        phase = time.perf_counter()
        mutation.propose(direction_seed, scale)
        torch.cuda.synchronize()
        proposal_seconds += time.perf_counter() - phase
        script_result, neural_result = scripts.run(seed), neural.run(seed)
        fitness = score(script_result) + score(neural_result)
        record = {
            "candidate": index,
            "mutation_seed": direction_seed,
            "scale": scale,
            "fitness": fitness,
            "scripts": script_result,
            "neural": neural_result,
        }
        for name in timing:
            timing[name] += script_result["timing"][name] + neural_result["timing"][name]
        admissible = (
            score(script_result) >= score(control_scripts)
            and score(neural_result) >= score(control_neural)
            and fitness > baseline
        )
        if admissible and (len(finalists) < config.finalists or fitness > finalists[-1]["fitness"]):
            phase = time.perf_counter()
            path = (
                p.output_dir
                / "candidates"
                / f"generation-{generation:06d}"
                / f"candidate-{index:04d}.pt"
            )
            recipe = {
                key: record[key] for key in ("candidate", "mutation_seed", "scale", "fitness")
            }
            save_policy(
                path,
                policy,
                p,
                generation=generation,
                recipe=recipe,
                training_phase="evolution_candidate",
            )
            finalists.append({**recipe, "checkpoint": {"path": str(path), "sha256": digest(path)}})
            finalists = sorted(
                finalists, key=lambda value: (-value["fitness"], value["candidate"])
            )[: config.finalists]
            checkpoint_seconds += time.perf_counter() - phase
        records.append(record)
        progress(p.output_dir, generation, rank, "search", len(records), local_count)
        print(
            {
                "generation": generation,
                "rank": rank,
                "candidate": index,
                "script_wdl_gain": score(script_result) - score(control_scripts),
                "neural_wdl_gain": score(neural_result) - score(control_neural),
                "eligible": admissible,
            },
            flush=True,
        )
    path = p.output_dir / "generations" / f"generation-{generation:06d}-rank-{rank}.json"
    write_json(
        path,
        {
            "generation": generation,
            "seed_start": seed,
            "controls": {"scripts": control_scripts, "neural": control_neural},
            "candidates": records,
        },
    )
    return {
        "rank": rank,
        "search": {
            "seed_start": seed,
            "controls": {
                "scripts": panel_summary(control_scripts),
                "neural": panel_summary(control_neural),
            },
            "candidates": [
                candidate_summary(record, {"scripts": control_scripts, "neural": control_neural})
                for record in records
            ],
        },
        "finalists": finalists,
        "report": str(path),
        "physical_games": (1 + len(records)) * 2 * p.evaluation_games,
        "timing": {
            **timing,
            "proposal_seconds": proposal_seconds,
            "checkpoint_seconds": checkpoint_seconds,
            "elapsed_seconds": time.perf_counter() - started,
        },
        "peak_allocated_bytes": torch.cuda.max_memory_allocated(),
        "peak_reserved_bytes": torch.cuda.max_memory_reserved(),
    }
