"""Incremental readers for JSONL and TensorBoard scalar metrics."""

from __future__ import annotations

import json
import math
import re
import threading
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, cast

from kagg_revue.core.observability import numeric_metrics
from kagg_revue.monitor.league import metrics as league_metrics
from kagg_revue.monitor.learning import metrics as learning_metrics
from kagg_revue.monitor.production import metrics as production_metrics
from kagg_revue.monitor.search import context as search_context
from kagg_revue.monitor.search import enrich as enrich_search
from kagg_revue.monitor.search import metrics as search_metrics

_OPPONENT_PREFIX = "rl/rollout/opponents/"
_HISTORY_OPPONENT = re.compile(r"^history:u(?P<update>[0-9]{8}):[0-9a-f]{64}$")


@dataclass(frozen=True)
class MetricPoint:
    """One scalar observation on a training step."""

    step: int
    value: float
    wall_time: float | None = None

    def payload(self) -> dict[str, int | float | None]:
        """Return a JSON-compatible point."""
        return {"step": self.step, "value": self.value, "wall_time": self.wall_time}


@dataclass(frozen=True)
class MetricSnapshot:
    """Bounded metric series plus the newest values."""

    series: dict[str, tuple[MetricPoint, ...]]
    latest: dict[str, float]
    last_step: int | None
    row_count: int
    last_modified: float | None
    sources: tuple[str, ...]
    context: dict[str, Any] = field(default_factory=dict)


@dataclass
class _JsonlCache:
    inode: int
    offset: int = 0
    row_count: int = 0
    last_step: int | None = None
    latest: dict[str, float] = field(default_factory=dict)
    series: dict[str, list[MetricPoint]] = field(default_factory=dict)
    context: dict[str, Any] = field(default_factory=dict)


def _step_and_metrics(row: Mapping[str, object]) -> tuple[int | None, dict[str, float]]:
    generation = row.get("generation")
    if isinstance(generation, int) and not isinstance(generation, bool):
        return generation, search_metrics(row)
    epoch = row.get("epoch")
    update = row.get("update")
    groups: tuple[str, ...]
    if isinstance(update, int | float) and not isinstance(update, bool):
        step = int(update)
        prefix = "rl"
        groups = (
            "rollout",
            "optimization",
            "system",
            "timing",
            "behavior_replay",
            "pfsp",
            "search",
            "batch",
            "land",
        )
    elif isinstance(epoch, int | float) and not isinstance(epoch, bool):
        step = int(epoch)
        prefix = "bc"
        groups = ("training", "validation", "system", "test")
    else:
        return None, {}

    flattened: dict[str, float] = {}
    for group in groups:
        values = row.get(group)
        if not isinstance(values, Mapping):
            continue
        for name, metric_value in numeric_metrics(cast(Mapping[str, object], values)).items():
            if math.isfinite(metric_value):
                flattened[f"{prefix}/{group}/{name}"] = metric_value
    for name in ("actor_update_requested", "actor_update_applied"):
        flag_value = row.get(name)
        if isinstance(flag_value, bool | int | float):
            flattened[f"{prefix}/run/{name}"] = float(flag_value)
    if prefix == "bc":
        timing = ("bc/system/training_seconds", "bc/system/validation_seconds")
        if all(tag in flattened for tag in timing):
            flattened["bc/system/epoch_seconds"] = sum(flattened[tag] for tag in timing)
    if prefix == "rl":
        flattened.update(_capability_outcome_metrics(row))
        flattened.update(_intent_outcome_metrics(row))
        flattened.update(_cuda_memory_metrics(row))
        flattened.update(production_metrics(row))
        flattened.update(learning_metrics(row))
        flattened.update(league_metrics(row))
        elapsed = row.get("elapsed_seconds")
        if isinstance(elapsed, int | float) and not isinstance(elapsed, bool):
            elapsed_value = float(elapsed)
            if math.isfinite(elapsed_value):
                flattened["rl/system/elapsed_seconds"] = elapsed_value

        aliases = {
            "rl/optimization/loss": "rl/optimization/total_loss",
            "rl/optimization/gradient_norm": "rl/optimization/maximum_gradient_norm",
            "rl/optimization/peak_gpu_allocated_bytes": "rl/system/cuda_peak_allocated_bytes",
            "rl/optimization/peak_gpu_reserved_bytes": "rl/system/cuda_peak_reserved_bytes",
            "rl/rollout/seconds": "rl/rollout/elapsed_seconds",
            "rl/rollout/physical_games_per_second": "rl/rollout/games_per_second",
            "rl/timing/update_seconds": "rl/system/update_elapsed_seconds",
            "rl/timing/optimization_seconds": "rl/system/optimization_seconds",
            "rl/timing/physical_games_per_second": "rl/rollout/games_per_second",
            "rl/behavior_replay/maximum_absolute_log_probability_error": (
                "rl/behavior_replay/log_probability_error"
            ),
            "rl/behavior_replay/maximum_absolute_value_error": "rl/behavior_replay/value_error",
        }
        for source, destination in aliases.items():
            if source in flattened and destination not in flattened:
                flattened[destination] = flattened[source]

        official_turns = flattened.get("rl/rollout/official_turns")
        rollout_elapsed = flattened.get("rl/rollout/elapsed_seconds")
        if (
            official_turns is not None
            and rollout_elapsed is not None
            and rollout_elapsed > 0.0
            and "rl/rollout/turns_per_second" not in flattened
        ):
            flattened["rl/rollout/turns_per_second"] = official_turns / rollout_elapsed

        physical_games = flattened.get("rl/rollout/physical_games")
        if physical_games is not None and "rl/rollout/games" not in flattened:
            flattened["rl/rollout/games"] = physical_games

        direct_fraction = flattened.get("rl/search/selected_direct_fraction")
        if direct_fraction is not None:
            flattened["rl/search/selected_capability_fraction"] = 1.0 - direct_fraction
        optimization_seconds = row.get("optimization_seconds")
        if isinstance(optimization_seconds, int | float) and not isinstance(
            optimization_seconds, bool
        ):
            seconds_value = float(optimization_seconds)
            if math.isfinite(seconds_value):
                flattened["rl/system/optimization_seconds"] = seconds_value
    return step, flattened


