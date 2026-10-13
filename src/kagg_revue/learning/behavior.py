"""Full-season action and cash accounting for authenticated random-root policies."""

import json
from collections import Counter
from pathlib import Path
from typing import Any, Literal, cast

import hydra
import numpy as np
import torch
from omegaconf import DictConfig, OmegaConf
from pydantic import Field, model_validator

from kagg_revue.artifacts.io import write_json
from kagg_revue.configuration import FrozenSettings
from kagg_revue.datasets.restarts import RestartBank
from kagg_revue.learning.config import Experiment
from kagg_revue.learning.curriculum import create_bank
from kagg_revue.learning.state import budget_member, load_member, source_identity
from kagg_revue.native import _revue_core as native
from kagg_revue.native.comparison import MirrorReference
from kagg_revue.policy.inference import ActorRuntime


class Audit(FrozenSettings):
    """Same-seed accounting for initial and trained members of explicit new runs."""

    runs: tuple[Path, ...]
    output_dir: Path
    games: int = Field(default=8, gt=0)
    seed: int = Field(default=730000000, ge=0)
    device: str = "cuda:0"
    start_step: int = Field(default=0, ge=0)
    split: Literal["selection", "confirmation"] = "selection"
    updates: tuple[int, ...] | None = None
    members: tuple[str, ...] | None = None
    reference_directory: Path | None = None

    @model_validator(mode="after")
    def validate_members(self) -> "Audit":
        """Allow explicit initialization checkpoints without ambiguous budget aliases."""
        if self.members is not None and (
            self.updates is not None
            or not self.members
            or len(set(self.members)) != len(self.members)
        ):
            raise ValueError("choose unique registered members or online updates, not both")
        if self.reference_directory is not None and (
            self.reference_directory.is_absolute()
            or ".." in self.reference_directory.parts
            or self.reference_directory.parts[:2] != ("data", "external")
        ):
            raise ValueError("official reference artifacts belong under data/external")
        return self


