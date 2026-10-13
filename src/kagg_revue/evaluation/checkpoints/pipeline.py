"""Run screening, held-out confirmation and direct finalist matches within a deadline."""

import json
import tarfile
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import hydra
from omegaconf import DictConfig, OmegaConf
from pydantic import Field

from kagg_revue.artifacts.io import digest, write_json
from kagg_revue.configuration import FrozenSettings
from kagg_revue.evaluation.checkpoints import reporting, schedule
from kagg_revue.evaluation.checkpoints.config import Task
from kagg_revue.evaluation.checkpoints.supervisor import Supervision
from kagg_revue.evaluation.checkpoints.supervisor import run as supervised
from kagg_revue.learning.state import source_identity


class Study(FrozenSettings):
    """Fix ranking rules, controls and an absolute stopping time before screening."""

    manifest: Path
    output: Path
    deadline: datetime
    devices: tuple[str, ...] = ("cuda:0", "cuda:1")
    memory_fraction: float = Field(default=0.06, gt=0, le=0.08)
    selection_games: int = Field(default=64, ge=64, multiple_of=64)
    confirmation_base_games: int = Field(default=128, ge=64, multiple_of=64)
    confirmation_games: int = Field(default=192, ge=64, multiple_of=64)
    controls: tuple[str, ...] = ("u0588", "u0616")
    final_duel_games: int = Field(default=256, ge=32, multiple_of=32)


def execute(study: Study, name: str, tasks: list[Task], batch_games: int) -> None:
    """Persist the entire stage schedule before any of its outcomes are generated."""
    path = study.output / f"{name}-schedule.json"
    values = [task.model_dump(mode="json") for task in tasks]
    if path.exists() and json.loads(path.read_text()) != values:
        raise ValueError("cannot revise an already started stage")
    write_json(path, values)
    remaining = int(study.deadline.timestamp() - time.time())
    if remaining <= 0:
        raise RuntimeError("study reached its absolute budget deadline")
    write_json(study.output / "progress.json", {"stage": name, "started_at": time.time()})
    supervised(
        Supervision(
            manifest=study.manifest,
            schedule=path,
            output=study.output / name,
            devices=study.devices,
            batch_games=batch_games,
            memory_fraction=study.memory_fraction,
            maximum_seconds=min(28800, remaining),
        )
    )