def _intent_outcome_metrics(row: Mapping[str, object]) -> dict[str, float]:
    """Normalize top-level RL outcome fields used by intent-ledger training."""
    if row.get("outcomes") is not None:
        return {}
    normalized: dict[str, float] = {}
    for name in ("wins", "ties", "losses", "mean_terminal_cash", "mean_cash_difference"):
        value = row.get(name)
        if isinstance(value, int | float) and not isinstance(value, bool):
            float_value = float(value)
            if math.isfinite(float_value):
                normalized[f"rl/rollout/{name}"] = float_value
    wins = normalized.get("rl/rollout/wins")
    ties = normalized.get("rl/rollout/ties")
    losses = normalized.get("rl/rollout/losses")
    games = sum(value or 0.0 for value in (wins, ties, losses))
    if games > 0.0:
        for count_name, rate_name in (
            ("wins", "win_rate"),
            ("ties", "tie_rate"),
            ("losses", "loss_rate"),
        ):
            count = normalized.get(f"rl/rollout/{count_name}")
            if count is not None:
                normalized[f"rl/rollout/{rate_name}"] = count / games
        normalized["rl/rollout/games"] = games
    return normalized


def _cuda_memory_metrics(row: Mapping[str, object]) -> dict[str, float]:
    """Aggregate per-device CUDA peaks into one dashboard tag."""
    cuda_memory = row.get("cuda_memory")
    if not isinstance(cuda_memory, Mapping):
        return {}
    peak_allocated = 0.0
    peak_reserved = 0.0
    for device_values in cuda_memory.values():
        if not isinstance(device_values, Mapping):
            continue
        allocated = device_values.get("peak_allocated_bytes")
        reserved = device_values.get("peak_reserved_bytes")
        if (
            isinstance(allocated, int | float)
            and not isinstance(allocated, bool)
            and math.isfinite(float(allocated))
        ):
            peak_allocated = max(peak_allocated, float(allocated))
        if (
            isinstance(reserved, int | float)
            and not isinstance(reserved, bool)
            and math.isfinite(float(reserved))
        ):
            peak_reserved = max(peak_reserved, float(reserved))
    normalized: dict[str, float] = {}
    if peak_allocated > 0.0:
        normalized["rl/system/cuda_peak_allocated_bytes"] = peak_allocated
    if peak_reserved > 0.0:
        normalized["rl/system/cuda_peak_reserved_bytes"] = peak_reserved
    return normalized


