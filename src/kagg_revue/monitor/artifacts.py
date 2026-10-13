"""Read-only aggregation of immutable and in-progress experiment artifacts."""

from __future__ import annotations

import json
import time
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import cast

from kagg_revue.monitor import pretraining
from kagg_revue.monitor.config import MonitorSettings
from kagg_revue.monitor.curves import CurveQuery, CurveReader
from kagg_revue.monitor.evaluation import EvaluationHistoryReader
from kagg_revue.monitor.history import HistoryReader
from kagg_revue.monitor.learning import has_evaluation as learning_has_evaluation
from kagg_revue.monitor.learning import progress as learning_progress
from kagg_revue.monitor.metrics import (
    JsonlMetricReader,
    MetricSnapshot,
    TensorboardMetricReader,
    snapshot_payload,
)
from kagg_revue.monitor.opponents.query import OpponentQuery
from kagg_revue.monitor.opponents.query import payload as opponent_payload
from kagg_revue.monitor.search import live_progress

_REPORT_NAMES = (
    "training-report.json",
    "evaluation-report.json",
    "report.json",
    "resolved-settings.json",
    "resolved-config.json",
    "run-status.json",
    "learning-progress.json",
    "league-progress.json",
)
_RESOLVED_CONFIG_NAMES = ("resolved-settings.json", "resolved-config.json")
_CONFIGURATION_KEYS = (
    "optimization_target",
    "value_target",
    "terminal_cash_scale",
    "device",
    "evaluation_device",
    "epochs",
    "updates",
    "batch_size",
    "seeds_per_update",
    "rollout_batch_games",
    "rollout_cpu_workers",
    "rollout_actor_streams",
    "evaluation_opponents",
)
_RL_SECTION_NAMES = (
    "rl",
    "capability_rl",
    "structured_plan_rl",
    "unit_task_rl",
    "conditional_program_rl",
    "intent_ledger_rl",
    "route_ppo",
    "ppo",
)
_BC_SECTION_NAMES = ("experiment", "unit_task_bc", "conditional_program_bc", "bc")


def _read_json(path: Path) -> dict[str, object] | None:
    if not path.is_file() or path.stat().st_size > 20 * 1024 * 1024:
        return None
    try:
        value: object = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return None
    if not isinstance(value, dict):
        return None
    return cast(dict[str, object], value)


def _resolved_training(run_dir: Path) -> dict[str, object]:
    """Return the first resolved training config artifact for one run."""
    for name in _RESOLVED_CONFIG_NAMES:
        resolved = _read_json(run_dir / name)
        if resolved is not None:
            return resolved
    return {}


def _mapping(value: object) -> Mapping[str, object] | None:
    return cast(Mapping[str, object], value) if isinstance(value, Mapping) else None


def _resolved_section(
    resolved: Mapping[str, object],
    kind: str,
) -> tuple[str | None, Mapping[str, object]]:
    """Return the first recognized training section and its schema name."""
    if kind == "rl" and "games_per_pair" in resolved:
        section = _mapping(resolved.get("experiment"))
        if section is not None:
            return "experiment", section
    names = _RL_SECTION_NAMES if kind == "rl" else _BC_SECTION_NAMES
    for name in names:
        section = _mapping(resolved.get(name))
        if section is not None:
            return name, section
    target_name = "updates" if kind == "rl" else "epochs"
    if _integer(resolved.get(target_name)) is not None:
        return None, resolved
    return None, {}


def _numeric(value: object) -> float | None:
    if isinstance(value, int | float) and not isinstance(value, bool):
        return float(value)
    return None


def _integer(value: object) -> int | None:
    numeric = _numeric(value)
    return int(numeric) if numeric is not None else None


def _iso(timestamp: float | None) -> str | None:
    if timestamp is None:
        return None
    return datetime.fromtimestamp(timestamp, tz=UTC).isoformat()


def _event_files(run_dir: Path) -> list[Path]:
    tensorboard = run_dir / "tensorboard"
    if not tensorboard.is_dir():
        return []
    return sorted(tensorboard.glob("events.out.tfevents.*"))


