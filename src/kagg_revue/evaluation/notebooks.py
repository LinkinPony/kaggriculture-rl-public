"""Paired public-notebook games using Kaggle's final-callable entrypoint rule."""

import json
import multiprocessing
import time
from collections.abc import Callable
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
from typing import Any, cast

import hydra
import numpy as np
import torch
from omegaconf import DictConfig, OmegaConf
from pydantic import Field, model_validator

from kagg_revue.artifacts.io import digest, write_json
from kagg_revue.configuration import FrozenSettings
from kagg_revue.native import _revue_core as native
from kagg_revue.opponents.public import (
    PublicAgentRecord,
    _accepts_configuration,
    load_public_agent_manifest,
    resolve_public_agent_path,
)


class Panel(FrozenSettings):
    """Freeze sources, worlds, both seats and an optional recurrent reference."""

    manifest: Path
    output: Path
    candidates: tuple[str, ...]
    seeds: tuple[int, ...]
    anchor: str = "ahmed_v45"
    reference: Path | None = None
    workers: int = Field(default=8, ge=1, le=16)

    @model_validator(mode="after")
    def validate_panel(self) -> "Panel":
        """Reject duplicate worlds and ambiguous script identities."""
        if not self.seeds or len(set(self.seeds)) != len(self.seeds):
            raise ValueError("seeds must be nonempty and unique")
        if not self.candidates or len(set(self.candidates)) != len(self.candidates):
            raise ValueError("candidates must be nonempty and unique")
        if self.reference is None and self.anchor in self.candidates:
            raise ValueError("script anchor cannot be its own candidate")
        if not self.output.resolve().is_relative_to((Path.cwd() / "outputs").resolve()):
            raise ValueError("evaluation artifacts must remain under outputs")
        return self


def load_script(record: PublicAgentRecord) -> Callable[..., Any]:
    """Execute reviewed, hash-bound source and select the official final callable."""
    path = resolve_public_agent_path(record, Path.cwd())
    namespace: dict[str, Any] = {}
    exec(compile(path.read_text(), str(path), "exec"), namespace)
    function = cast(Callable[..., Any], [v for v in namespace.values() if callable(v)][-1])
    accepts_configuration = _accepts_configuration(function)

    def call(observation: dict[str, Any], configuration: dict[str, Any]) -> dict[str, Any]:
        value = (
            function(observation, configuration) if accepts_configuration else function(observation)
        )
        return dict(value)

    return call


class Reference:
    """Run a frozen FP32 actor with independent per-game memory and sampling."""

    def __init__(self, directory: Path, configuration: dict[str, Any], sample_seed: int) -> None:
        """Authenticate the serialized actor before allocating its causal buffers."""
        self.profile = json.loads((directory / "profile.json").read_text())
        if digest(directory / "actor.pt") != self.profile["actor_sha256"]:
            raise ValueError("reference actor identity changed")
        self.actor = torch.jit.load(str(directory / "actor.pt"), map_location="cpu").eval()  # type: ignore[no-untyped-call]
        self.session = native.ContractSession(configuration, self.profile["unit_limit"])
        self.features = np.empty((1, self.profile["observation_features"]), dtype=np.float16)
        self.inputs = torch.from_numpy(self.features)
        self.steps = torch.zeros(1, dtype=torch.long)
        self.memory: tuple[torch.Tensor, ...] = ()
        memory = self.profile["memory"]
        if memory["turns"]:
            capacity = memory["turns"] * memory["tokens"]
            shape = (
                memory["layers"],
                1,
                memory["heads"],
                capacity,
                memory["width"] // memory["heads"],
            )
            self.memory = (
                torch.zeros(shape),
                torch.zeros(shape),
                torch.full((capacity,), -1, dtype=torch.long),
            )
        self.rng = torch.Generator(device="cpu").manual_seed(sample_seed).get_state()

    def act(self, observation: dict[str, Any]) -> dict[str, Any]:
        """Consume every contiguous observation and return its grounded program."""
        self.session.update(observation)
        self.session.observe_into(self.features)
        self.steps.fill_(observation["step"])
        with torch.random.fork_rng(devices=[]), torch.inference_mode():
            torch.set_rng_state(self.rng)
            result = self.actor(self.inputs, self.steps, *self.memory)
            if self.memory:
                program, *following = result
                self.memory = tuple(following)
            else:
                program = result
            self.rng = torch.get_rng_state()
        self.session.set_program(program.numpy(), 1, self.profile["quantities"])
        return dict(self.session.program_action())