def _capability_outcome_metrics(row: Mapping[str, object]) -> dict[str, float]:
    """Normalize RL outcomes to bounded canonical dashboard tags."""
    outcomes_value = row.get("outcomes")
    if not isinstance(outcomes_value, Mapping):
        return {}
    outcomes = cast(Mapping[str, object], outcomes_value)
    flat_program_outcomes = all(name in outcomes for name in ("wins", "ties", "losses"))
    overall_value = outcomes.get("overall")
    overall = (
        outcomes
        if flat_program_outcomes
        else (
            cast(Mapping[str, object], overall_value) if isinstance(overall_value, Mapping) else {}
        )
    )
    normalized: dict[str, float] = {}

    def add_metrics(metric_prefix: str, values: Mapping[str, object]) -> None:
        for name, value in numeric_metrics(values).items():
            if math.isfinite(value):
                normalized[f"{metric_prefix}/{name}"] = value
        episodes = values.get("episodes")
        if (
            "games" not in values
            and isinstance(episodes, int | float)
            and not isinstance(episodes, bool)
            and math.isfinite(float(episodes))
        ):
            normalized[f"{metric_prefix}/games"] = float(episodes)

    add_metrics("rl/rollout", overall)
    bucketed_rows: dict[str, list[Mapping[str, object]]] = {}
    history_updates: dict[str, list[int]] = {}
    opponent_values = outcomes.get("opponents") if flat_program_outcomes else outcomes
    opponent_mapping = (
        cast(Mapping[str, object], opponent_values) if isinstance(opponent_values, Mapping) else {}
    )
    for opponent, value in opponent_mapping.items():
        if opponent == "overall" or not isinstance(value, Mapping):
            continue
        opponent_row = cast(Mapping[str, object], value)
        opponent_name = str(opponent)
        match = _HISTORY_OPPONENT.fullmatch(opponent_name)
        display_name = "history" if match is not None else opponent_name
        bucketed_rows.setdefault(display_name, []).append(opponent_row)
        if match is not None:
            history_updates.setdefault(display_name, []).append(int(match["update"]))

    def merge_rows(rows: list[Mapping[str, object]]) -> dict[str, object]:
        merged: dict[str, object] = dict(rows[0]) if len(rows) == 1 else {}
        if len(rows) > 1:
            for name in (
                "games",
                "training_episodes",
                "training_trajectories",
                "wins",
                "ties",
                "losses",
            ):
                values = [
                    float(value)
                    for row_values in rows
                    if isinstance((value := row_values.get(name)), int | float)
                    and not isinstance(value, bool)
                    and math.isfinite(float(value))
                ]
                if values:
                    merged[name] = sum(values)
            for name in ("mean_terminal_cash", "mean_cash_difference"):
                weighted_sum = 0.0
                weight = 0.0
                for row_values in rows:
                    games = row_values.get("games")
                    value = row_values.get(name)
                    if (
                        isinstance(games, int | float)
                        and not isinstance(games, bool)
                        and isinstance(value, int | float)
                        and not isinstance(value, bool)
                        and math.isfinite(float(games))
                        and math.isfinite(float(value))
                        and games > 0
                    ):
                        weighted_sum += float(games) * float(value)
                        weight += float(games)
                if weight > 0.0:
                    merged[name] = weighted_sum / weight
        games = merged.get("games")
        if isinstance(games, int | float) and not isinstance(games, bool) and games > 0.0:
            for count_name, rate_name in (
                ("wins", "win_rate"),
                ("ties", "tie_rate"),
                ("losses", "loss_rate"),
            ):
                count = merged.get(count_name)
                if isinstance(count, int | float) and not isinstance(count, bool):
                    merged[rate_name] = float(count) / float(games)
        return merged

    opponent_rows = [(opponent, merge_rows(rows)) for opponent, rows in bucketed_rows.items()]
    for opponent, opponent_row in opponent_rows:
        opponent_prefix = f"{_OPPONENT_PREFIX}{opponent}"
        add_metrics(opponent_prefix, opponent_row)
        updates = history_updates.get(opponent)
        if updates:
            normalized[f"{opponent_prefix}/opponent_update"] = float(max(updates))

    def training_count(values: Mapping[str, object]) -> float | None:
        for name in ("training_trajectories", "training_episodes", "games"):
            value = values.get(name)
            if (
                isinstance(value, int | float)
                and not isinstance(value, bool)
                and math.isfinite(float(value))
                and value >= 0
            ):
                return float(value)
        return None

    total_training = sum(
        count for _, values in opponent_rows if (count := training_count(values)) is not None
    )
    if total_training > 0.0:
        for opponent, values in opponent_rows:
            count = training_count(values)
            if count is None:
                continue
            opponent_prefix = f"{_OPPONENT_PREFIX}{opponent}"
            normalized.setdefault(
                f"{opponent_prefix}/training_fraction",
                count / total_training,
            )
            normalized.setdefault(
                f"{opponent_prefix}/training_trajectories",
                count,
            )

        for name in ("mean_terminal_cash", "mean_cash_difference"):
            weighted_sum = 0.0
            weight = 0.0
            for _, values in opponent_rows:
                games = values.get("games")
                metric = values.get(name)
                if (
                    isinstance(games, int | float)
                    and not isinstance(games, bool)
                    and isinstance(metric, int | float)
                    and not isinstance(metric, bool)
                    and math.isfinite(float(games))
                    and math.isfinite(float(metric))
                    and games > 0
                ):
                    weighted_sum += float(games) * float(metric)
                    weight += float(games)
            if weight > 0.0:
                normalized.setdefault(f"rl/rollout/{name}", weighted_sum / weight)

    games = normalized.get("rl/rollout/games")
    if games is not None and games > 0.0:
        for count_name, rate_name in (
            ("wins", "win_rate"),
            ("ties", "tie_rate"),
            ("losses", "loss_rate"),
        ):
            count = normalized.get(f"rl/rollout/{count_name}")
            if count is not None:
                normalized.setdefault(f"rl/rollout/{rate_name}", count / games)
    return normalized


