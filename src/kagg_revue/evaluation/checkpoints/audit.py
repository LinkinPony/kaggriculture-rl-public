"""Verify committed study evidence and unchanged live-training identities."""

import json
import math
import os
import shutil
import time
from collections import defaultdict
from itertools import pairwise
from pathlib import Path
from statistics import fmean
from typing import Any

from kagg_revue.artifacts.io import digest, write_json
from kagg_revue.evaluation.checkpoints.supervisor import health


def _stage(directory: Path, phase: str, size: int) -> dict[str, Any]:
    """Check every scheduled identity, paired seat and terminal outcome independently."""
    tasks = json.loads((directory / f"{phase}-schedule.json").read_text())
    paths = {p.stem: p for p in (directory / phase / "batches").glob("*.json")}
    if len(tasks) != len(paths) or {t["name"] for t in tasks} != set(paths):
        raise ValueError(f"{phase}: committed batches do not exactly cover the schedule")
    hashes = {}
    for task in tasks:
        path = paths[task["name"]]
        batch = json.loads(path.read_text())
        if batch["task"] != task or len(batch["games"]) != size:
            raise ValueError(f"{path}: task identity or sample count changed")
        identities = {(row["seed"], row["seat"]) for row in batch["games"]}
        expected = {
            (seed, seat)
            for seed in range(task["seed"], task["seed"] + size // 2)
            for seat in (0, 1)
        }
        if identities != expected:
            raise ValueError(f"{path}: seeds or swapped seats are incomplete")
        for row in batch["games"]:
            for key in ("candidate", "opponent", "group", "phase", "sampling_seed"):
                if row[key] != task[key]:
                    raise ValueError(f"{path}: game identity differs from its task")
            own, other = row["cash"], row["opponent_cash"]
            if not math.isfinite(own) or not math.isfinite(other):
                raise ValueError(f"{path}: non-finite terminal cash")
            if row["outcome"] != int(own > other) - int(own < other):
                raise ValueError(f"{path}: recorded outcome disagrees with terminal cash")
        hashes[path.name] = digest(path)
    supervised = json.loads((directory / phase / "supervisor-result.json").read_text())
    if supervised["reason"] != "complete" or any(supervised["exit_codes"]):
        raise ValueError(f"{phase}: supervisor did not finish successfully")
    statuses = [json.loads(p.read_text()) for p in (directory / phase).glob("worker-*-status.json")]
    if len(statuses) != len(supervised["exit_codes"]) or any(
        s["status"] != "complete" or not s["weights_unchanged"] for s in statuses
    ):
        raise ValueError(f"{phase}: missing successful worker weight verification")
    return {"tasks": len(tasks), "physical_games": size * len(tasks), "batch_sha256": hashes}


def _panel_scores(directory: Path, phase: str, report: dict[str, Any]) -> None:
    """Recompute reported means with ordinary Python, independently of NumPy tensors."""
    games: dict[tuple[str, str, str], list[float]] = defaultdict(list)
    for path in (directory / phase / "batches").glob("*.json"):
        for row in json.loads(path.read_text())["games"]:
            games[row["candidate"], row["group"], row["opponent"]].append((row["outcome"] + 1) / 2)
    for record in report[phase]["results"]:
        score = 0.0
        for group, weight in report["manifest"]["group_weights"].items():
            mean = fmean(
                fmean(values)
                for (candidate, family, _), values in games.items()
                if candidate == record["candidate"] and family == group
            )
            if abs(mean - record["family_scores"][group]) > 1e-12:
                raise ValueError(f"{phase}: opponent-family score disagrees with game records")
            score += weight * mean
        if abs(score - record["composite_score"]) > 1e-12:
            raise ValueError(f"{phase}: composite score disagrees with game records")


def verify(directory: Path) -> dict[str, Any]:
    """Write an auditable completion certificate without changing training or results."""
    report = json.loads((directory / "report.json").read_text())
    manifest = json.loads((directory / "manifest.json").read_text())
    frozen = json.loads((directory / "state.json").read_text())
    if (
        report["manifest"] != manifest
        or digest(directory / "state.json") != manifest["state_sha256"]
    ):
        raise ValueError("frozen manifest or training ledger changed")
    actors = {row["name"]: row for row in manifest["candidates"] + manifest["opponents"]}
    for actor in actors.values():
        if digest(Path(actor["path"])) != actor["sha256"]:
            raise ValueError(f"actor changed: {actor['name']}")
    phases = {"selection": 64, "round_robin": 32, "confirmation": 64, "final_duels": 32}
    stages = {name: _stage(directory, name, size) for name, size in phases.items()}
    for name, evidence in stages.items():
        field = "total_games" if name in ("selection", "confirmation") else "physical_games"
        if report[name][field] != evidence["physical_games"]:
            raise ValueError(f"{name}: report game count disagrees with committed evidence")
    for name in ("selection", "confirmation"):
        _panel_scores(directory, name, report)
    history = sorted(
        [
            json.loads(line)
            for name in phases
            for line in (directory / name / "health.jsonl").read_text().splitlines()
        ],
        key=lambda row: row["time"],
    )
    pids = {row["training_pid"] for row in history}
    if len(pids) != 1 or any(
        right["training_update"] < left["training_update"] for left, right in pairwise(history)
    ):
        raise ValueError("training process changed or training progress moved backwards")
    pid = pids.pop()
    current = health(Path(manifest["run"]), pid)
    live = json.loads((Path(manifest["run"]) / "state.json").read_text())
    for key in ("run_id", "protocol", "source", "native", "native_artifact"):
        if frozen[key] != live[key]:
            raise ValueError(f"training identity changed: {key}")
    if live["completed_update"] <= manifest["cutoff_update"]:
        raise ValueError("training did not advance beyond the frozen checkpoint")
    os.kill(pid, 0)
    verifier = directory / "audit-source.py"
    shutil.copy2(__file__, verifier)
    result = {
        "verified_at": time.time(),
        "verifier_sha256": digest(verifier),
        "report_sha256": digest(directory / "report.json"),
        "actors_verified": {name: row["sha256"] for name, row in actors.items()},
        "stages": stages,
        "total_formal_games": sum(stage["physical_games"] for stage in stages.values()),
        "panel_scores_independently_recomputed": True,
        "training": {
            "same_pid": pid,
            "same_run_id": live["run_id"],
            "protocol_source_native_unchanged": True,
            "frozen_update": manifest["cutoff_update"],
            "latest_completed_update": live["completed_update"],
            "current_health": current,
            "health_samples": len(history),
            "minimum_free_mib": min(gpu[1] for row in history for gpu in row["gpus"]),
            "maximum_heartbeat_age": max(row["training_heartbeat_age"] for row in history),
        },
    }
    write_json(directory / "completion-verification.json", result)
    return result
