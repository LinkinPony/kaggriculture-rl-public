"""Orchestration and reporting for public-notebook opponent benchmarks."""

from __future__ import annotations

import hashlib
import json
import multiprocessing
import statistics
import time
from collections import defaultdict
from collections.abc import Mapping, Sequence
from concurrent.futures import Future, ProcessPoolExecutor, as_completed
from importlib import import_module
from itertools import combinations
from pathlib import Path
from typing import Any, cast

import numpy as np

from kagg_revue.core.backend import load_backend
from kagg_revue.core.provenance import source_identity
from kagg_revue.opponents.config import OpponentBenchmarkSettings
from kagg_revue.opponents.match import MatchJob, run_match_job
from kagg_revue.opponents.public import PublicAgentRecord, load_public_agent_manifest

_BUFFER_SIZE = 1024 * 1024


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(_BUFFER_SIZE):
            digest.update(chunk)
    return digest.hexdigest()


def _pairings(settings: OpponentBenchmarkSettings) -> tuple[tuple[str, str], ...]:
    if settings.anchor_id is None:
        return tuple(combinations(settings.agent_ids, 2))
    return tuple(
        (agent_id, settings.anchor_id)
        for agent_id in settings.agent_ids
        if agent_id != settings.anchor_id
    )


def _match_jobs(
    settings: OpponentBenchmarkSettings,
    repository_root: Path,
    records: Mapping[str, PublicAgentRecord],
) -> list[MatchJob]:
    jobs: list[MatchJob] = []
    for agent_a_id, agent_b_id in _pairings(settings):
        for seed in settings.seeds:
            for seat in (0, 1):
                jobs.append(
                    MatchJob(
                        repository_root=str(repository_root),
                        engine=settings.engine,
                        environment=dict(settings.environment),
                        act_timeout_seconds=settings.act_timeout_seconds,
                        remaining_overage_seconds=settings.remaining_overage_seconds,
                        agent_a=cast(
                            dict[str, object], records[agent_a_id].model_dump(mode="json")
                        ),
                        agent_b=cast(
                            dict[str, object], records[agent_b_id].model_dump(mode="json")
                        ),
                        seed=seed,
                        agent_a_seat=seat,
                    )
                )
    return jobs


def _numeric_mapping(row: Mapping[str, Any], name: str) -> Mapping[str, float]:
    value = row[name]
    if not isinstance(value, Mapping):
        raise TypeError(f"match {name} is not a mapping")
    return cast(Mapping[str, float], value)


def _integer_mapping(row: Mapping[str, Any], name: str) -> Mapping[str, int]:
    value = row[name]
    if not isinstance(value, Mapping):
        raise TypeError(f"match {name} is not a mapping")
    return cast(Mapping[str, int], value)


def _timing_mapping(row: Mapping[str, Any]) -> Mapping[str, Mapping[str, Any]]:
    value = row["timing"]
    if not isinstance(value, Mapping):
        raise TypeError("match timing is not a mapping")
    return cast(Mapping[str, Mapping[str, Any]], value)