def _bounded(points: list[MetricPoint], limit: int) -> tuple[MetricPoint, ...]:
    if len(points) <= limit:
        return tuple(points)
    if limit == 1:
        return (points[-1],)
    last = len(points) - 1
    indexes = {round(index * last / (limit - 1)) for index in range(limit)}
    return tuple(points[index] for index in sorted(indexes))


class JsonlMetricReader:
    """Tail append-only metric files without repeatedly materializing them."""

    def __init__(self, max_points: int) -> None:
        """Create a reader with bounded in-memory scalar histories."""
        self._max_points = max_points
        self._internal_limit = max_points * 2
        self._caches: dict[Path, _JsonlCache] = {}
        self._lock = threading.RLock()

    def read(self, path: Path) -> MetricSnapshot:
        """Read newly completed lines and return a stable snapshot."""
        if not path.is_file():
            return empty_snapshot()
        with self._lock:
            stat = path.stat()
            cache = self._caches.get(path)
            if cache is None or cache.inode != stat.st_ino or stat.st_size < cache.offset:
                cache = _JsonlCache(inode=stat.st_ino)
                self._caches[path] = cache
            self._read_new_lines(path, cache)
            return MetricSnapshot(
                series={
                    tag: _bounded(points, self._max_points) for tag, points in cache.series.items()
                },
                latest=dict(cache.latest),
                last_step=cache.last_step,
                row_count=cache.row_count,
                last_modified=stat.st_mtime,
                sources=("metrics.jsonl",),
                context=dict(cache.context),
            )

    def _read_new_lines(self, path: Path, cache: _JsonlCache) -> None:
        """Consume only newline-terminated records after the cached offset."""
        with path.open("rb") as stream:
            stream.seek(cache.offset)
            while True:
                line_start = stream.tell()
                line = stream.readline()
                if not line:
                    cache.offset = stream.tell()
                    break
                if not line.endswith(b"\n"):
                    cache.offset = line_start
                    break
                cache.offset = stream.tell()
                try:
                    value: object = json.loads(line)
                except (json.JSONDecodeError, UnicodeDecodeError):
                    continue
                if not isinstance(value, dict):
                    continue
                row = cast(dict[str, object], value)
                if isinstance(row.get("generation"), int):
                    row = enrich_search(path.parent, row)
                    cache.context = search_context(row)
                elif row.get("training_phase") in {"expert_iteration", "state_branch"}:
                    cache.context = {
                        **{
                            name: row.get(name)
                            for name in (
                                "update",
                                "expert",
                                "checkpoint",
                                "source_revision",
                                "learning",
                            )
                        },
                        "search": row.get("search") or cache.context.get("search"),
                    }
                    if row.get("training_phase") == "state_branch":
                        cache.context["branch_workers"] = [
                            {"rank": worker["rank"], "search": worker["search"]}
                            for worker in cast(list[dict[str, Any]], row.get("workers", []))
                        ]
                step, metrics = _step_and_metrics(row)
                if step is None:
                    continue
                if "search/counts/accepted" in metrics:
                    metrics["search/counts/accepted_total"] = (
                        cache.latest.get("search/counts/accepted_total", 0)
                        + metrics["search/counts/accepted"]
                    )
                previous_step = cache.last_step
                previous_elapsed = cache.latest.get("rl/system/elapsed_seconds")
                current_elapsed = metrics.get("rl/system/elapsed_seconds")
                if (
                    "rl/system/update_elapsed_seconds" not in metrics
                    and previous_step is not None
                    and previous_elapsed is not None
                    and current_elapsed is not None
                    and step > previous_step
                    and current_elapsed >= previous_elapsed
                ):
                    metrics["rl/system/update_elapsed_seconds"] = (
                        current_elapsed - previous_elapsed
                    ) / (step - previous_step)
                elif (
                    "rl/system/update_elapsed_seconds" not in metrics
                    and "rl/rollout/elapsed_seconds" in metrics
                    and "rl/system/optimization_seconds" in metrics
                ):
                    metrics["rl/system/update_elapsed_seconds"] = (
                        metrics["rl/rollout/elapsed_seconds"]
                        + metrics["rl/system/optimization_seconds"]
                    )
                cache.row_count += 1
                cache.last_step = step
                if "generation" in row:
                    for tag in tuple(cache.latest):
                        if tag.startswith("search/"):
                            del cache.latest[tag]
                if isinstance(row.get("outcomes"), Mapping) or isinstance(
                    row.get("populations"), Mapping
                ):
                    for tag in tuple(cache.latest):
                        if tag.startswith(_OPPONENT_PREFIX):
                            del cache.latest[tag]
                if "history_score" in row and row["history_score"] is None:
                    cache.latest.pop("rl/run/history_score", None)
                cache.latest.update(metrics)
                for tag, metric in metrics.items():
                    points = cache.series.setdefault(tag, [])
                    timestamp = row.get("timestamp")
                    points.append(
                        MetricPoint(
                            step=step,
                            value=metric,
                            wall_time=float(timestamp)
                            if isinstance(timestamp, int | float)
                            else None,
                        )
                    )
                    if len(points) > self._internal_limit:
                        points[:] = points[::2]


