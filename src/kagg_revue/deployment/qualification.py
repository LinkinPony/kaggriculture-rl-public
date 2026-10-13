"""Official closed-loop equivalence and local CPU timing for a serialized new actor."""

import json
import tarfile
import time
from collections import Counter
from pathlib import Path
from typing import Any

import hydra
import numpy as np
import torch
from omegaconf import DictConfig, OmegaConf
from pydantic import Field, model_validator

from kagg_revue.artifacts.io import digest, write_json
from kagg_revue.configuration import FrozenSettings
from kagg_revue.deployment.actor import freeze
from kagg_revue.deployment.provenance import load_run
from kagg_revue.deployment.recurrent import empty_inputs
from kagg_revue.learning.state import load_member, source_identity
from kagg_revue.native import _revue_core as native
from kagg_revue.native.comparison import MirrorReference
from kagg_revue.policy.memory.policy import MemoryPolicy, RecurrentExecution


class Qualification(FrozenSettings):
    """One registered checkpoint and a separately declared complete-game CPU panel."""

    run: Path
    member: str
    output_dir: Path
    reference_directory: Path
    games: int = Field(default=2, gt=0)
    seed: int = Field(default=1200000000, ge=0)
    cpu_threads: int = Field(default=1, gt=0)
    temperature: float = Field(default=1.0, ge=0, allow_inf_nan=False)
    cache_atol: float = Field(default=1e-6, ge=0, le=1e-5, allow_inf_nan=False)

    @model_validator(mode="after")
    def validate_paths(self) -> "Qualification":
        """Keep source models, persistent references and deployment outputs distinct."""
        for path, prefix in (
            (self.run, ("outputs", "learning")),
            (self.output_dir, ("outputs", "deployment")),
            (self.reference_directory, ("data", "external")),
        ):
            if path.is_absolute() or ".." in path.parts or path.parts[:2] != prefix:
                raise ValueError("deployment qualification path has the wrong artifact role")
        return self


