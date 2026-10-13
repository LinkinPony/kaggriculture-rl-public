"""Standalone one-stage panel: every candidate against frozen neural opponent families."""

import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Literal

import hydra
import torch
from omegaconf import DictConfig, OmegaConf
from pydantic import Field

from kagg_revue.artifacts.io import digest, write_json
from kagg_revue.configuration import FrozenSettings
from kagg_revue.evaluation.checkpoints import reporting, schedule
from kagg_revue.native import _revue_core


class Entry(FrozenSettings):
    """A registered run member, or an already frozen actor file."""

    name: str
    group: str = "current"
    run: Path | None = None
    member: str | None = None
    path: Path | None = None
    temperature: float = Field(default=1.0, ge=0, allow_inf_nan=False)


class PanelStudy(FrozenSettings):
    """Common-seed candidate-by-opponent panel, or a complete candidate round robin."""

    output: Path
    mode: Literal["panel", "round_robin"] = "panel"
    candidates: tuple[Entry, ...]
    opponents: tuple[Entry, ...] = ()
    games: int = Field(default=128, ge=64, multiple_of=64)
    seed: int = Field(ge=0)
    sampling_seed: int = Field(ge=0)
    devices: tuple[str, ...] = ("cuda:0", "cuda:1")
    batch_games: int = Field(default=64, gt=0, multiple_of=2)
    memory_fraction: float = Field(default=0.06, gt=0, le=0.08)
    precision: Literal["bf16", "fp32"] = "bf16"
    minimum_free_mib: int = Field(default=12288, ge=8192)
    scope: str


def _source(entry: Entry) -> Path:
    if entry.path is not None:
        return entry.path
    if entry.run is None:
        raise ValueError(f"entry needs a run or a frozen path: {entry.name}")
    state = json.loads((entry.run / "state.json").read_text())
    member = entry.member or state["rl_initial"]
    source = entry.run / member
    if digest(source) != state["members"][member]:
        raise ValueError(f"member differs from its run ledger: {entry.name}")
    return source


def freeze(study: PanelStudy) -> dict[str, Any]:
    """Copy only the actor fields evaluated by the worker; hashes pin every input."""
    target = study.output / "manifest.json"
    if target.exists():
        return dict(json.loads(target.read_text()))
    rows: dict[str, list[dict[str, Any]]] = {"candidates": [], "opponents": []}
    for role, entries in (("candidates", study.candidates), ("opponents", study.opponents)):
        for entry in entries:
            source = _source(entry)
            raw = torch.load(source, map_location="cpu", weights_only=False, mmap=True)
            path = study.output / "actors" / f"{entry.name}.pt"
            path.parent.mkdir(parents=True, exist_ok=True)
            torch.save({k: raw[k] for k in ("model", "layout", "settings", "lineage")}, path)
            rows[role].append(
                {
                    "name": entry.name,
                    "path": str(path),
                    "sha256": digest(path),
                    "source": str(source),
                    "checkpoint_sha256": digest(source),
                    "kind": "candidate" if role == "candidates" else "neural",
                    "group": entry.group,
                    "temperature": entry.temperature,
                }
            )
    groups = sorted({row["group"] for row in rows["opponents"]})
    manifest = {
        **rows,
        "scripts": [],
        "group_weights": {group: 1.0 / len(groups) for group in groups} if groups else {},
        "native_sha256": digest(Path(_revue_core.__file__)),
        "run": None,
        "scope": study.scope,
    }
    write_json(target, manifest)
    return manifest


def _free_mib() -> int:
    raw = subprocess.check_output(
        ["nvidia-smi", "--query-gpu=memory.free", "--format=csv,noheader,nounits"],
        text=True,
        timeout=10,
    )
    return min(int(line) for line in raw.split())


def run(study: PanelStudy) -> dict[str, Any]:
    """Resume committed batches; stop evaluators only if GPU reserve is crossed."""
    study.output.mkdir(parents=True, exist_ok=True)
    manifest = freeze(study)
    candidates = [row["name"] for row in manifest["candidates"]]
    if study.mode == "round_robin":
        tasks = schedule.duels(candidates, study.mode, study.games, study.seed, study.sampling_seed)
        batch_games = 32
    else:
        tasks = schedule.panel(
            manifest, candidates, study.mode, study.games, study.seed, study.sampling_seed
        )
        batch_games = study.batch_games
    path = study.output / f"{study.mode}-schedule.json"
    values = [task.model_dump(mode="json") for task in tasks]
    if path.exists() and json.loads(path.read_text()) != values:
        raise ValueError("cannot revise an already started panel")
    write_json(path, values)
    output = study.output / study.mode
    output.mkdir(parents=True, exist_ok=True)
    processes = []
    for shard, device in enumerate(study.devices):
        stream = (output / f"worker-{shard}.log").open("ab")
        processes.append(
            subprocess.Popen(
                [
                    sys.executable,
                    "-m",
                    "kagg_revue.evaluation.checkpoints.worker",
                    f"comparison.manifest={study.output / 'manifest.json'}",
                    f"comparison.schedule={path}",
                    f"comparison.output={output}",
                    f"comparison.device={device}",
                    f"comparison.batch_games={batch_games}",
                    f"comparison.memory_fraction={study.memory_fraction}",
                    f"+comparison.precision={study.precision}",
                    f"comparison.shard={shard}",
                    f"comparison.shards={len(study.devices)}",
                ],
                stdout=stream,
                stderr=subprocess.STDOUT,
            )
        )
    try:
        while any(p.poll() is None for p in processes):
            if _free_mib() < study.minimum_free_mib:
                raise RuntimeError("GPU reserve crossed; stopping panel evaluators")
            if any(p.poll() not in (None, 0) for p in processes):
                raise RuntimeError("a panel worker failed")
            time.sleep(10)
    finally:
        for process in processes:
            if process.poll() is None:
                process.terminate()
    if any(p.returncode != 0 for p in processes):
        raise RuntimeError("a panel worker failed")
    if study.mode == "round_robin":
        return reporting.round_robin(output, candidates)
    return reporting.summarize(manifest, output, candidates, role="panel")


@hydra.main(version_base=None, config_path="../../../../configs", config_name="evaluation_panel")
def main(configuration: DictConfig) -> None:
    """Run one configured panel or round robin and print its ranking."""
    study = PanelStudy.model_validate(OmegaConf.to_container(configuration.study, resolve=True))
    report = run(study)
    keys = ("candidate", "composite_score", "score")
    for row in report.get("results", report.get("ranking", [])):
        print(json.dumps({k: row[k] for k in row if k in keys}))


if __name__ == "__main__":
    main()