def run(study: Study) -> dict[str, Any]:
    """Choose finalists using screening only, then give all finalists equal new seeds."""
    manifest = json.loads(study.manifest.read_text())
    candidates = [row["name"] for row in manifest["candidates"]]
    study.output.mkdir(parents=True, exist_ok=True)
    protocol = study.model_dump(mode="json")
    protocol.update(
        manifest_sha256=digest(study.manifest),
        primary_metric="Equal-family mean of win=1, draw=0.5, loss=0; cash is diagnostic only.",
        shortlist=(
            "All candidates whose simultaneous screening leader-gap interval includes zero, "
            "submitted/latest controls and round-robin winner. Amendment 0002 followed screening."
        ),
        confirmation_budget_rule=(
            "Complete 128 games/opponent for the entire cohort; before inspecting outcomes, "
            "extend everyone to 192 only if measured confirmation throughput with 15% overhead "
            "and 25 minutes reserve fits the remaining deadline."
        ),
        phase_seeds={
            "selection": 9300000000,
            "round_robin": 9310000000,
            "confirmation": 9320000000,
            "final_duels": 9330000000,
        },
    )
    previous = study.output / "protocol.json"
    if previous.exists() and json.loads(previous.read_text()) != protocol:
        raise ValueError("study protocol changed on resume")
    write_json(previous, protocol)
    identity = source_identity()
    write_json(study.output / "source.json", identity)
    if not (study.output / "source.tar.gz").exists():
        with tarfile.open(study.output / "source.tar.gz", "w:gz") as archive:
            for name in identity["files"]:
                archive.add(name, arcname=name, recursive=False)
    execute(
        study,
        "selection",
        schedule.panel(
            manifest, candidates, "selection", study.selection_games, 9300000000, 93000001
        ),
        64,
    )
    selection = reporting.summarize(
        manifest, study.output / "selection", candidates, role="selection"
    )
    execute(
        study,
        "round_robin",
        schedule.duels(candidates, "round_robin", 32, 9310000000, 93100001),
        32,
    )
    robin = reporting.round_robin(study.output / "round_robin", candidates)
    chosen = [
        row["candidate"]
        for row in selection["results"]
        if row["leader_difference_simultaneous_ci95"][0] <= 0
    ]
    for name in (*study.controls, robin["ranking"][0]["candidate"]):
        if name not in chosen:
            chosen.append(name)
    shortlist_path = study.output / "shortlist.json"
    if shortlist_path.exists():
        decision = json.loads(shortlist_path.read_text())
        if decision["candidates"] != chosen:
            raise ValueError("shortlist changed on resume")
    else:
        decision = {
            "candidates": chosen,
            "base_games_per_opponent": study.confirmation_base_games,
            "maximum_games_per_opponent": study.confirmation_games,
            "chosen_at": time.time(),
        }
        write_json(shortlist_path, decision)
    confirm(study, manifest, chosen)
    confirmation = reporting.summarize(
        manifest, study.output / "confirmation", chosen, role="held_out_confirmation"
    )
    final_names = [row["candidate"] for row in confirmation["results"][:4]]
    execute(
        study,
        "final_duels",
        schedule.duels(final_names, "final_duels", study.final_duel_games, 9330000000, 93300001),
        32,
    )
    final = reporting.round_robin(study.output / "final_duels", final_names)
    result = {
        "completed_at": time.time(),
        "manifest": manifest,
        "protocol": protocol,
        "selection": selection,
        "round_robin": robin,
        "confirmation": confirmation,
        "final_duels": final,
    }
    write_json(study.output / "report.json", result)
    write_json(study.output / "progress.json", {"stage": "complete", "time": time.time()})
    return result


def confirm(study: Study, manifest: dict[str, Any], chosen: list[str]) -> None:
    """Complete a balanced base panel and make one outcome-blind extension decision."""
    base_games, maximum = study.confirmation_base_games, study.confirmation_games
    if maximum < base_games:
        raise ValueError("confirmation maximum must cover the base panel")
    path = study.output / "confirmation-extension.json"
    if not path.exists():
        execute(
            study,
            "confirmation",
            schedule.panel(manifest, chosen, "confirmation", base_games, 9320000000, 93200001),
            64,
        )
        worker_seconds = sum(
            json.loads(batch.read_text())["total_seconds"]
            for batch in (study.output / "confirmation/batches").glob("*.json")
        )
        extra = worker_seconds * (maximum / base_games - 1) / len(study.devices)
        remaining = study.deadline.timestamp() - time.time()
        write_json(
            path,
            {
                "decided_at": time.time(),
                "base_worker_seconds": worker_seconds,
                "extension_estimated_seconds": extra,
                "remaining_seconds": remaining,
                "games_per_opponent": maximum if extra * 1.15 + 1500 < remaining else base_games,
                "outcomes_used": False,
            },
        )
    games = int(json.loads(path.read_text())["games_per_opponent"])
    tasks = schedule.panel(manifest, chosen, "confirmation", games, 9320000000, 93200001)
    target = study.output / "confirmation-schedule.json"
    values = [task.model_dump(mode="json") for task in tasks]
    previous = json.loads(target.read_text())
    if previous != values:
        indexed = {row["name"]: row for row in values}
        if any(indexed.get(row["name"]) != row for row in previous):
            raise ValueError("confirmation extension changed an existing task")
        write_json(study.output / "confirmation-base-schedule.json", previous)
        write_json(target, values)
    execute(study, "confirmation", tasks, 64)


@hydra.main(
    version_base=None, config_path="../../../../configs", config_name="evaluation_checkpoints_study"
)
def main(configuration: DictConfig) -> None:
    """Run a complete study whose durable outputs survive evaluator restarts."""
    options = Study.model_validate(OmegaConf.to_container(configuration.study, resolve=True))
    print(json.dumps({"winner": run(options)["confirmation"]["leader"]}), flush=True)


if __name__ == "__main__":
    main()