def play(job: dict[str, Any]) -> dict[str, Any]:
    """Play all 719 decisions; propagate failures instead of replacing with PASS."""
    torch.set_num_threads(1)
    candidate = load_script(PublicAgentRecord.model_validate(job["candidate"]))
    engine = native.Engine(job["seed"], job["environment"])
    configuration = dict(engine.configuration)
    seat = job["seat"]
    sample_seed = 2 * job["seed"] + 1 - seat
    opponent: Callable[..., Any]
    if job["reference"] is not None:
        reference = Reference(Path(job["reference"]), configuration, sample_seed)

        def opponent(observation: dict[str, Any], _: dict[str, Any]) -> dict[str, Any]:
            return reference.act(observation)
    else:
        opponent = load_script(PublicAgentRecord.model_validate(job["anchor"]))
    timings: list[list[float]] = [[], []]
    routes: list[Any] = []
    observations: list[Any] = []
    started = time.perf_counter()
    for turn in range(job["environment"]["episodeSteps"] - 1):
        obs = [dict(engine.observation(index)) for index in (0, 1)]
        actions: list[dict[str, Any]] = [{}, {}]
        for index, function in ((seat, candidate), (1 - seat, opponent)):
            phase = time.perf_counter()
            actions[index] = function(obs[index], configuration)
            timings[index].append(time.perf_counter() - phase)
        if job["retain_actions"]:
            routes.append(actions)
            if turn % 24 == 0:
                observations.append(obs)
        engine.step(*actions)
    if not engine.done:
        raise RuntimeError("game did not finish")
    overage = [60 - sum(max(0, duration - 1) for duration in row) for row in timings]
    if min(overage) < 0:
        raise RuntimeError("observed per-action time exhausted the overage budget")
    own, other = float(engine.money(seat)), float(engine.money(1 - seat))
    result = {
        "candidate": job["candidate"]["agent_id"],
        "anchor": job["anchor_name"],
        "seed": job["seed"],
        "seat": seat,
        "sampling_seed": sample_seed,
        "cash": own,
        "opponent_cash": other,
        "margin": own - other,
        "outcome": int(own > other) - int(own < other),
        "transitions": 719,
        "wall_seconds": time.perf_counter() - started,
        "max_action_seconds_by_seat": [max(row) for row in timings],
        "remaining_overage_by_seat": overage,
    }
    if routes:
        result.update(actions=routes, observations=observations)
    return result


def run(config: Panel) -> None:
    """Persist a prospective protocol and each independent paired-seat result."""
    records = load_public_agent_manifest(config.manifest).by_id()
    environment = {
        "boardSize": 10,
        "episodeSteps": 720,
        "turnsPerDay": 24,
        "maxMarketOrdersPerTurn": 10,
    }
    profile = None
    if config.reference is not None:
        profile = json.loads((config.reference / "profile.json").read_text())
        environment = profile["environment"]
    config.output.mkdir(parents=True, exist_ok=False)
    write_json(
        config.output / "protocol.json",
        {
            "configuration": config.model_dump(mode="json"),
            "manifest_sha256": digest(config.manifest),
            "profile": profile,
            "runner_sha256": digest(Path(__file__)),
            "engine_sha256": digest(Path(native.__file__)),
            "entrypoint": "last callable in fresh exec namespace, matching Kaggle",
        },
    )
    jobs = [
        {
            "candidate": records[name].model_dump(mode="json"),
            "anchor": records[config.anchor].model_dump(mode="json"),
            "anchor_name": config.reference.name if config.reference else config.anchor,
            "reference": str(config.reference) if config.reference else None,
            "environment": environment,
            "seed": seed,
            "seat": seat,
            "retain_actions": seed == config.seeds[0],
        }
        for name in config.candidates
        for seed in config.seeds
        for seat in (0, 1)
    ]
    rows: list[dict[str, Any]] = []
    with ProcessPoolExecutor(
        max_workers=config.workers, mp_context=multiprocessing.get_context("spawn")
    ) as pool:
        futures = {pool.submit(play, job): index for index, job in enumerate(jobs)}
        for future in as_completed(futures):
            row = future.result()
            write_json(config.output / "games" / f"{futures[future]:04d}.json", row)
            row = {
                key: value for key, value in row.items() if key not in {"actions", "observations"}
            }
            rows.append(row)
            print(json.dumps(row), flush=True)
    summary = {}
    for name in config.candidates:
        games = [row for row in rows if row["candidate"] == name]
        summary[name] = {
            "wins": sum(row["outcome"] == 1 for row in games),
            "draws": sum(row["outcome"] == 0 for row in games),
            "losses": sum(row["outcome"] == -1 for row in games),
            "mean_margin": float(np.mean([row["margin"] for row in games])),
        }
    write_json(config.output / "summary.json", {"summary": summary, "games": rows})
    print(json.dumps(summary), flush=True)


@hydra.main(version_base=None, config_path="../../../configs", config_name="notebook_survey")
def main(configuration: DictConfig) -> None:
    """Read the complete experiment specification through Hydra."""
    run(Panel.model_validate(OmegaConf.to_container(configuration.panel, resolve=True)))


if __name__ == "__main__":
    main()