def measure(
    config: Experiment,
    state: dict[str, Any],
    member: str,
    audit: Audit,
    bank: RestartBank | None = None,
) -> dict[str, Any]:
    """Account actual native actions and revenue, without using a script opponent."""
    device = torch.device(audit.device)
    torch.manual_seed(audit.seed)
    policy, payload = load_member(config, state, member, device)
    lineage = payload["lineage"]
    del payload
    policy.eval()
    layout = policy.layout
    runtime = ActorRuntime(policy, audit.games * 2, sample=True, precision=config.precision)
    restart: dict[str, Any] = {"start_step": 0, "split": "fresh"}
    prefixes = None
    seeds = list(range(audit.seed, audit.seed + audit.games))
    if audit.start_step:
        if bank is None:
            raise ValueError("a suffix behavior audit needs a verified replay bank")
        _, restart = bank.sample(audit.start_step, audit.games, audit.seed)
        seeds = restart["environment_seeds"]
        prefixes = [bank.loaded[name][0] for name in restart["members"]]
    engines = [native.Engine(seed, config.environment) for seed in seeds]
    reference = (
        MirrorReference(audit.reference_directory, config.environment, seeds)
        if audit.reference_directory is not None
        else None
    )
    sessions = [
        native.ContractSession(config.environment, config.unit_limit)
        for _ in range(2 * audit.games)
    ]
    operations: Counter[str] = Counter()
    market: Counter[str] = Counter()
    market_quantities: Counter[str] = Counter()
    revenue = expenditure = unit_cost = absent_fields = job_fields = 0.0
    boundaries = {turn: i for i, turn in enumerate(layout.starts)}
    plant_turns = yield_turns = unit_turns = 0
    starting = float(config.environment.get("startingMoney", 3000)) * 2 * audit.games
    for turn in range(layout.observation.turns):
        observations = (
            reference.observations(engines)
            if reference is not None
            else [engine.observation(seat) for engine in engines for seat in (0, 1)]
        )
        if turn == audit.start_step:
            starting = sum(engine.money(seat) for engine in engines for seat in (0, 1))
        for row, (observation, session) in enumerate(zip(observations, sessions, strict=True)):
            session.update(observation)
            if turn < audit.start_step:
                continue
            own = observation["farms"][row % 2]
            unit_turns += 1 + len(own["hands"])
            for tiles in own["tiles"]:
                for tile in tiles:
                    if isinstance(tile, dict):
                        plant_turns += tile.get("kind") == "PLANT"
                        yield_turns += tile.get("yield_units", 0) > 0
            if turn in boundaries:
                session.observe_into(runtime.host[row : row + 1].numpy())
        if turn < audit.start_step:
            assert prefixes is not None
            for engine, prefix in zip(engines, prefixes, strict=True):
                engine.step(*prefix[turn])
            if reference is not None:
                for game, prefix in zip(reference.games, prefixes, strict=True):
                    game.step(prefix[turn])
            continue
        if turn in boundaries:
            selected, _ = runtime.act(boundaries[turn])
            with torch.no_grad():
                weights = policy.field_weights(selected, runtime.steps, runtime.observations)
                job_weights = (
                    weights[:, : layout.work_factors]
                    .reshape(
                        -1,
                        config.unit_limit,
                        layout.capacity + 1,
                        4,
                    )
                    .sum((2, 3))
                    .cpu()
                    .numpy()
                )
            for row, session in enumerate(sessions):
                present = 1 + len(observations[row]["farms"][row % 2]["hands"])
                absent_fields += float(job_weights[row, present:].sum())
                job_fields += float(job_weights[row].sum())
                session.set_program(
                    runtime.selected[row : row + 1].numpy(),
                    layout.capacity,
                    list(layout.observation.quantities),
                )
        actions = [cast(dict[str, Any], session.program_action()) for session in sessions]
        for action in actions:
            for unit in [action["farmer"], *action["hands"]]:
                operations[str(unit[0])] += 1
        for i, engine in enumerate(engines):
            before = sum(float(farm["money"]) for farm in observations[2 * i]["farms"])
            trace = engine.step_with_trace(actions[2 * i], actions[2 * i + 1])
            cash_delta = 0.0
            for entry in trace["market_trace"]:
                actual = entry["actual"]
                market[str(actual[0]) if actual else "NO_OP"] += 1
                if actual and len(actual) > 2 and isinstance(actual[2], int):
                    market_quantities[f"{actual[0]}:{actual[1]}"] += actual[2]
                change = float(entry["money_after"] - entry["money_before"])
                cash_delta += change
                revenue += max(0, change)
                expenditure += max(0, -change)
            unit_cost += before + cash_delta - engine.money(0) - engine.money(1)
            if reference is not None:
                reference.games[i].step(actions[2 * i : 2 * i + 2])
    if reference is not None:
        reference.observations(engines)
    cash = [engine.money(seat) for engine in engines for seat in (0, 1)]
    if not np.isclose(sum(cash), starting + revenue - expenditure - unit_cost):
        raise RuntimeError("full-season cash accounting does not reconcile")
    result = {
        "run": str(config.output_dir),
        "member": member,
        "checkpoint_sha256": state["members"][member],
        "lineage": lineage,
        "official_reference": reference.report() if reference is not None else None,
        "games": audit.games,
        "sample_seed": audit.seed,
        "physical_transitions": audit.games * (layout.observation.turns - audit.start_step),
        "restart": restart,
        "mean_cash_change": float(np.mean(cash)) - starting / len(cash),
        "unit_actions": operations,
        "market_actions": market,
        "market_quantities": market_quantities,
        "sales_revenue": revenue,
        "market_expenditure": expenditure,
        "unit_construction_cost": unit_cost,
        "mean_terminal_cash": float(np.mean(cash)),
        "plant_tile_turns": plant_turns,
        "positive_yield_tile_turns": yield_turns,
        "unit_turns": unit_turns,
        "job_fields": job_fields,
        "absent_unit_job_fields": absent_fields,
        "absent_unit_job_field_fraction": absent_fields / max(1, job_fields),
        "scope": (
            "Sampled mirror games; absent work-v1 fields may affect market conditioning; "
            "grounded-v1 masks absent units"
        ),
    }
    print(json.dumps(result), flush=True)
    return result


@hydra.main(
    version_base=None,
    config_path=str(Path(__file__).resolve().parents[3] / "configs"),
    config_name="learning_behavior",
)
def main(configuration: DictConfig) -> None:
    """Measure complete closed-loop behavior under a separately declared audit seed."""
    audit = Audit.model_validate(OmegaConf.to_container(configuration.audit, resolve=True))
    if (
        audit.output_dir.is_absolute()
        or ".." in audit.output_dir.parts
        or audit.output_dir.parts[:1] != ("outputs",)
    ):
        raise ValueError("behavior reports belong under outputs")
    torch.set_num_threads(4)
    torch.cuda.set_device(torch.device(audit.device))
    results = []
    for run in audit.runs:
        state = json.loads((run / "state.json").read_text())
        config = Experiment.model_validate(state["protocol"])
        bank = None
        if audit.start_step:
            actor, _ = load_member(config, state, "initial.pt", torch.device("cpu"))
            bank = create_bank(config, actor, audit.split)
            del actor
        members = audit.members or (
            tuple(dict.fromkeys(("initial.pt", budget_member(state, 0), state["latest"])))
            if audit.updates is None
            else tuple(budget_member(state, update) for update in audit.updates)
        )
        for member in members:
            results.append(measure(config, state, member, audit, bank))
    write_json(
        audit.output_dir / "behavior.json",
        {
            "configuration": audit.model_dump(mode="json"),
            "source": source_identity(),
            "results": results,
        },
    )


if __name__ == "__main__":
    main()