def _run_modified(run_dir: Path) -> float:
    candidates = [
        run_dir / "metrics.jsonl",
        run_dir / "selection-metrics.jsonl",
        run_dir / "pretraining/metrics.jsonl",
        run_dir / "pretraining/progress.json",
        *(run_dir / name for name in _REPORT_NAMES),
        *_event_files(run_dir),
        *(run_dir / "progress").glob("rank-*.json"),
        *(run_dir / member / "learning-progress.json" for member in ("a", "bc", "spataro")),
    ]
    modified = [path.stat().st_mtime for path in candidates if path.is_file()]
    return max(modified, default=run_dir.stat().st_mtime)


def _has_monitoring_artifact(run_dir: Path) -> bool:
    return any((run_dir / name).is_file() for name in _REPORT_NAMES) or (
        (run_dir / "metrics.jsonl").is_file() or bool(_event_files(run_dir))
    )


def _kind(run_dir: Path, snapshot: MetricSnapshot) -> str:
    if run_dir.parent.name == "learning":
        return "bc" if pretraining.is_bc_run(run_dir) else "rl"
    if any(tag.startswith("search/") for tag in snapshot.latest):
        return "search"
    if any(tag.startswith("rl/") for tag in snapshot.latest):
        return "rl"
    if any(tag.startswith("bc/") for tag in snapshot.latest):
        return "bc"
    if run_dir.parent.name == "terminal-wdl":
        return "rl"
    if run_dir.parent.name == "capability-rl":
        return "rl"
    if run_dir.parent.name in {
        "unit-task-rl",
        "conditional-program-rl",
        "structured-plan-rl",
        "route-ppo",
        "intent-ledger-rl",
        "production-policy",
    }:
        return "rl"
    if run_dir.parent.name in {"unit-task-bc", "conditional-program-bc"}:
        return "bc"
    if run_dir.parent.name == "turn-policy":
        return "bc"
    training = _read_json(run_dir / "training-report.json") or {}
    schema = str(training.get("schema_version", ""))
    if "terminal-wdl" in schema:
        return "rl"
    if "turn-policy" in schema:
        return "bc"
    return "other"


def _target(run_dir: Path, kind: str) -> int | None:
    resolved = _resolved_training(run_dir)
    if kind == "bc" and resolved.get("pretraining_only"):
        return _integer((_mapping(resolved.get("demonstrations")) or {}).get("epochs"))
    if "root_groups" in resolved and "continuation" in resolved:
        return _integer(resolved.get("updates"))
    if kind == "search":
        return _integer(resolved.get("generations"))
    if kind == "rl":
        if "teacher" in resolved and "learner_steps" in resolved:
            return _integer(resolved.get("generations"))
        _section_name, section = _resolved_section(resolved, kind)
        target = _integer(section.get("updates"))
        if target is not None:
            return target
    if kind == "bc":
        _section_name, section = _resolved_section(resolved, kind)
        target = _integer(section.get("epochs"))
        if target is None:
            optimization = _mapping(section.get("optimization"))
            target = _integer(optimization.get("epochs")) if optimization is not None else None
        if target is not None:
            return target

    training = _read_json(run_dir / "training-report.json") or {}
    if kind == "rl":
        updates = _mapping(training.get("updates"))
        return _integer(updates.get("target")) if updates is not None else None
    span = _mapping(training.get("training_span"))
    if span is not None:
        target = _integer(span.get("target_epoch"))
        if target is not None:
            return target
    return _integer(training.get("best_epoch"))


