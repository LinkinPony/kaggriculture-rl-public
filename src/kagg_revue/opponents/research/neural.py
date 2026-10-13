"""Evaluate script improvements against an authenticated frozen neural reference."""

import ast
import json
import multiprocessing
import shutil
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import hydra
import numpy as np
import torch
from omegaconf import DictConfig, OmegaConf
from pydantic import BaseModel, ConfigDict, Field

from kagg_revue.artifacts.io import digest, write_json
from kagg_revue.native import _revue_core as native
from kagg_revue.native.features import Layout
from kagg_revue.opponents.public import PublicAgentRecord, load_public_agent_manifest
from kagg_revue.opponents.research.arena import summarize
from kagg_revue.opponents.research.runtime import ResearchRuntime
from kagg_revue.opponents.research.settings import Variant


class NeuralPanel(BaseModel):
    """Declare the exact neural checkpoint, scripts, and fresh research seeds."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    reference: Path
    manifest: Path
    output: Path
    variants: tuple[Variant, ...]
    seeds: tuple[int, ...]
    workers: int = Field(default=4, ge=1, le=16)
    resume: bool = False


@dataclass(frozen=True)
class NeuralGame:
    """One scripted seat facing the same fixed neural sampling configuration."""

    reference: Path
    metadata: dict[str, Any]
    record: PublicAgentRecord
    variant: Variant
    seed: int
    seat: int


def play(job: NeuralGame) -> dict[str, Any]:
    """Run full observed games and retain neural routes for offline investigation."""
    torch.set_num_threads(1)
    actor_path = job.reference / "actor.pt"
    if digest(actor_path) != job.metadata["actor_sha256"]:
        raise ValueError("neural actor hash changed")
    actor = torch.jit.load(str(actor_path), map_location="cpu").eval()  # type: ignore[no-untyped-call]
    layout = Layout(**job.metadata["layout"]["observation"])
    environment = job.metadata["settings"]["environment"]
    engine = native.Engine(job.seed, environment)
    session = native.ContractSession(environment, layout.units)
    script = ResearchRuntime(job.record, dict(engine.configuration), job.variant)
    features = np.empty((1, layout.features), dtype=np.float16)
    inputs = torch.from_numpy(features)
    steps = torch.zeros(1, dtype=torch.long)
    torch.manual_seed(job.seed * 2 + (1 - job.seat))
    routes = []
    timeline = []
    timings = []
    started = time.perf_counter()
    with torch.inference_mode():
        for turn in range(719):
            observations = [dict(engine.observation(seat)) for seat in (0, 1)]
            session.update(observations[1 - job.seat])
            session.observe_into(features)
            steps.fill_(turn)
            phase = time.perf_counter()
            program = actor(inputs, steps).numpy()
            timings.append(time.perf_counter() - phase)
            session.set_program(program, 1, list(layout.quantities))
            neural_action = dict(session.program_action())
            script_action = script.act(observations[job.seat])
            actions = (
                [script_action, neural_action] if job.seat == 0 else [neural_action, script_action]
            )
            routes.append(actions)
            if turn % 24 == 0:
                timeline.append(
                    {
                        "step": turn,
                        "cash": [engine.money(seat) for seat in (0, 1)],
                        "shops": observations[0]["town"]["unlocked_shops"],
                        "neural_observation": observations[1 - job.seat],
                    }
                )
            engine.step(*actions)
    if not engine.done:
        raise RuntimeError("neural comparison did not finish")
    own, other = float(engine.money(job.seat)), float(engine.money(1 - job.seat))
    return {
        "variant": job.variant.name,
        "opponent": f"neural_u{job.metadata['update']}",
        "seed": job.seed,
        "seat": job.seat,
        "cash": own,
        "opponent_cash": other,
        "margin": own - other,
        "outcome": int(own > other) - int(own < other),
        "actions": routes,
        "timeline": timeline,
        "counters": script.counters,
        "wall_seconds": time.perf_counter() - started,
        "inference_mean_ms": float(np.mean(timings) * 1000),
    }


def _prepare(config: NeuralPanel, metadata: dict[str, Any]) -> None:
    """Resume only identical game semantics and retain the original declaration."""
    configuration = config.model_dump(mode="json")
    runner = Path(__file__)
    if config.resume:
        previous = json.loads((config.output / "protocol.json").read_text())
        old = dict(previous["configuration"])
        for values in (old, configuration):
            values.pop("workers", None)
            values.pop("resume", None)
        if old != configuration or previous["reference"] != metadata:
            raise ValueError("resume changes the declared neural experiment")
        for name in ("runtime.py", "market.py", "settings.py"):
            path = runner.with_name(name)
            if previous["source"][str(path)] != digest(path):
                raise ValueError("resume changes the script controller")
        archived = config.output / "original-runner.py"

        def signature(path: Path) -> str:
            tree = ast.parse(path.read_text())
            play = next(
                node
                for node in tree.body
                if isinstance(node, ast.FunctionDef) and node.name == "play"
            )
            return ast.dump(play, include_attributes=False)

        if signature(archived) != signature(runner):
            raise ValueError("resume changes the neural game or inference implementation")
        write_json(
            config.output / "resume.json",
            {
                "configuration": config.model_dump(mode="json"),
                "runner_sha256": digest(runner),
                "original_runner_sha256": digest(archived),
                "manifest_sha256": digest(config.manifest),
                "game_function_ast_unchanged": True,
            },
        )
        return
    config.output.mkdir(parents=True, exist_ok=False)
    shutil.copy2(runner, config.output / "original-runner.py")
    write_json(
        config.output / "protocol.json",
        {
            "configuration": configuration,
            "reference": metadata,
            "source": {str(p): digest(p) for p in runner.parent.glob("*.py")},
            "manifest_sha256": digest(config.manifest),
            "sampling": "CPU FP32 T=1; one RNG stream per game, seed=2*world+neural_seat",
        },
    )


def run(config: NeuralPanel) -> None:
    """Freeze the reference identity and write each complete game as it finishes."""
    if not config.output.resolve().is_relative_to((Path.cwd() / "outputs").resolve()):
        raise ValueError("neural comparison artifacts must remain under outputs")
    metadata = json.loads((config.reference / "manifest.json").read_text())
    records = load_public_agent_manifest(config.manifest).by_id()
    _prepare(config, metadata)
    jobs = [
        NeuralGame(config.reference, metadata, records[v.base], v, seed, seat)
        for v in config.variants
        for seed in config.seeds
        for seat in (0, 1)
    ]
    rows = []
    pending = {}
    for index, job in enumerate(jobs):
        path = config.output / "games" / f"{index:04d}.json"
        if not path.exists():
            pending[index] = job
            continue
        row = json.loads(path.read_text())
        if (row["variant"], row["seed"], row["seat"], row["opponent"]) != (
            job.variant.name,
            job.seed,
            job.seat,
            f"neural_u{metadata['update']}",
        ) or len(row["actions"]) != 719:
            raise ValueError("saved neural game does not match its declared job")
        rows.append(row)
    with ProcessPoolExecutor(
        max_workers=config.workers,
        mp_context=multiprocessing.get_context("spawn"),
        max_tasks_per_child=1,
    ) as pool:
        futures = {pool.submit(play, job): index for index, job in pending.items()}
        for future in as_completed(futures):
            row = future.result()
            write_json(config.output / "games" / f"{futures[future]:04d}.json", row)
            rows.append(row)
            print(f"completed {len(rows)}/{len(jobs)}", flush=True)
    write_json(config.output / "summary.json", summarize(rows))


@hydra.main(version_base=None, config_path="../../../../configs", config_name="script_neural")
def main(configuration: DictConfig) -> None:
    """Resolve the independent neural-reference research panel."""
    run(NeuralPanel.model_validate(OmegaConf.to_container(configuration.panel, resolve=True)))


if __name__ == "__main__":
    main()