@dataclass
class _TensorboardCache:
    accumulator: Any
    signature: tuple[tuple[str, int, int], ...]


class TensorboardMetricReader:
    """Reload TensorBoard event accumulators only when event files change."""

    def __init__(self, max_points: int) -> None:
        """Create a scalar-only TensorBoard reader."""
        self._max_points = max_points
        self._caches: dict[Path, _TensorboardCache] = {}
        self._lock = threading.RLock()

    @staticmethod
    def _signature(directory: Path) -> tuple[tuple[str, int, int], ...]:
        events = sorted(directory.glob("events.out.tfevents.*"))
        return tuple((path.name, path.stat().st_size, path.stat().st_mtime_ns) for path in events)

    def read(self, directory: Path) -> MetricSnapshot:
        """Return scalar events from a TensorBoard log directory."""
        if not directory.is_dir():
            return empty_snapshot()
        signature = self._signature(directory)
        if not signature:
            return empty_snapshot()
        with self._lock:
            cache = self._caches.get(directory)
            if cache is None:
                from importlib import import_module

                event_module: Any = import_module(
                    "tensorboard.backend.event_processing.event_accumulator"
                )
                accumulator: Any = event_module.EventAccumulator(
                    str(directory), size_guidance={"scalars": self._max_points * 2}
                )
                accumulator.Reload()
                cache = _TensorboardCache(accumulator=accumulator, signature=signature)
                self._caches[directory] = cache
            elif cache.signature != signature:
                cache.accumulator.Reload()
                cache.signature = signature

            tags = cast(dict[str, list[str]], cache.accumulator.Tags())
            scalar_tags = tags.get("scalars", [])
            series: dict[str, tuple[MetricPoint, ...]] = {}
            latest: dict[str, float] = {}
            last_step: int | None = None
            last_wall_time: float | None = None
            for tag in scalar_tags:
                events: list[Any] = cache.accumulator.Scalars(tag)
                points = [
                    MetricPoint(
                        step=int(event.step),
                        value=float(event.value),
                        wall_time=float(event.wall_time),
                    )
                    for event in events
                    if math.isfinite(float(event.value))
                ]
                if not points:
                    continue
                series[tag] = _bounded(points, self._max_points)
                newest = points[-1]
                latest[tag] = newest.value
                last_step = newest.step if last_step is None else max(last_step, newest.step)
                last_wall_time = (
                    newest.wall_time
                    if last_wall_time is None
                    else max(last_wall_time, cast(float, newest.wall_time))
                )
            return MetricSnapshot(
                series=series,
                latest=latest,
                last_step=last_step,
                row_count=max((len(points) for points in series.values()), default=0),
                last_modified=last_wall_time,
                sources=("tensorboard",),
            )


