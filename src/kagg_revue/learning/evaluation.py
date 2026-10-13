"""Frozen random-root controls for early learning curves, with paired uncertainty."""

from typing import Any

import torch

from kagg_revue.artifacts.io import write_json
from kagg_revue.evaluation.comparison import paired_scores
from kagg_revue.evaluation.neural import NeuralMatches
from kagg_revue.learning.config import Experiment
from kagg_revue.learning.settings import RuntimeSettings
from kagg_revue.learning.state import budget_member, load_member
from kagg_revue.policy.spatial.model import Policy


def evaluate(
    config: Experiment,
    settings: RuntimeSettings,
    state: dict[str, Any],
    actor: Policy,
    update: int,
    *,
    confirmation: bool = False,
) -> dict[str, Any]:
    """Evaluate both seats while keeping evaluation out of the training RNG stream."""
    device = next(actor.parameters()).device
    seed = config.evaluation.confirmation_seed if confirmation else config.evaluation.selection_seed
    games = []
    anchors = [
        budget_member(state, 0),
        *(f"anchors/seed-{s}.pt" for s in config.evaluation.anchor_seeds),
    ]
    with torch.random.fork_rng(devices=[device]):
        for index, name in enumerate(anchors):
            opponent, _ = load_member(config, state, name, device)
            torch.manual_seed(seed + index)
            result = NeuralMatches(settings, actor, opponent, sample=True).run(seed)
            for game in result["games"]:
                game["opponent"] = state["members"][name]
            games.extend(result["games"])
    result = {
        "update": update,
        "seed_role": "confirmation" if confirmation else "selection",
        "sample": True,
        "temperature": 1.0,
        "games": games,
        "wins": sum(game["outcome"] > 0 for game in games),
        "ties": sum(game["outcome"] == 0 for game in games),
        "losses": sum(game["outcome"] < 0 for game in games),
        "mean_cash": sum(game["cash"] for game in games) / len(games),
        "mean_score": sum((game["outcome"] + 1) / 2 for game in games) / len(games),
        "checkpoint_sha256": state["members"][budget_member(state, update)],
        "scope": "own RL initial control and random policies; "
        "does not establish external competitive strength or scaling",
    }
    write_json(
        config.output_dir / "evaluation" / f"{result['seed_role']}-{update:06d}.json",
        result,
    )
    return result


def confirm(
    config: Experiment,
    settings: RuntimeSettings,
    state: dict[str, Any],
    actor: Policy,
) -> None:
    """Reserve confirmation seeds until the predeclared training budget ends."""
    device = next(actor.parameters()).device
    with torch.random.fork_rng(devices=[device]):
        initial, _ = load_member(config, state, budget_member(state, 0), device)
        control = evaluate(config, settings, state, initial, 0, confirmation=True)
        candidate = evaluate(
            config,
            settings,
            state,
            actor,
            state["completed_update"],
            confirmation=True,
        )
    write_json(
        config.output_dir / "confirmation.json",
        {
            "paired": paired_scores(control, candidate),
            "completed_update": state["completed_update"],
            "competitive_strength_verified": False,
            "scaling_verified": False,
        },
    )
