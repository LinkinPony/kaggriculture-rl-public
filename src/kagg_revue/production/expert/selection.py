"""Select the next complete neural policy on fresh paired validation games."""

from pathlib import Path
from typing import Any

import torch

from kagg_revue.evaluation.neural import NeuralMatches
from kagg_revue.policy.checkpoints import load_policy
from kagg_revue.policy.spatial.model import Policy
from kagg_revue.production.evaluation.matches import ScriptMatches
from kagg_revue.production.expert.config import EvolutionSettings
from kagg_revue.production.expert.screen import score
from kagg_revue.production.expert.telemetry import progress
from kagg_revue.production.expert.train import _comparison


def select_generation(
    config: EvolutionSettings,
    policy: Policy,
    parent: Policy,
    scripts: ScriptMatches,
    reference: NeuralMatches,
    finalists: list[dict[str, Any]],
    generation: int,
) -> dict[str, Any]:
    """Retain the parent unless a candidate improves WDL without sacrificing either population."""
    p = config.production
    seed = p.evaluation_seed + (generation - 1) * p.evaluation_games // 2
    progress(p.output_dir, generation, 0, "selection", 0, 1 + len(finalists))
    policy.load_state_dict(parent.state_dict())
    baseline_scripts, baseline_neural = scripts.run(seed), reference.run(seed)
    progress(p.output_dir, generation, 0, "selection", 1, 1 + len(finalists))
    best_score = score(baseline_scripts) + score(baseline_neural)
    selected = None
    selected_scripts, selected_neural = baseline_scripts, baseline_neural
    records = []
    for candidate in finalists:
        loaded, unused = load_policy(Path(candidate["checkpoint"]["path"]), torch.device("cpu"))
        policy.load_state_dict(loaded.state_dict())
        del loaded, unused
        script_result, neural_result = scripts.run(seed), reference.run(seed)
        fitness = score(script_result) + score(neural_result)
        records.append(
            {
                "candidate": candidate,
                "scripts": script_result,
                "neural": neural_result,
                "paired_scripts": _comparison(script_result, baseline_scripts),
                "paired_neural": _comparison(neural_result, baseline_neural),
            }
        )
        progress(p.output_dir, generation, 0, "selection", 1 + len(records), 1 + len(finalists))
        if (
            score(script_result) >= score(baseline_scripts)
            and score(neural_result) >= score(baseline_neural)
            and fitness > best_score
        ):
            selected, best_score = candidate, fitness
            selected_scripts, selected_neural = script_result, neural_result
    if selected:
        loaded, unused = load_policy(Path(selected["checkpoint"]["path"]), torch.device("cpu"))
        policy.load_state_dict(loaded.state_dict())
        del loaded, unused
    else:
        policy.load_state_dict(parent.state_dict())
    return {
        "generation": generation,
        "seed_start": seed,
        "selected": selected,
        "baseline_scripts": baseline_scripts,
        "baseline_neural": baseline_neural,
        "candidates": records,
        "scripts": selected_scripts,
        "neural": selected_neural,
        "paired_scripts": _comparison(selected_scripts, baseline_scripts),
        "paired_neural": _comparison(selected_neural, baseline_neural),
        "physical_games": (1 + len(finalists)) * 2 * p.evaluation_games,
    }