def qualify(config: Qualification) -> None:
    """Check sampled programs under paired RNG and every official/native observation."""
    experiment, state = load_run(config.run)
    torch.set_num_threads(config.cpu_threads)
    policy, payload = load_member(experiment, state, config.member, torch.device("cpu"))
    lineage = payload["lineage"]
    del payload
    policy.eval()
    layout = policy.layout
    if layout.network.architecture not in {"grounded-v1", "grounded-v2"}:
        raise ValueError("this deployment qualification covers grounded single-turn policies")
    config.output_dir.mkdir(parents=True, exist_ok=False)
    identity = source_identity()
    with tarfile.open(config.output_dir / "source.tar.gz", "w:gz") as archive:
        for name in identity["files"]:
            archive.add(name, arcname=name, recursive=False)
    path = config.output_dir / "actor.pt"
    started = time.perf_counter()
    freeze(policy, path, temperature=config.temperature)
    export_seconds = time.perf_counter() - started
    started = time.perf_counter()
    serialized = torch.jit.load(str(path), map_location="cpu").eval()  # type: ignore[no-untyped-call]
    load_seconds = time.perf_counter() - started
    seeds = list(range(config.seed, config.seed + config.games))
    reference = MirrorReference(config.reference_directory, experiment.environment, seeds)
    engines = [native.Engine(seed, experiment.environment) for seed in seeds]
    sessions = [
        native.ContractSession(experiment.environment, experiment.unit_limit)
        for _ in range(config.games * 2)
    ]
    features = np.empty((1, layout.observation.features), dtype=np.float16)
    inputs = torch.from_numpy(features)
    step_tensor = torch.zeros(1, dtype=torch.long)
    durations = []
    recurrent = isinstance(policy, MemoryPolicy)
    if isinstance(policy, MemoryPolicy):
        eager = [RecurrentExecution(policy, 1, torch.device("cpu")) for _ in sessions]
        caches = [empty_inputs(policy) for _ in sessions]
    else:
        eager, caches = [], []
    operations: Counter[str] = Counter()
    cache_errors: dict[str, Any] = {
        "rtol": 1e-5,
        "atol": config.cache_atol,
        "max_absolute_error": 0.0,
        "max_error_above_relative_allowance": 0.0,
        "comparisons_exceeding_default_atol": 0,
        "first_default_exceedance": None,
    }
    for turn in range(layout.observation.turns):
        observations = reference.observations(engines)
        actions = []
        step_tensor.fill_(turn)
        for seat_row, (session, observation) in enumerate(zip(sessions, observations, strict=True)):
            session.update(observation)
            session.observe_into(features)
            sample_seed = config.seed + turn * len(sessions) + seat_row
            torch.manual_seed(sample_seed)
            with torch.inference_mode():
                expected = (eager[seat_row] if recurrent else policy).act(
                    inputs,
                    step_tensor,
                    sample=config.temperature > 0,
                    temperature=config.temperature if config.temperature > 0 else 1.0,
                )[0]
                torch.manual_seed(sample_seed)
                started = time.perf_counter()
                if recurrent:
                    actual, keys, values, turns = serialized(inputs, step_tensor, *caches[seat_row])
                    caches[seat_row] = (keys, values, turns)
                else:
                    actual = serialized(inputs, step_tensor)
                durations.append(time.perf_counter() - started)
            if not torch.equal(actual, expected):
                raise ValueError(f"serialized sampled actor differs at {turn}:{seat_row}")
            if recurrent:
                memory = eager[seat_row].state
                for cache_name, actual_cache, expected_cache in zip(
                    ("keys", "values", "turns"),
                    caches[seat_row],
                    (torch.stack(memory.keys), torch.stack(memory.values), memory.turns),
                    strict=True,
                ):
                    if actual_cache.is_floating_point():
                        error = (actual_cache - expected_cache).abs()
                        excess = float((error - 1e-5 * expected_cache.abs()).max())
                        cache_errors["max_absolute_error"] = max(
                            cache_errors["max_absolute_error"], float(error.max())
                        )
                        cache_errors["max_error_above_relative_allowance"] = max(
                            cache_errors["max_error_above_relative_allowance"], excess
                        )
                        if excess > 1e-6:
                            cache_errors["comparisons_exceeding_default_atol"] += 1
                            if cache_errors["first_default_exceedance"] is None:
                                cache_errors["first_default_exceedance"] = {
                                    "turn": turn,
                                    "seat_row": seat_row,
                                    "cache": cache_name,
                                    "excess": excess,
                                }
                    torch.testing.assert_close(
                        actual_cache,
                        expected_cache,
                        rtol=1e-5 if actual_cache.is_floating_point() else 0,
                        atol=config.cache_atol if actual_cache.is_floating_point() else 0,
                        msg=f"recurrent cache differs at {turn}:{seat_row}:{cache_name}",
                    )
            session.set_program(
                actual.numpy(), layout.capacity, list(layout.observation.quantities)
            )
            action: dict[str, Any] = dict(session.program_action())
            operations.update(str(unit[0]) for unit in [action["farmer"], *action["hands"]])
            actions.append(action)
        for index, engine in enumerate(engines):
            pair = actions[2 * index : 2 * index + 2]
            engine.step(*pair)
            reference.games[index].step(pair)
        if (turn + 1) % 64 == 0:
            write_json(
                config.output_dir / "progress.json",
                {"completed_turns": turn + 1, "programs_checked": len(durations), **cache_errors},
            )
    reference.observations(engines)
    if source_identity() != identity:
        raise ValueError("source or native binary changed during deployment qualification")
    report: dict[str, Any] = {
        "configuration": config.model_dump(mode="json"),
        "source": identity,
        "source_archive_sha256": digest(config.output_dir / "source.tar.gz"),
        "run_id": state["run_id"],
        "checkpoint_sha256": state["members"][config.member],
        "lineage": lineage,
        "actor_sha256": digest(path),
        "actor_bytes": path.stat().st_size,
        "export_seconds": export_seconds,
        "local_load_seconds": load_seconds,
        "sampled_programs_checked": len(durations),
        "sampled_programs_identical": True,
        "memory_turns": layout.network.memory_turns,
        "recurrent_caches_checked": len(durations) if recurrent else 0,
        "cache_comparison": cache_errors,
        "official_reference": reference.report(),
        "inference_seconds": {
            "mean": float(np.mean(durations)),
            "p95": float(np.quantile(durations, 0.95)),
            "max": max(durations),
            "total": sum(durations),
        },
        "unit_operations": dict(operations),
        "mean_terminal_cash": float(np.mean([e.money(s) for e in engines for s in (0, 1)])),
        "scope": "Local single-thread FP32 serialized sampled actor versus eager CPU under "
        "paired RNG. Official observations drive both seats; full state matches native. "
        "Not BF16 GPU trajectory identity, a portable package, or Kaggle budget qualification.",
    }
    write_json(config.output_dir / "qualification.json", report)
    print(json.dumps({key: value for key, value in report.items() if key != "source"}), flush=True)


@hydra.main(
    version_base=None,
    config_path=str(Path(__file__).resolve().parents[3] / "configs"),
    config_name="deployment_qualification",
)
def main(configuration: DictConfig) -> None:
    """Resolve the registered member before loading or writing a deployment artifact."""
    qualify(Qualification.model_validate(OmegaConf.to_container(configuration.audit, resolve=True)))


if __name__ == "__main__":
    main()
