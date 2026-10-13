"""Direct complete-match screening of coherent neural-policy proposals."""

import json
import os
import time
from pathlib import Path
from typing import Any, Literal

import hydra
import torch
import torch.multiprocessing as mp
from omegaconf import DictConfig, OmegaConf
from pydantic import Field, model_validator

from kagg_revue.artifacts.io import digest, write_json
from kagg_revue.evaluation.neural import NeuralMatches
from kagg_revue.policy.checkpoints import load_policy, save_policy
from kagg_revue.production.artifacts import provenance
from kagg_revue.production.config import FrozenSettings, Settings
from kagg_revue.production.evaluation import panel
from kagg_revue.production.evaluation.matches import ScriptMatches
from kagg_revue.production.expert.mutations import ParameterSearch, readout_parameters
from kagg_revue.production.expert.train import _comparison


class ScreenSettings(FrozenSettings):
    """Bound the candidate set before examining any complete-match results."""

    production: Settings
    search_seed: int = Field(ge=0)
    mutation_seed: int = Field(ge=0)
    directions: int = Field(gt=0)
    scales: tuple[float, ...]
    finalists: int = Field(gt=0)
    mutation_scope: Literal["readouts", "actor"] = "readouts"
    selection_games: int | None = Field(default=None, gt=0)
    confirmation_games: int | None = Field(default=None, gt=0)
    neural_opponent: Path | None = None
    reuse_scripts: Path | None = None

    @model_validator(mode="after")
    def validate_search(self) -> "ScreenSettings":
        """Keep search, selection and confirmation seeds disjoint."""
        p = self.production
        if p.checkpoint is None or p.model.time_prior or p.model.architecture != "work-v1":
            raise ValueError("screening requires an explicit no-table work model")
        if not self.scales or any(v <= 0 for v in self.scales):
            raise ValueError("mutation scales must be positive")
        ranges = sorted(
            (seed, seed + games // 2)
            for seed, games in (
                (self.search_seed, p.evaluation_games),
                (p.evaluation_seed, self.selection_games or p.evaluation_games),
                (p.confirmation_seed, self.confirmation_games or p.evaluation_games),
            )
        )
        if any(a[1] > b[0] for a, b in zip(ranges, ranges[1:], strict=False)):
            raise ValueError("search and held-out seed ranges overlap")
        for games in (self.selection_games, self.confirmation_games):
            if games is not None:
                Settings.model_validate({**p.model_dump(), "evaluation_games": games})
        return self


def score(result: dict[str, Any]) -> int:
    """Use only the direct terminal WDL surface."""
    return int(result["wins"] - result["losses"])


def _neural(config: ScreenSettings, policy: Any, device: torch.device) -> NeuralMatches | None:
    if config.neural_opponent is None:
        return None
    opponent, unused = load_policy(config.neural_opponent, torch.device("cpu"))
    del unused
    return NeuralMatches(
        config.production, policy, opponent.to(device).eval().requires_grad_(False)
    )


def _cached(config: ScreenSettings, rank: int) -> tuple[dict[str, Any], dict[int, dict[str, Any]]]:
    assert config.reuse_scripts is not None
    previous = json.loads((config.reuse_scripts / "resolved-config.json").read_text())
    current = config.model_dump(mode="json")
    for value in (previous, current):
        value.pop("neural_opponent", None)
        value.pop("reuse_scripts", None)
        for name in ("output_dir", "evaluation_seed", "confirmation_seed"):
            value["production"].pop(name)
    if previous != current:
        raise ValueError("cached script panels do not match the exact proposal experiment")
    control = json.loads((config.reuse_scripts / f"control-rank-{rank}.json").read_text())
    records = json.loads((config.reuse_scripts / f"rank-{rank}.json").read_text())
    return control, {r["candidate"]: r["panel"] for r in records}


def _rank(rank: int, resolved: dict[str, Any]) -> None:
    config = ScreenSettings.model_validate(resolved)
    p = config.production
    device = torch.device(p.devices[rank])
    torch.cuda.set_device(device)
    torch.set_num_threads(p.cpu_threads)
    assert p.checkpoint is not None
    policy, unused = load_policy(p.checkpoint, torch.device("cpu"))
    del unused
    policy = policy.to(device).eval().requires_grad_(False)
    parameters = (
        dict(policy.named_parameters())
        if config.mutation_scope == "actor"
        else readout_parameters(policy)
    )
    mutation = ParameterSearch(parameters)
    scripts = ScriptMatches(p, policy)
    neural = _neural(config, policy, device)
    control_neural = neural.run(config.search_seed) if neural else None
    cache: dict[int, dict[str, Any]] = {}
    if config.reuse_scripts:
        control, cache = _cached(config, rank)
    else:
        control = scripts.run(config.search_seed)
    control_score = score(control) + (score(control_neural) if control_neural else 0)
    write_json(p.output_dir / f"control-rank-{rank}.json", control)
    write_json(p.output_dir / f"control-neural-rank-{rank}.json", control_neural)
    proposals = [
        (config.mutation_seed + direction, scale * sign)
        for direction in range(config.directions)
        for scale in config.scales
        for sign in (1, -1)
    ]
    records = []
    best: list[int] = []
    for index in range(rank, len(proposals), len(p.devices)):
        seed, scale = proposals[index]
        mutation.propose(seed, scale)
        result = cache[index] if cache else scripts.run(config.search_seed)
        neural_result = neural.run(config.search_seed) if neural else None
        fitness = score(result) + (score(neural_result) if neural_result else 0)
        record: dict[str, Any] = {
            "candidate": index,
            "mutation_seed": seed,
            "scale": scale,
            "panel": result,
            "neural": neural_result,
            "fitness": fitness,
            "paired_to_control": _comparison(result, control),
        }
        if (
            score(result) >= score(control)
            and fitness > control_score
            and (len(best) < config.finalists or fitness > min(best))
        ):
            checkpoint = p.output_dir / "candidates" / f"candidate-{index:04d}.pt"
            save_policy(
                checkpoint,
                policy,
                p,
                training_phase="parameter_search",
                mutation=record,
                search_configuration=resolved,
            )
            record["checkpoint"] = {"path": str(checkpoint), "sha256": digest(checkpoint)}
            best = sorted([*best, fitness], reverse=True)[: config.finalists]
        records.append(record)
        write_json(p.output_dir / "screen" / f"candidate-{index:04d}.json", record)
        print(
            {
                "rank": rank,
                "candidate": index,
                "scale": scale,
                "wins": result["wins"],
                "neural_wins": neural_result["wins"] if neural_result else None,
                "gain": fitness - control_score,
            },
            flush=True,
        )
    write_json(p.output_dir / f"rank-{rank}.json", records)


def launch(config: ScreenSettings) -> None:
    """Screen complete policies, then validate selected candidates on unseen seeds."""
    p = config.production
    source = provenance(p)
    if not source["clean"]:
        raise ValueError("screening requires a clean source revision")
    if config.reuse_scripts:
        prior_source = json.loads((config.reuse_scripts / "source.json").read_text())
        if any(prior_source[key] != source[key] for key in ("native_sha256", "opponents")):
            raise ValueError("cached match engine or opponent artifact identities changed")
    directory = p.output_dir
    directory.mkdir(parents=True, exist_ok=True)
    started = time.perf_counter()
    write_json(directory / "source.json", source)
    write_json(directory / "resolved-config.json", config.model_dump(mode="json"))
    status = directory / "run-status.json"
    write_json(status, {"status": "running", "pid": os.getpid(), "started_at": time.time()})
    try:
        mp.spawn(_rank, args=(config.model_dump(mode="json"),), nprocs=len(p.devices), join=True)  # type: ignore[attr-defined, no-untyped-call]
        records = [
            record
            for rank in range(len(p.devices))
            for record in json.loads((directory / f"rank-{rank}.json").read_text())
        ]
        candidates = sorted(
            (r for r in records if "checkpoint" in r),
            key=lambda r: (-r["fitness"], r["candidate"]),
        )[: config.finalists]
        assert p.checkpoint is not None
        device = torch.device(p.devices[0])
        torch.cuda.set_device(device)
        torch.set_num_threads(p.cpu_threads)
        policy, unused = load_policy(p.checkpoint, torch.device("cpu"))
        del unused
        policy = policy.to(device).eval().requires_grad_(False)
        selection_settings = Settings.model_validate(
            {**p.model_dump(), "evaluation_games": config.selection_games or p.evaluation_games}
        )
        confirmation_settings = Settings.model_validate(
            {**p.model_dump(), "evaluation_games": config.confirmation_games or p.evaluation_games}
        )
        neural = _neural(
            config.model_copy(update={"production": selection_settings}), policy, device
        )
        selection_scripts = ScriptMatches(selection_settings, policy)
        baseline_selection = selection_scripts.run(p.evaluation_seed)
        baseline_neural_selection = neural.run(p.evaluation_seed) if neural else None
        best_score = score(baseline_selection) + (
            score(baseline_neural_selection) if baseline_neural_selection else 0
        )
        selected = None
        selection_records = []
        for candidate in candidates:
            loaded, unused = load_policy(Path(candidate["checkpoint"]["path"]), torch.device("cpu"))
            policy.load_state_dict(loaded.state_dict())
            del loaded, unused
            result = selection_scripts.run(p.evaluation_seed)
            neural_result = neural.run(p.evaluation_seed) if neural else None
            fitness = score(result) + (score(neural_result) if neural_result else 0)
            record = {
                "candidate": candidate["candidate"],
                "checkpoint": candidate["checkpoint"],
                "panel": result,
                "neural": neural_result,
                "paired_to_control": _comparison(result, baseline_selection),
            }
            selection_records.append(record)
            if score(result) >= score(baseline_selection) and fitness > best_score:
                best_score, selected = fitness, candidate
        confirmation = None
        baseline_confirmation = baseline_neural_confirmation = None
        if selected is not None:
            loaded, unused = load_policy(p.checkpoint, torch.device("cpu"))
            policy.load_state_dict(loaded.state_dict())
            del loaded, unused
            baseline_confirmation = panel(confirmation_settings, policy, p.confirmation_seed)
            neural = _neural(
                config.model_copy(update={"production": confirmation_settings}), policy, device
            )
            baseline_neural_confirmation = neural.run(p.confirmation_seed) if neural else None
            loaded, unused = load_policy(Path(selected["checkpoint"]["path"]), torch.device("cpu"))
            policy.load_state_dict(loaded.state_dict())
            del loaded, unused
            result = panel(confirmation_settings, policy, p.confirmation_seed)
            neural_result = neural.run(p.confirmation_seed) if neural else None
            confirmation = {
                "checkpoint": selected["checkpoint"],
                "panel": result,
                "neural": neural_result,
                "paired_to_control": _comparison(result, baseline_confirmation),
                "paired_to_neural": _comparison(neural_result, baseline_neural_confirmation)
                if neural_result and baseline_neural_confirmation
                else None,
            }
        report = {
            "source": source,
            "resolved_configuration": config.model_dump(mode="json"),
            "baseline": {"path": str(p.checkpoint), "sha256": digest(p.checkpoint)},
            "baseline_selection": baseline_selection,
            "baseline_confirmation": baseline_confirmation,
            "baseline_neural_selection": baseline_neural_selection,
            "baseline_neural_confirmation": baseline_neural_confirmation,
            "neural_opponent": {
                "path": str(config.neural_opponent),
                "sha256": digest(config.neural_opponent),
            }
            if config.neural_opponent
            else None,
            "selection": selection_records,
            "confirmation": confirmation,
            "elapsed_seconds": time.perf_counter() - started,
            "deployment_budget_qualified": False,
        }
        write_json(directory / "report.json", report)
        write_json(status, {"status": "completed", "pid": os.getpid(), "ended_at": time.time()})
        print(
            {
                "selection_candidates": len(candidates),
                "selected": selected["candidate"] if selected else None,
                "confirmation": confirmation["paired_to_control"] if confirmation else None,
            },
            flush=True,
        )
    except BaseException:
        write_json(status, {"status": "failed", "pid": os.getpid(), "ended_at": time.time()})
        raise


@hydra.main(version_base=None, config_path="../../../../configs", config_name="production_screen")
def main(configuration: DictConfig) -> None:
    """Resolve the bounded search before generating any candidate outcomes."""
    launch(ScreenSettings.model_validate(OmegaConf.to_container(configuration, resolve=True)))


if __name__ == "__main__":
    main()
