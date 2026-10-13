"""Paired suffix learning curves on source episodes excluded from training."""

import json
from pathlib import Path
from typing import Any, Literal

import hydra
import numpy as np
import torch
from omegaconf import DictConfig, OmegaConf
from pydantic import Field

from kagg_revue.artifacts.io import write_json
from kagg_revue.configuration import FrozenSettings
from kagg_revue.evaluation.comparison import paired_cash, paired_scores
from kagg_revue.evaluation.neural import PairedPolicy
from kagg_revue.learning.config import Experiment
from kagg_revue.learning.curriculum import create_bank
from kagg_revue.learning.state import load_member, source_identity
from kagg_revue.policy.inference import ActorRuntime
from kagg_revue.policy.spatial.model import Policy


class Probe(FrozenSettings):
    """A fixed source panel, with explicit member budgets and terminal cash metrics."""

    runs: tuple[Path, ...]
    output_dir: Path
    updates: tuple[int, ...] = (0, 8, 16, 32, 64)
    start_step: int = Field(default=576, gt=0)
    seeds: int = Field(default=32, gt=0)
    sampling_seed: int = Field(default=840000000, ge=0)
    split: Literal["selection", "confirmation"] = "selection"


def _matches(
    config: Experiment,
    learner: Policy,
    opponent: Policy,
    base: Any,
    panel: dict[str, Any],
    seed: int,
    opponent_id: str,
) -> list[dict[str, Any]]:
    games = 2 * len(panel["members"])
    paired = PairedPolicy(learner, opponent, games)
    torch.manual_seed(seed)
    runtime = ActorRuntime(
        paired,
        2 * games,
        sample=True,
        precision=config.precision,
        bf16_reduced_precision_reduction=False,
    )
    batch = base.fork(np.repeat(np.arange(games // 2, dtype=np.int64), 2))
    for turn in range(panel["start_step"], learner.layout.observation.turns):
        batch.observe_selfplay_into(runtime.host.numpy())
        runtime.act(turn)
        batch.advance_programs(runtime.selected.numpy(), 1, 1, True)
    if batch.completed_games != games:
        raise RuntimeError("source probe did not complete each sampled suffix")
    cash = batch.cash()
    result = []
    for game in range(games):
        seat, source = game % 2, game // 2
        value = float(cash[game, seat])
        other = float(cash[game, 1 - seat])
        result.append(
            {
                "seed": panel["environment_seeds"][source],
                "seat": seat,
                "opponent": opponent_id,
                "source": panel["members"][source],
                "cash": value,
                "opponent_cash": other,
                "net_cash": value - panel["initial_cash"][source][seat],
                "outcome": int(np.sign(value - other)),
            }
        )
    return result


def run(probe: Probe) -> None:
    """Load only authenticated new-run members and preserve every panel outcome."""
    if (
        probe.output_dir.is_absolute()
        or ".." in probe.output_dir.parts
        or probe.output_dir.parts[:1] != ("outputs",)
    ):
        raise ValueError("source probe reports belong under outputs")
    if (
        not probe.updates
        or probe.updates[0] != 0
        or tuple(sorted(set(probe.updates))) != probe.updates
    ):
        raise ValueError("source probes need an initial control and ordered unique budgets")
    torch.set_num_threads(4)
    results = []
    for directory in probe.runs:
        state = json.loads((directory / "state.json").read_text())
        config = Experiment.model_validate(state["protocol"])
        if probe.split == "confirmation" and state["completed_update"] != config.updates:
            raise ValueError("source confirmation is reserved until the complete training budget")
        device = torch.device(config.device)
        torch.cuda.set_device(device)
        initial, _ = load_member(config, state, "initial.pt", device)
        bank = create_bank(config, initial, probe.split)
        if bank is None:
            raise ValueError("source probes require the run's declared curriculum source")
        base, panel = bank.sample(probe.start_step, probe.seeds, probe.sampling_seed, replace=False)
        anchors = ["initial.pt", *(f"anchors/seed-{s}.pt" for s in config.evaluation.anchor_seeds)]
        control = None
        for update in probe.updates:
            member = "initial.pt" if not update else f"checkpoints/update-{update:06d}.pt"
            actor, _ = load_member(config, state, member, device)
            games = []
            for index, anchor in enumerate(anchors):
                opponent, _ = load_member(config, state, anchor, device)
                games.extend(
                    _matches(
                        config,
                        actor,
                        opponent,
                        base,
                        panel,
                        probe.sampling_seed + index,
                        state["members"][anchor],
                    )
                )
                del opponent
            record = {
                "run": str(directory),
                "update": update,
                "source_panel": panel,
                "checkpoint_sha256": state["members"][member],
                "games": games,
                "mean_net_cash": float(np.mean([game["net_cash"] for game in games])),
            }
            control = record if control is None else control
            record["paired_score"] = paired_scores(control, record)
            record["paired_cash"] = paired_cash(control, record)
            results.append(record)
            write_json(probe.output_dir / directory.name / f"update-{update:06d}.json", record)
            print(
                json.dumps(
                    {
                        "run": str(directory),
                        "update": update,
                        "paired_cash": record["paired_cash"],
                        "mean_net_cash": record["mean_net_cash"],
                    }
                ),
                flush=True,
            )
            del actor
    write_json(
        probe.output_dir / "curves.json",
        {
            "configuration": probe.model_dump(mode="json"),
            "results": results,
            "source": source_identity(),
            "scope": "Paired source suffixes against fresh random neural anchors; "
            "does not establish initial-state strength or external competitiveness",
        },
    )


@hydra.main(
    version_base=None,
    config_path=str(Path(__file__).resolve().parents[3] / "configs"),
    config_name="learning_probes",
)
def main(configuration: DictConfig) -> None:
    """Resolve fixed source partitions and checkpoint budgets before evaluation."""
    run(Probe.model_validate(OmegaConf.to_container(configuration.probe, resolve=True)))


if __name__ == "__main__":
    main()