def _summary(
    rows: Sequence[Mapping[str, Any]],
    agent_ids: Sequence[str],
    samples: Mapping[str, Sequence[int]],
    elapsed_seconds: float,
    workers: int,
) -> dict[str, object]:
    outcomes: dict[str, list[int]] = defaultdict(list)
    cash: dict[str, list[float]] = defaultdict(list)
    margins: dict[str, list[float]] = defaultdict(list)
    initialization: dict[str, list[float]] = defaultdict(list)
    match_wall: dict[str, list[float]] = defaultdict(list)
    errors: dict[str, int] = defaultdict(int)
    status_failures: dict[str, int] = defaultdict(int)
    total_calls = 0
    total_transitions = 0
    for row in rows:
        seat_ids = cast(list[str], row["seat_agent_ids"])
        row_outcomes = _integer_mapping(row, "outcome")
        row_cash = _numeric_mapping(row, "money")
        row_margins = _numeric_mapping(row, "margin")
        row_timing = _timing_mapping(row)
        statuses = cast(Mapping[str, str], row["status"])
        total_transitions += int(row["transitions"])
        for agent_id in seat_ids:
            outcomes[agent_id].append(int(row_outcomes[agent_id]))
            cash[agent_id].append(float(row_cash[agent_id]))
            margins[agent_id].append(float(row_margins[agent_id]))
            timing = row_timing[agent_id]
            initialization[agent_id].append(float(timing["initialization_seconds"]))
            match_wall[agent_id].append(float(row["match_wall_seconds"]))
            errors[agent_id] += timing["error"] is not None
            status_failures[agent_id] += statuses[agent_id] != "DONE"
            total_calls += int(timing["calls"])

    agents: dict[str, object] = {}
    for agent_id in agent_ids:
        agent_outcomes = outcomes[agent_id]
        timing_ns = np.asarray(samples[agent_id], dtype=np.int64)
        total_act_seconds = float(timing_ns.sum()) / 1_000_000_000
        agents[agent_id] = {
            "games": len(agent_outcomes),
            "wins": sum(outcome > 0 for outcome in agent_outcomes),
            "ties": sum(outcome == 0 for outcome in agent_outcomes),
            "losses": sum(outcome < 0 for outcome in agent_outcomes),
            "mean_terminal_cash": statistics.fmean(cash[agent_id]),
            "mean_cash_difference": statistics.fmean(margins[agent_id]),
            "errors": errors[agent_id],
            "non_done_statuses": status_failures[agent_id],
            "timing": {
                "calls": int(timing_ns.size),
                "total_act_seconds": total_act_seconds,
                "actions_per_second": (
                    float(timing_ns.size) / total_act_seconds if total_act_seconds else None
                ),
                "p50_ms": float(np.percentile(timing_ns, 50)) / 1_000_000,
                "p95_ms": float(np.percentile(timing_ns, 95)) / 1_000_000,
                "p99_ms": float(np.percentile(timing_ns, 99)) / 1_000_000,
                "max_ms": float(timing_ns.max()) / 1_000_000,
                "initialization_p50_ms": (statistics.median(initialization[agent_id]) * 1000),
                "initialization_max_ms": max(initialization[agent_id]) * 1000,
                "fresh_match_wall_p50_seconds": statistics.median(match_wall[agent_id]),
            },
        }

    pairwise: list[dict[str, object]] = []
    for agent_a_id, agent_b_id in combinations(agent_ids, 2):
        pair_rows = [
            row
            for row in rows
            if {str(row["agent_a_id"]), str(row["agent_b_id"])} == {agent_a_id, agent_b_id}
        ]
        if not pair_rows:
            continue
        pair_outcomes = [int(_integer_mapping(row, "outcome")[agent_a_id]) for row in pair_rows]
        paired_margins: dict[int, float] = defaultdict(float)
        for row in pair_rows:
            paired_margins[int(row["seed"])] += float(_numeric_mapping(row, "margin")[agent_a_id])
        pairwise.append(
            {
                "agent_a_id": agent_a_id,
                "agent_b_id": agent_b_id,
                "games": len(pair_outcomes),
                "agent_a_wins": sum(outcome > 0 for outcome in pair_outcomes),
                "ties": sum(outcome == 0 for outcome in pair_outcomes),
                "agent_a_losses": sum(outcome < 0 for outcome in pair_outcomes),
                "paired_seed_wins": sum(value > 0 for value in paired_margins.values()),
                "paired_seed_ties": sum(value == 0 for value in paired_margins.values()),
                "paired_seed_losses": sum(value < 0 for value in paired_margins.values()),
                "mean_agent_a_cash_difference": statistics.fmean(
                    float(_numeric_mapping(row, "margin")[agent_a_id]) for row in pair_rows
                ),
            }
        )
    return {
        "agents": agents,
        "pairwise": pairwise,
        "throughput": {
            "worker_isolation": "fresh spawned process per complete match",
            "workers": workers,
            "elapsed_seconds": elapsed_seconds,
            "games": len(rows),
            "games_per_second": len(rows) / elapsed_seconds,
            "transitions_per_second": total_transitions / elapsed_seconds,
            "agent_calls_per_second": total_calls / elapsed_seconds,
        },
    }


def _resolved_environment(
    settings: OpponentBenchmarkSettings, repository_root: Path
) -> dict[str, object]:
    if settings.engine == "native":
        engine = load_backend(repository_root).engine(
            seed=settings.seeds[0], configuration=dict(settings.environment)
        )
        return cast(dict[str, object], dict(engine.configuration))
    make = import_module("kaggle_environments").make

    configuration = dict(settings.environment)
    configuration.update(
        {
            "seed": settings.seeds[0],
            "actTimeout": settings.act_timeout_seconds,
        }
    )
    environment = make("kaggriculture", configuration=configuration, debug=False)
    return cast(dict[str, object], dict(environment.configuration))


