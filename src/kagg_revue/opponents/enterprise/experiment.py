"""Complete reacting games for independent economic director experiments."""

import hashlib
import multiprocessing
import shutil
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import hydra
import orjson
from omegaconf import DictConfig, OmegaConf
from pydantic import BaseModel, ConfigDict

from kagg_revue.artifacts.io import digest, write_json
from kagg_revue.evaluation.accounting import GameAccounting
from kagg_revue.opponents.enterprise.agent import Director
from kagg_revue.opponents.public import (
    PublicAgentRecord,
    PublicAgentRuntime,
    load_public_agent_manifest,
)
from kagg_revue.opponents.research.arena import summarize


class Panel(BaseModel):
    """Declare a complete independent-prototype panel before observing its outcomes."""

    model_config = ConfigDict(extra="forbid", frozen=True)
    manifest: Path
    output: Path
    variants: dict[str, dict[str, Any]]
    opponents: tuple[str, ...]
    seeds: tuple[int, ...]
    workers: int = 8
    trace: bool = False
    source: Path | None = None


@dataclass(frozen=True)
class Game:
    """A fixed source opponent, world, seat and independent director recipe."""

    variant: str
    settings: dict[str, Any]
    opponent: PublicAgentRecord
    seed: int
    seat: int
    trace: bool
    source: Path | None = None
    source_sha256: str | None = None


def play(job: Game) -> dict[str, Any]:
    """Run a full season with original public opponents observing every real action."""
    from kagg_revue.native import _revue_native as native

    engine = native.Engine(job.seed, {})
    if job.source is not None:
        from kagg_revue.opponents.research.qualification import _agent

        if digest(job.source) != job.source_sha256:
            raise ValueError("frozen independent source changed")
        candidate: Any = SimpleNamespace(act=_agent(job.source, "none"), ranking=[])
    elif job.settings.get("native_execution"):
        from kagg_revue.opponents.enterprise.allocation import Allocator

        candidate = Allocator(dict(engine.configuration), job.settings)
    else:
        candidate = Director(dict(engine.configuration), job.settings)
    opponent = PublicAgentRuntime(job.opponent, Path.cwd(), dict(engine.configuration))
    fingerprint = hashlib.sha256()
    timeline = []
    accounting = GameAccounting(24) if job.trace else None
    started = time.perf_counter()
    for step in range(719):
        obs = dict(engine.observation(job.seat))
        action = candidate.act(obs)
        other_obs = dict(engine.observation(1 - job.seat))
        other = opponent.act(other_obs)
        fingerprint.update(orjson.dumps(action, option=orjson.OPT_SORT_KEYS))
        fingerprint.update(b"\0")
        if job.trace and (step % 24 == 0 or step % 24 == 23 or step == 718):
            timeline.append({"observation": obs, "action": action, "ranking": candidate.ranking})
        actions = [action, other] if job.seat == 0 else [other, action]
        if accounting is None:
            engine.step(*actions)
        else:
            observations = [obs, other_obs] if job.seat == 0 else [other_obs, obs]
            trace = engine.step_with_trace(*actions)
            accounting.record(
                observations, actions, trace, [float(engine.money(s)) for s in (0, 1)]
            )
    if not engine.done:
        raise RuntimeError("incomplete economic director game")
    own, other_cash = float(engine.money(job.seat)), float(engine.money(1 - job.seat))
    return {
        "variant": job.variant,
        "opponent": job.opponent.agent_id,
        "seed": job.seed,
        "seat": job.seat,
        "cash": own,
        "opponent_cash": other_cash,
        "margin": own - other_cash,
        "outcome": int(own > other_cash) - int(own < other_cash),
        "action_sha256": fingerprint.hexdigest(),
        "timeline": timeline,
        "wall_seconds": time.perf_counter() - started,
        "accounting": accounting.finish([dict(engine.observation(s)) for s in (0, 1)])
        if accounting is not None
        else None,
    }


def run(config: Panel) -> None:
    """Freeze source snapshots and retain every complete game before summarizing."""
    if not config.output.resolve().is_relative_to((Path.cwd() / "outputs").resolve()):
        raise ValueError("research output must remain under outputs")
    config.output.mkdir(parents=True, exist_ok=False)
    source = Path(__file__).parent
    shutil.copytree(source, config.output / "source", ignore=shutil.ignore_patterns("__pycache__"))
    write_json(
        config.output / "protocol.json",
        {
            "configuration": config.model_dump(mode="json"),
            "source_sha256": {p.name: digest(p) for p in source.glob("*.py")},
            "manifest_sha256": digest(config.manifest),
        },
    )
    records = load_public_agent_manifest(config.manifest).by_id()
    jobs = [
        Game(
            name,
            settings,
            records[opponent],
            seed,
            seat,
            config.trace,
            config.source,
            digest(config.source) if config.source is not None else None,
        )
        for name, settings in config.variants.items()
        for opponent in config.opponents
        for seed in config.seeds
        for seat in (0, 1)
    ]
    rows = []
    with ProcessPoolExecutor(
        max_workers=config.workers,
        mp_context=multiprocessing.get_context("spawn"),
        max_tasks_per_child=1,
    ) as pool:
        futures = {pool.submit(play, job): index for index, job in enumerate(jobs)}
        for future in as_completed(futures):
            row = future.result()
            rows.append(row)
            write_json(config.output / "games" / f"{futures[future]:04d}.json", row)
            print(f"{len(rows)}/{len(jobs)} {row['variant']} {row['margin']:.0f}", flush=True)
    write_json(config.output / "summary.json", summarize(rows))


@hydra.main(version_base=None, config_path="../../../../configs", config_name="enterprise")
def main(configuration: DictConfig) -> None:
    """Resolve the independently authored economic controller's experiment."""
    run(Panel.model_validate(OmegaConf.to_container(configuration.panel, resolve=True)))


if __name__ == "__main__":
    main()
