"""Fixed-seed mutual matches outside all optimizer tapes and training RNG streams."""

import torch

from kagg_revue.artifacts.io import write_json
from kagg_revue.learning.distributed import gather, rank_world
from kagg_revue.learning.league.collection import collect
from kagg_revue.learning.league.config import League
from kagg_revue.learning.league.telemetry import combine_pairs
from kagg_revue.learning.settings import RuntimeSettings
from kagg_revue.policy.inference import ActorRuntime


def evaluate(
    config: League, settings: RuntimeSettings, runtimes: list[ActorRuntime], update: int
) -> None:
    """Measure every pair on the same held-out seeds, with confirmation only at budget."""
    rank, _ = rank_world()
    confirmation = update == config.experiment.updates
    seed = (
        config.experiment.evaluation.confirmation_seed
        if confirmation
        else config.experiment.evaluation.selection_seed
    )
    if config.script_names or len(config.members) != 3:
        recipe = config.model_copy(
            update={"experiment": config.experiment.model_copy(update={"train_seed": seed})}
        )
        with torch.random.fork_rng(devices=[runtimes[0].device]):
            torch.manual_seed(seed + rank)
            tapes, metrics = collect(recipe, settings, runtimes, 1)
            del tapes
        pairs = combine_pairs(gather(metrics))
        if rank == 0:
            write_json(
                config.experiment.output_dir / "evaluation" / f"update-{update:06d}.json",
                {
                    "update": update,
                    "partition": "confirmation" if confirmation else "selection",
                    "seed": seed,
                    "seed_blocks": {"mixed_league": seed},
                    "physical_games": config.experiment.games,
                    "members": config.members,
                    "script_opponents": config.script_names,
                    "pairs": pairs,
                },
            )
        return
    # Each pass preserves the captured inference batch size. Mutual evaluation
    # retains its original game count and seeds when training adds self-play.
    per_pair = config.games_per_pair + config.selfplay_games_per_member
    pairs = {}
    blocks = {}
    for selfplay in (False, True) if config.selfplay_games_per_member else (False,):
        block_seed = seed + (config.experiment.games if selfplay else 0)
        recipe = config.model_copy(
            update={
                "experiment": config.experiment.model_copy(update={"train_seed": block_seed}),
                "games_per_pair": 0 if selfplay else per_pair,
                "selfplay_games_per_member": per_pair if selfplay else 0,
            }
        )
        with torch.random.fork_rng(devices=[runtimes[0].device]):
            torch.manual_seed(block_seed + rank)
            tapes, metrics = collect(recipe, settings, runtimes, 1)
            del tapes
        pairs.update(combine_pairs(gather(metrics)))
        blocks["self_play" if selfplay else "mutual"] = block_seed
    if rank == 0:
        directory = config.experiment.output_dir / "evaluation"
        directory.mkdir(exist_ok=True)
        write_json(
            directory / f"update-{update:06d}.json",
            {
                "update": update,
                "partition": "confirmation" if confirmation else "selection",
                "seed": seed,
                "seed_blocks": blocks,
                "physical_games": sum(panel["games"] for panel in pairs.values()),
                "pairs": pairs,
            },
        )