def empty_snapshot() -> MetricSnapshot:
    """Return a metric snapshot with no observations."""
    return MetricSnapshot({}, {}, None, 0, None, ())


def merge_snapshots(
    primary: MetricSnapshot, secondary: MetricSnapshot, max_points: int
) -> MetricSnapshot:
    """Merge snapshots by tag and step while retaining primary values on overlap."""
    tags = primary.series.keys() | secondary.series.keys()
    series: dict[str, tuple[MetricPoint, ...]] = {}
    for tag in tags:
        by_step = {point.step: point for point in secondary.series.get(tag, ())}
        by_step.update({point.step: point for point in primary.series.get(tag, ())})
        series[tag] = _bounded(
            [by_step[step] for step in sorted(by_step)],
            max_points,
        )
    latest = dict(secondary.latest)
    latest.update(primary.latest)
    steps = [step for step in (primary.last_step, secondary.last_step) if step is not None]
    modified = [
        value for value in (primary.last_modified, secondary.last_modified) if value is not None
    ]
    return MetricSnapshot(
        series=series,
        latest=latest,
        last_step=max(steps) if steps else None,
        row_count=max(primary.row_count, secondary.row_count),
        last_modified=max(modified) if modified else None,
        sources=tuple(dict.fromkeys((*primary.sources, *secondary.sources))),
        context=primary.context or secondary.context,
    )


def snapshot_payload(snapshot: MetricSnapshot) -> dict[str, object]:
    """Serialize a bounded snapshot for the browser client."""
    return {
        "series": {
            tag: [point.payload() for point in points] for tag, points in snapshot.series.items()
        },
        "latest": snapshot.latest,
        "last_step": snapshot.last_step,
        "row_count": snapshot.row_count,
        "last_modified": snapshot.last_modified,
        "sources": list(snapshot.sources),
        "scalar_count": len(snapshot.series),
        "context": snapshot.context,
    }


__all__ = [
    "JsonlMetricReader",
    "MetricPoint",
    "MetricSnapshot",
    "TensorboardMetricReader",
    "empty_snapshot",
    "merge_snapshots",
    "snapshot_payload",
]