def run_benchmark(settings: OpponentBenchmarkSettings, repository_root: Path) -> dict[str, object]:
    """Run an immutable, paired-seat notebook panel and write compact evidence."""
    repository_root = repository_root.resolve()
    manifest_path = (
        settings.public_agent_manifest
        if settings.public_agent_manifest.is_absolute()
        else repository_root / settings.public_agent_manifest
    ).resolve()
    manifest = load_public_agent_manifest(manifest_path)
    available = manifest.by_id()
    missing = set(settings.agent_ids) - set(available)
    if missing:
        raise KeyError(f"benchmark agents are absent from the manifest: {sorted(missing)}")
    records = {agent_id: available[agent_id] for agent_id in settings.agent_ids}
    output_dir = (
        settings.output_dir
        if settings.output_dir.is_absolute()
        else repository_root / settings.output_dir
    ).resolve()
    output_dir.mkdir(parents=True, exist_ok=False)
    resolved_path = output_dir / "resolved-settings.json"
    resolved_path.write_text(
        json.dumps(settings.model_dump(mode="json"), indent=2, sort_keys=True),
        encoding="utf-8",
    )
    jobs = _match_jobs(settings, repository_root, records)
    rows: list[dict[str, object] | None] = [None] * len(jobs)
    started = time.perf_counter()
    context = multiprocessing.get_context("spawn")
    with ProcessPoolExecutor(
        max_workers=settings.workers,
        mp_context=context,
        max_tasks_per_child=1,
    ) as executor:
        futures: dict[Future[dict[str, object]], int] = {
            executor.submit(run_match_job, job): index for index, job in enumerate(jobs)
        }
        progress_interval = max(1, len(jobs) // 20)
        for completed, future in enumerate(as_completed(futures), start=1):
            rows[futures[future]] = future.result()
            if completed % progress_interval == 0 or completed == len(jobs):
                print(f"completed {completed}/{len(jobs)} matches", flush=True)
    elapsed_seconds = time.perf_counter() - started
    completed_rows = [row for row in rows if row is not None]
    if len(completed_rows) != len(jobs):
        raise RuntimeError("opponent benchmark lost completed match records")

    samples: dict[str, list[int]] = {agent_id: [] for agent_id in settings.agent_ids}
    public_rows: list[dict[str, Any]] = []
    sample_agent_indices: list[int] = []
    sample_values: list[int] = []
    agent_index = {agent_id: index for index, agent_id in enumerate(settings.agent_ids)}
    for raw_row in completed_rows:
        row = cast(dict[str, Any], raw_row)
        raw_samples = cast(dict[str, list[int]], row.pop("_timing_samples_ns"))
        for agent_id, values in raw_samples.items():
            samples[agent_id].extend(values)
            sample_agent_indices.extend([agent_index[agent_id]] * len(values))
            sample_values.extend(values)
        public_rows.append(row)

    games_path = output_dir / "match-games.json"
    games_path.write_text(json.dumps(public_rows, indent=2, sort_keys=True), encoding="utf-8")
    samples_path = output_dir / "action-timing-samples.npz"
    np.savez_compressed(
        samples_path,
        agent_ids=np.asarray(settings.agent_ids),
        agent_index=np.asarray(sample_agent_indices, dtype=np.int16),
        elapsed_ns=np.asarray(sample_values, dtype=np.int64),
    )
    summary = _summary(
        public_rows,
        settings.agent_ids,
        samples,
        elapsed_seconds,
        settings.workers,
    )
    report: dict[str, object] = {
        "schema_version": "public-opponent-benchmark-v1",
        "decision_surface": [
            "win",
            "loss",
            "tie",
            "terminal cash",
            "terminal cash difference",
        ],
        "source": source_identity(repository_root),
        "manifest": {
            "path": str(manifest_path),
            "sha256": _sha256(manifest_path),
            "agents": {
                agent_id: {
                    "notebook_ref": record.notebook_ref,
                    "notebook_id": record.notebook_id,
                    "artifact_sha256": record.sha256,
                }
                for agent_id, record in records.items()
            },
        },
        "engine": settings.engine,
        "resolved_environment": _resolved_environment(settings, repository_root),
        "act_timeout_seconds": settings.act_timeout_seconds,
        "remaining_overage_seconds": settings.remaining_overage_seconds,
        "paired_seats": True,
        "seeds": list(settings.seeds),
        "anchor_id": settings.anchor_id,
        **summary,
        "artifacts": {
            "resolved_settings": {
                "path": str(resolved_path),
                "sha256": _sha256(resolved_path),
            },
            "match_games": {
                "path": str(games_path),
                "sha256": _sha256(games_path),
                "games": len(public_rows),
            },
            "action_timing_samples": {
                "path": str(samples_path),
                "sha256": _sha256(samples_path),
                "samples": len(sample_values),
            },
        },
    }
    report_path = output_dir / "benchmark-report.json"
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    return report


__all__ = ["run_benchmark"]