def _reported_step(run_dir: Path, kind: str, target: int | None) -> int | None:
    if run_dir.parent.name == "learning":
        if kind == "bc":
            records = (_read_json(run_dir / "pretraining/progress.json") or {}).get("records", [])
            return len(records) if isinstance(records, list) else 0
        live = learning_progress(run_dir)
        status = _read_json(run_dir / "run-status.json") or {}
        return _integer(live.get("update", status.get("completed_update", 0)))
    training = _read_json(run_dir / "training-report.json")
    if training is None:
        return None
    if kind == "rl":
        updates = _mapping(training.get("updates"))
        if updates is not None:
            last = _mapping(updates.get("last"))
            last_update = _integer(last.get("update")) if last is not None else None
            if last_update is not None:
                return last_update
            completed = _integer(updates.get("completed"))
            start = _integer(updates.get("start_update"))
            if completed is not None and start is not None and completed > 0:
                return start + completed - 1
        completed_update = _integer(training.get("completed_update"))
        if completed_update is not None:
            return completed_update
        return target
    span = _mapping(training.get("training_span"))
    completed_target = _integer(span.get("target_epoch")) if span is not None else None
    return completed_target or _integer(training.get("best_epoch")) or target


def _duration_metric(snapshot: MetricSnapshot, kind: str) -> tuple[str, str]:
    if kind == "search":
        return "search/timing/generation_seconds", "generation"
    if kind == "rl":
        return "rl/system/update_elapsed_seconds", "update"
    return "bc/system/elapsed_seconds", "epoch"


def _mean_step_seconds(snapshot: MetricSnapshot, kind: str) -> float | None:
    """Return a per-step duration from direct or cumulative timing metrics."""
    duration_tag, _unit = _duration_metric(snapshot, kind)
    durations = [point.value for point in snapshot.series.get(duration_tag, ())[-10:]]
    if kind == "bc" and snapshot.series.get("bc/system/epoch_seconds"):
        durations = [point.value for point in snapshot.series["bc/system/epoch_seconds"][-10:]]
    if durations:
        return sum(durations) / len(durations)
    if kind != "rl":
        return None

    cumulative = snapshot.series.get("rl/system/elapsed_seconds", ())[-11:]
    derived = [
        (current.value - previous.value) / (current.step - previous.step)
        for previous, current in zip(cumulative, cumulative[1:], strict=False)
        if current.step > previous.step and current.value >= previous.value
    ]
    if derived:
        return sum(derived) / len(derived)
    rollout = [point.value for point in snapshot.series.get("rl/rollout/elapsed_seconds", ())[-10:]]
    return sum(rollout) / len(rollout) if rollout else None


def _progress(
    snapshot: MetricSnapshot,
    target: int | None,
    kind: str,
    reported_step: int | None,
) -> dict[str, object]:
    current = snapshot.last_step if snapshot.last_step is not None else reported_step
    percent = None
    if current is not None and target is not None and target > 0:
        percent = min(100.0, max(0.0, 100.0 * current / target))
    _duration_tag, unit = _duration_metric(snapshot, kind)
    mean_duration = _mean_step_seconds(snapshot, kind)
    eta = None
    if current is not None and target is not None and mean_duration is not None:
        eta = max(0.0, target - current) * mean_duration
    return {
        "current": current,
        "target": target,
        "percent": percent,
        "unit": unit,
        "mean_step_seconds": mean_duration,
        "eta_seconds": eta,
    }


def _headline(snapshot: MetricSnapshot, kind: str) -> dict[str, float | None]:
    latest = snapshot.latest
    if kind == "search":
        return {
            "accepted": latest.get("search/counts/accepted"),
            "accepted_total": latest.get("search/counts/accepted_total"),
            "games_per_second": latest.get("search/timing/physical_games_per_second"),
        }
    if kind == "rl":
        wins = latest.get("rl/rollout/wins")
        ties = latest.get("rl/rollout/ties")
        losses = latest.get("rl/rollout/losses")
        games = sum(value or 0.0 for value in (wins, ties, losses))
        return {
            "wins": wins,
            "ties": ties,
            "losses": losses,
            "win_rate": None if games <= 0 else (wins or 0.0) / games,
            "mean_cash_difference": latest.get("rl/rollout/mean_cash_difference"),
            "mean_terminal_cash": latest.get("rl/rollout/mean_terminal_cash"),
            "turns_per_second": latest.get("rl/rollout/turns_per_second"),
            "games_per_second": latest.get("rl/rollout/games_per_second"),
            "total_loss": latest.get("rl/optimization/total_loss"),
        }
    return {
        "validation_objective_nll": latest.get(
            "bc/validation/causal_objective_nll",
            latest.get("bc/validation/objective_nll", latest.get("bc/validation/action_nll")),
        ),
        "validation_action_accuracy": latest.get("bc/validation/action_accuracy"),
        "validation_quantity_accuracy": latest.get("bc/validation/quantity_accuracy"),
        "turns_per_second": latest.get("bc/training/turns_per_second"),
        "training_objective_nll": latest.get(
            "bc/training/causal_objective_nll",
            latest.get("bc/training/objective_nll", latest.get("bc/training/action_nll")),
        ),
    }


