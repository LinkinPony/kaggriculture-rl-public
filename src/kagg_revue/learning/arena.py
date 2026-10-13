"""Common-opponent learning curves for authenticated, newly initialized runs."""

import json
from pathlib import Path
from typing import Any, Literal

import hydra
import numpy as np
import torch
from omegaconf import DictConfig, OmegaConf
from pydantic import Field, model_validator

from kagg_revue.artifacts.io import write_json
from kagg_revue.configuration import FrozenSettings
from kagg_revue.evaluation.comparison import paired_cash, paired_scores
from kagg_revue.evaluation.neural import NeuralMatches
from kagg_revue.learning.adapter import runtime_settings
from kagg_revue.learning.config import Experiment
from kagg_revue.learning.state import budget_member, load_member, source_identity
from kagg_revue.learning.validation import validated_run
from kagg_revue.native import _revue_core as native


class Member(FrozenSettings):
    """One frozen opponent named by its new-run ledger and registered member."""

    run: Path
    member: str


class Arena(FrozenSettings):
    """Fix opponents, paired seeds, budgets and sampling before reading outcomes."""

    runs: tuple[Path, ...]
    opponents: tuple[Member, ...]
    updates: tuple[int, ...] = (0, 16, 32, 64, 96, 128)
    output_dir: Path
    device: str = "cuda:0"
    games_per_opponent: int = Field(default=64, gt=0, multiple_of=2)
    seed: int = Field(default=940000000, ge=0)
    role: Literal["selection", "confirmation"] = "selection"

    @model_validator(mode="after")
    def validate_panel(self) -> "Arena":
        """Reject duplicate candidates, changed budget order and report path escapes."""
        if not self.runs or len(set(self.runs)) != len(self.runs) or not self.opponents:
            raise ValueError("arena requires unique candidate runs and a fixed opponent panel")
        if (
            not self.updates
            or self.updates[0] != 0
            or tuple(sorted(set(self.updates))) != self.updates
        ):
            raise ValueError("arena curves require an initial control and ordered unique budgets")
        if (
            self.output_dir.is_absolute()
            or ".." in self.output_dir.parts
            or self.output_dir.parts[:1] != ("outputs",)
        ):
            raise ValueError("arena reports belong under outputs")
        return self


def _run(directory: Path, arena: Arena) -> tuple[Experiment, dict[str, Any]]:
    return validated_run(
        directory, seed=arena.seed, games_per_opponent=arena.games_per_opponent, role=arena.role
    )


def run(arena: Arena) -> None:
    """Use identical frozen neural opponents for every candidate and budget."""
    torch.set_num_threads(4)
    device = torch.device(arena.device)
    torch.cuda.set_device(device)
    runs = [_run(directory, arena) for directory in arena.runs]
    if arena.role == "confirmation" and any(
        state["completed_update"] != config.updates for config, state in runs
    ):
        raise ValueError("arena confirmation requires all candidate training budgets to finish")
    if any(max(arena.updates) > state["completed_update"] for _, state in runs):
        raise ValueError("requested arena budget has not completed")
    opponents = []
    for opponent_spec in arena.opponents:
        config, state = _run(opponent_spec.run, arena)
        actor, _ = load_member(config, state, opponent_spec.member, device)
        opponents.append((config, actor, state["members"][opponent_spec.member]))
    if len({sha for _, _, sha in opponents}) != len(opponents):
        raise ValueError("arena cannot count duplicate opponent weights as different controls")
    records = []
    reference: dict[int, dict[str, Any]] = {}
    for index, (config, state) in enumerate(runs):
        environment = native.Engine(0, config.environment).configuration
        if any(
            native.Engine(0, other.environment).configuration != environment
            for other, _, _ in opponents
        ):
            raise ValueError("common arena opponents require identical environment rules")
        settings = runtime_settings(config).model_copy(
            update={"evaluation_games": arena.games_per_opponent}
        )
        initial = None
        for update in arena.updates:
            member = budget_member(state, update)
            actor, _ = load_member(config, state, member, device)
            games = []
            for opponent_index, (_, opponent, sha) in enumerate(opponents):
                torch.manual_seed(arena.seed + opponent_index)
                panel = NeuralMatches(settings, actor, opponent, sample=True).run(arena.seed)
                for game in panel["games"]:
                    game["opponent"] = sha
                games.extend(panel["games"])
            record = {
                "run": str(config.output_dir),
                "run_id": state["run_id"],
                "update": update,
                "checkpoint_sha256": state["members"][member],
                "mean_score": float(np.mean([(game["outcome"] + 1) / 2 for game in games])),
                "mean_cash": float(np.mean([game["cash"] for game in games])),
                "profitable_games": sum(
                    game["cash"] > environment["startingMoney"] for game in games
                ),
                "games": games,
            }
            initial = record if initial is None else initial
            record["paired_initial_score"] = paired_scores(initial, record)
            record["paired_initial_cash"] = paired_cash(initial, record)
            if index == 0:
                reference[update] = record
            record["paired_first_run_score"] = paired_scores(reference[update], record)
            record["paired_first_run_cash"] = paired_cash(reference[update], record)
            records.append(record)
            write_json(arena.output_dir / config.output_dir.name / f"{update:06d}.json", record)
            print(json.dumps({k: v for k, v in record.items() if k != "games"}), flush=True)
            del actor
    write_json(
        arena.output_dir / "curves.json",
        {
            "configuration": arena.model_dump(mode="json"),
            "source": source_identity(),
            "opponent_sha256": [sha for _, _, sha in opponents],
            "results": records,
            "scope": "Common internal neural controls and complete initial-state games; "
            "not external competitive strength or independent training RNG replication.",
        },
    )


@hydra.main(
    version_base=None,
    config_path=str(Path(__file__).resolve().parents[3] / "configs"),
    config_name="learning_arena",
)
def main(configuration: DictConfig) -> None:
    """Resolve one common panel before loading any registered checkpoint."""
    run(Arena.model_validate(OmegaConf.to_container(configuration.arena, resolve=True)))


if __name__ == "__main__":
    main()