def _status(
    run_dir: Path,
    run_id: str,
    active_run_ids: set[str],
    modified: float,
    stale_after_seconds: int,
) -> str:
    if run_id in active_run_ids:
        return "running"
    run_status = _read_json(run_dir / "run-status.json") or {}
    if run_status.get("status") in {"failed", "stopped"}:
        return str(run_status["status"])
    if run_status.get("status") == "complete":
        return "trained"
    if run_status.get("status") == "running" and time.time() - modified <= stale_after_seconds:
        return "running"
    if (run_dir / "evaluation-report.json").is_file():
        return "evaluated"
    if (run_dir / "training-report.json").is_file():
        return "trained"
    if time.time() - modified <= stale_after_seconds:
        return "recent"
    return "stopped"


def _wdl_rows(report: Mapping[str, object]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []

    def visit(path: tuple[str, ...], value: Mapping[str, object]) -> None:
        if all(name in value for name in ("wins", "ties", "losses")):
            row: dict[str, object] = {
                "path": list(path),
                "label": " · ".join(path),
                "wins": _integer(value.get("wins")),
                "ties": _integer(value.get("ties")),
                "losses": _integer(value.get("losses")),
            }
            for name in (
                "games",
                "mean_terminal_cash",
                "mean_cash_difference",
                "errors",
                "max_act_seconds",
            ):
                if name in value:
                    row[name] = value[name]
            rows.append(row)
        for name, child in value.items():
            child_mapping = _mapping(child)
            if child_mapping is not None:
                visit((*path, str(name)), child_mapping)

    visit((), report)
    return rows[:100]


def _evaluation(run_dir: Path) -> dict[str, object] | None:
    evaluation = _read_json(run_dir / "evaluation-report.json")
    if evaluation is None:
        return None
    experiment = _read_json(run_dir / "report.json") or {}
    decision = evaluation.get("decision", experiment.get("decision"))
    return {
        "generated_at": evaluation.get("generated_at"),
        "decision_surface": evaluation.get("decision_surface"),
        "diagnostic_surface": evaluation.get("diagnostic_surface"),
        "decision": decision,
        "completion": evaluation.get("completion"),
        "execution": evaluation.get("execution"),
        "wdl_rows": _wdl_rows(evaluation),
    }


def _artifact_payload(path: Path, run_dir: Path, kind: str) -> dict[str, object]:
    stat = path.stat()
    return {
        "path": path.relative_to(run_dir).as_posix(),
        "kind": kind,
        "size_bytes": stat.st_size,
        "modified_at": _iso(stat.st_mtime),
    }


def _artifacts(run_dir: Path) -> dict[str, object]:
    files: list[dict[str, object]] = []
    for path in run_dir.iterdir():
        if not path.is_file():
            continue
        if path.name in _REPORT_NAMES or path.name == "metrics.jsonl":
            files.append(_artifact_payload(path, run_dir, "report"))
        elif path.suffix in {".pt", ".pth"}:
            files.append(_artifact_payload(path, run_dir, "model"))

    checkpoints_dir = run_dir / "checkpoints"
    checkpoint_paths: list[Path] = []
    if checkpoints_dir.is_dir():
        checkpoint_paths = sorted(
            (path for path in checkpoints_dir.iterdir() if path.is_file()),
            key=lambda path: path.stat().st_mtime,
            reverse=True,
        )
        files.extend(
            _artifact_payload(path, run_dir, "checkpoint") for path in checkpoint_paths[:8]
        )
    files.sort(key=lambda item: cast(str, item["modified_at"]), reverse=True)
    return {"files": files, "checkpoint_count": len(checkpoint_paths)}


def _source(run_dir: Path) -> dict[str, object] | None:
    production = _read_json(run_dir / "source.json")
    if production is not None and "revision" in production:
        return {
            "commit": production["revision"],
            "worktree_dirty": not production.get("clean", False),
            "source_tree_sha256": production.get("native_sha256"),
        }
    training = _read_json(run_dir / "training-report.json") or {}
    value = _mapping(training.get("source"))
    if value is None:
        resolved = _resolved_training(run_dir)
        value = _mapping(resolved.get("source"))
    if value is None:
        revision = training.get("source_revision")
        if revision is None:
            return None
        return {
            "commit": revision,
            "worktree_dirty": None,
            "source_tree_sha256": None,
        }
    return {
        "commit": value.get("commit"),
        "worktree_dirty": value.get("worktree_dirty"),
        "source_tree_sha256": value.get("source_tree_sha256"),
    }


def _configuration(run_dir: Path, kind: str) -> dict[str, object]:
    resolved = _resolved_training(run_dir)
    if kind == "bc" and resolved.get("pretraining_only"):
        bc_source = _mapping(resolved.get("demonstrations")) or {}
        return {
            "training_family": "compact_bc",
            "epochs": bc_source.get("epochs"),
            "learning_rate": bc_source.get("learning_rate"),
            "batch_size": bc_source.get("batch_rows"),
            "devices": (_mapping(resolved.get("execution")) or {}).get("devices"),
            **{
                key: resolved.get(key)
                for key in ("width", "depth", "heads", "precision", "memory_turns")
            },
        }
    if "root_groups" in resolved and "continuation" in resolved:
        return {
            "training_family": "state_branch",
            "execution": "argmax",
            **{
                name: resolved[name]
                for name in (
                    "updates",
                    "candidates",
                    "pivots",
                    "continuation",
                    "learning_rate",
                    "learner_steps",
                    "evaluation_interval",
                )
            },
        }
    if "teacher" in resolved and "learner_steps" in resolved:
        return {
            "training_family": "expert_iteration",
            "execution": "argmax",
            **{
                name: resolved[name]
                for name in (
                    "generations",
                    "teacher",
                    "reference",
                    "learning_rate",
                    "learner_steps",
                    "temperature",
                    "search_interval",
                    "observations_per_trajectory",
                )
                if name in resolved
            },
        }
    if kind == "search":
        production = _mapping(resolved.get("production")) or {}
        return {
            "training_family": "policy_search",
            "execution": "argmax",
            **{
                name: resolved[name]
                for name in ("generations", "directions", "scales", "finalists", "reference")
                if name in resolved
            },
            **{
                name: production[name]
                for name in ("devices", "opponents", "evaluation_games")
                if name in production
            },
        }
    section_name, section = _resolved_section(resolved, kind)
    if section_name == "ppo":
        return {
            "training_family": "spatial-contract",
            **section,
            **{
                key: resolved[key]
                for key in ("devices", "workers", "decision_interval")
                if key in resolved
            },
        }
    configuration = {name: section[name] for name in _CONFIGURATION_KEYS if name in section}

    objective = _mapping(section.get("objective")) or {}
    rollout = _mapping(section.get("rollout")) or {}
    search = _mapping(section.get("search")) or {}
    model = _mapping(section.get("model")) or {}
    optimization = _mapping(section.get("optimization")) or {}
    execution = _mapping(section.get("execution")) or {}
    if execution:
        configuration.update(
            {
                "devices": execution.get("devices", []),
                "rollout_cpu_workers_per_rank": execution.get("workers_per_rank"),
                "learner_microbatch_rows": execution.get("microbatch_rows"),
                "compiled_inference": execution.get("compile_inference"),
            }
        )
    if section_name is not None or configuration or rollout or model or optimization:
        configuration = {
            "training_family": section_name or resolved.get("schema_version", "flat"),
            **configuration,
        }
    if isinstance(section.get("objective"), str):
        configuration["optimization_target"] = section["objective"]
    elif "reward" in objective:
        configuration["optimization_target"] = objective["reward"]
    for source, destination in (
        ("seeds_per_update", "seeds_per_update"),
        ("batch_games", "rollout_batch_games"),
        ("cpu_workers", "rollout_cpu_workers"),
        ("actor_streams_per_device", "rollout_actor_streams"),
        ("actor_streams", "rollout_actor_streams"),
    ):
        if source in rollout:
            configuration[destination] = rollout[source]
    for name in (
        "direct_capability",
        "updates",
        "devices",
        "device",
        "training_devices",
        "opponents",
        "opponent",
        "paired_seats",
        "act_timeout_seconds",
        "remaining_overage_seconds",
        "learning_rate",
        "unit_limit",
        "initial_weights",
    ):
        if name in section:
            configuration[name] = section[name]
        elif name in optimization:
            configuration[name] = optimization[name]
    for name in ("architecture_version", "model_width", "feedforward_width", "train_turn_encoder"):
        if name in model:
            configuration[name] = model[name]
    if "behavior_exploration_epsilon" in search:
        configuration["behavior_exploration_epsilon"] = search["behavior_exploration_epsilon"]
    return configuration


class RunRepository:
    """Discover and summarize run directories without mutating artifacts."""

    def __init__(
        self,
        repository_root: Path,
        settings: MonitorSettings,
    ) -> None:
        """Bind readers to a validated output directory."""
        self.repository_root = repository_root.resolve()
        outputs = settings.outputs_dir
        self.outputs_dir = (
            outputs.resolve()
            if outputs.is_absolute()
            else (self.repository_root / outputs).resolve()
        )
        if not self.outputs_dir.is_dir():
            raise FileNotFoundError(f"monitor output directory does not exist: {self.outputs_dir}")
        self._settings = settings
        self._jsonl = JsonlMetricReader(settings.max_points)
        self._tensorboard = TensorboardMetricReader(settings.max_points)
        self._evaluation_history = EvaluationHistoryReader()
        self._history = HistoryReader(settings.history_cache_runs)
        self._curves = CurveReader(settings, self._history)

    def opponents(self, run_id: str, query: OpponentQuery) -> dict[str, object]:
        """Query committed opponent outcomes and the independently dated live pool."""
        run_dir = self.resolve(run_id)
        with self._history.lock:
            history = self._history.read(run_dir / "metrics.jsonl")
            return opponent_payload(history, learning_progress(run_dir), query, self._settings)

    def curves(self, run_id: str, query: CurveQuery) -> dict[str, object]:
        """Return exact-range training trends for a validated run directory."""
        return self._curves.read(pretraining.metrics_path(self.resolve(run_id)), query)

    def run_directories(self) -> list[Path]:
        """Return supported two-level experiment directories."""
        runs: list[Path] = []
        for family in self.outputs_dir.iterdir():
            if not family.is_dir() or family.is_symlink():
                continue
            for run_dir in family.iterdir():
                if (
                    run_dir.is_dir()
                    and not run_dir.is_symlink()
                    and _has_monitoring_artifact(run_dir)
                ):
                    runs.append(run_dir)
        return runs

    def resolve(self, run_id: str) -> Path:
        """Resolve one exact family/run identifier beneath the output root."""
        relative = Path(run_id)
        if relative.is_absolute() or len(relative.parts) != 2:
            raise FileNotFoundError(run_id)
        candidate = (self.outputs_dir / relative).resolve()
        if not candidate.is_relative_to(self.outputs_dir) or not candidate.is_dir():
            raise FileNotFoundError(run_id)
        if candidate.is_symlink() or not _has_monitoring_artifact(candidate):
            raise FileNotFoundError(run_id)
        return candidate

    def list_runs(self, active_run_ids: set[str]) -> list[dict[str, object]]:
        """Summarize all monitored runs, placing active runs first."""
        summaries = [self._summary(path, active_run_ids) for path in self.run_directories()]
        return sorted(
            summaries,
            key=lambda row: (
                row["status"] == "running",
                cast(float, row["modified_timestamp"]),
            ),
            reverse=True,
        )

    def detail(
        self,
        run_id: str,
        active_run_ids: set[str],
        processes: Sequence[Mapping[str, object]],
        *,
        after_modified: float | None = None,
    ) -> dict[str, object]:
        """Return bounded curves, reports, and artifacts for one run."""
        run_dir = self.resolve(run_id)
        jsonl = self._jsonl.read(pretraining.metrics_path(run_dir))
        tensorboard: MetricSnapshot | None = None
        if jsonl.series:
            snapshot = jsonl
        else:
            tensorboard = self._tensorboard.read(run_dir / "tensorboard")
            snapshot = tensorboard
        summary = self._summary(run_dir, active_run_ids, snapshot=snapshot)
        matching_processes = [
            dict(process) for process in processes if process.get("run_id") == run_id
        ]
        history = self._evaluation_history.read(run_dir)
        modified = max(cast(float, summary["modified_timestamp"]), history["modified_timestamp"])
        summary["modified_timestamp"] = modified
        summary["modified_at"] = _iso(modified)
        if after_modified is not None and modified <= after_modified:
            return {
                "run": summary,
                "processes": matching_processes,
                "unchanged": True,
            }
        event_files = _event_files(run_dir)
        event_modified = max(
            (path.stat().st_mtime for path in event_files),
            default=None,
        )
        return {
            "run": summary,
            "metrics": snapshot_payload(snapshot),
            "evaluation": _evaluation(run_dir),
            "evaluation_history": history,
            "artifacts": _artifacts(run_dir),
            "source": _source(run_dir),
            "configuration": _configuration(run_dir, cast(str, summary["kind"])),
            "pretraining": pretraining.details(run_dir),
            "processes": matching_processes,
            "search_progress": live_progress(run_dir),
            "inputs": _read_json(run_dir / "inputs.json"),
            "tensorboard": {
                "available": bool(event_files),
                "event_file_count": len(event_files),
                "scalar_count": (None if tensorboard is None else len(tensorboard.series)),
                "last_event_at": _iso(
                    event_modified if tensorboard is None else tensorboard.last_modified
                ),
                "url": (
                    None
                    if self._settings.tensorboard_port is None
                    else f"http://127.0.0.1:{self._settings.tensorboard_port}"
                ),
            },
        }

    def _summary(
        self,
        run_dir: Path,
        active_run_ids: set[str],
        *,
        snapshot: MetricSnapshot | None = None,
    ) -> dict[str, object]:
        relative = run_dir.relative_to(self.outputs_dir)
        run_id = relative.as_posix()
        current_snapshot = snapshot or self._jsonl.read(pretraining.metrics_path(run_dir))
        run_kind = _kind(run_dir, current_snapshot)
        target = _target(run_dir, run_kind)
        reported_step = _reported_step(run_dir, run_kind, target)
        modified = max(_run_modified(run_dir), current_snapshot.last_modified or 0.0)
        return {
            "id": run_id,
            "learning": learning_progress(run_dir) if relative.parts[0] == "learning" else {},
            "family": relative.parts[0],
            "name": relative.parts[1],
            "kind": run_kind,
            "status": _status(
                run_dir,
                run_id,
                active_run_ids,
                modified,
                self._settings.stale_after_seconds,
            ),
            "modified_at": _iso(modified),
            "modified_timestamp": modified,
            "progress": _progress(current_snapshot, target, run_kind, reported_step),
            "headline": _headline(current_snapshot, run_kind),
            "has_tensorboard": bool(_event_files(run_dir)),
            "has_evaluation": (run_dir / "evaluation-report.json").is_file()
            or (relative.parts[0] == "learning" and learning_has_evaluation(run_dir)),
            "metric_sources": list(current_snapshot.sources),
        }


__all__ = ["RunRepository"]
