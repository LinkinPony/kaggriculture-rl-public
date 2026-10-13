"""Small-object aggregation for distributed structured-plan PPO."""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from kagg_revue.rl.plans.rollout import PlanGameResult, PlanRolloutResult


@dataclass(frozen=True)
class PlanRolloutSummary:
    """Tensor-free result transferred between synchronized CUDA ranks."""

    rank: int
    device: str
    games: tuple[PlanGameResult, ...]
    historical_opponent_id: str
    historical_opponent_update: int
    diagnostics: dict[str, object]


@dataclass(frozen=True)
class AggregatedPlanRollout:
    """Global complete-match surface and throughput diagnostics."""

    games: tuple[PlanGameResult, ...]
    historical_opponent_id: str
    historical_opponent_update: int
    diagnostics: dict[str, object]


def _metric(diagnostics: Mapping[str, object], name: str) -> float:
    value = diagnostics.get(name)
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise TypeError(f"structured-plan rollout metric is not numeric: {name}")
    return float(value)


def summarize_plan_rollout(
    result: PlanRolloutResult,
    *,
    rank: int,
    device: str,
) -> PlanRolloutSummary:
    """Drop large rollout tensors before the rank object collective."""
    return PlanRolloutSummary(
        rank=rank,
        device=device,
        games=result.games,
        historical_opponent_id=result.historical_opponent_id,
        historical_opponent_update=result.historical_opponent_update,
        diagnostics=result.diagnostics,
    )


def _consistent_integer(
    summaries: Sequence[PlanRolloutSummary],
    name: str,
) -> int:
    values = {int(_metric(summary.diagnostics, name)) for summary in summaries}
    if len(values) != 1:
        raise RuntimeError(f"structured-plan rollout ranks disagree on {name}")
    return values.pop()


def _event_counts(summaries: Sequence[PlanRolloutSummary]) -> dict[str, int]:
    counts: Counter[str] = Counter()
    for summary in summaries:
        raw = summary.diagnostics.get("event_source_counts")
        if not isinstance(raw, Mapping):
            raise TypeError("structured-plan event source diagnostics are invalid")
        for name, value in raw.items():
            if not isinstance(name, str) or not isinstance(value, int):
                raise TypeError("structured-plan event source diagnostics are invalid")
            counts[name] += value
    return dict(sorted(counts.items(), key=lambda item: int(item[0])))


def aggregate_plan_rollouts(
    summaries: Sequence[PlanRolloutSummary],
) -> AggregatedPlanRollout:
    """Combine disjoint rank panels without transferring observation tensors."""
    if not summaries:
        raise ValueError("structured-plan rollout rank summaries cannot be empty")
    ranks = {summary.rank for summary in summaries}
    if ranks != set(range(len(summaries))):
        raise RuntimeError("structured-plan rollout rank summaries are incomplete")
    ordered = tuple(sorted(summaries, key=lambda summary: summary.rank))
    historical_ids = {summary.historical_opponent_id for summary in ordered}
    historical_updates = {summary.historical_opponent_update for summary in ordered}
    if len(historical_ids) != 1 or len(historical_updates) != 1:
        raise RuntimeError("structured-plan rollout ranks selected different history")
    games = tuple(
        sorted(
            (game for summary in ordered for game in summary.games),
            key=lambda game: (game.seed, game.opponent_id, game.seat),
        )
    )
    if len({game.episode_id for game in games}) != len(games):
        raise RuntimeError("structured-plan rollout ranks reused a physical game")

    elapsed_values = [
        _metric(summary.diagnostics, "elapsed_seconds") for summary in ordered
    ]
    elapsed = max(elapsed_values)
    critical = elapsed_values.index(elapsed)
    critical_diagnostics = ordered[critical].diagnostics
    actor_decisions = sum(
        int(_metric(summary.diagnostics, "actor_decisions")) for summary in ordered
    )
    training_episodes = sum(
        int(_metric(summary.diagnostics, "training_episodes")) for summary in ordered
    )
    historical_decisions = sum(
        int(_metric(summary.diagnostics, "historical_opponent_decisions"))
        for summary in ordered
    )
    primitive_turns = sum(
        int(_metric(summary.diagnostics, "primitive_turns")) for summary in ordered
    )
    scheduler_rounds = sum(
        int(_metric(summary.diagnostics, "scheduler_rounds")) for summary in ordered
    )
    inference_calls = sum(
        int(_metric(summary.diagnostics, "inference_calls")) for summary in ordered
    )
    graph_metric_names = (
        "event_cuda_graph_captures",
        "event_cuda_graph_replays",
        "event_cuda_graph_eager_calls",
    )
    inference_rows = sum(
        _metric(summary.diagnostics, "mean_inference_batch")
        * _metric(summary.diagnostics, "inference_calls")
        for summary in ordered
    )
    ready_rows = sum(
        _metric(summary.diagnostics, "mean_ready_rows_per_round")
        * _metric(summary.diagnostics, "scheduler_rounds")
        for summary in ordered
    )
    training_outcomes = Counter[str]()
    for summary in ordered:
        raw_outcomes = summary.diagnostics.get("training_outcomes")
        if not isinstance(raw_outcomes, Mapping):
            raise TypeError("structured-plan training outcome diagnostics are invalid")
        for name in ("wins", "ties", "losses"):
            value = raw_outcomes.get(name)
            if not isinstance(value, int):
                raise TypeError("structured-plan training outcome diagnostics are invalid")
            training_outcomes[name] += value
    timing_names = (
        "event_scan_seconds",
        "rich_observation_seconds",
        "inference_seconds",
        "native_tick_seconds",
        "host_orchestration_seconds",
    )
    diagnostics: dict[str, object] = {
        "games": len(games),
        "training_episodes": training_episodes,
        "population": ordered[0].diagnostics["population"],
        "current_games": sum(
            int(_metric(summary.diagnostics, "current_games"))
            for summary in ordered
        ),
        "historical_games": sum(
            int(_metric(summary.diagnostics, "historical_games"))
            for summary in ordered
        ),
        "primitive_turns": primitive_turns,
        "actor_decisions": actor_decisions,
        "historical_opponent_decisions": historical_decisions,
        "inference_devices": [summary.device for summary in ordered],
        "distributed_rollout_ranks": len(ordered),
        "scheduler_rounds": scheduler_rounds,
        "scheduler_rounds_critical": int(
            _metric(critical_diagnostics, "scheduler_rounds")
        ),
        "inference_calls": inference_calls,
        **{
            name: sum(
                int(_metric(summary.diagnostics, name)) for summary in ordered
            )
            for name in graph_metric_names
        },
        "mean_ready_rows_per_round": ready_rows / max(scheduler_rounds, 1),
        "mean_inference_batch": inference_rows / max(inference_calls, 1),
        "day_history_advances": _consistent_integer(
            ordered,
            "day_history_advances",
        ),
        "historical_day_history_advances": _consistent_integer(
            ordered,
            "historical_day_history_advances",
        ),
        "actor_decisions_per_game": actor_decisions / len(games),
        "actor_decisions_per_training_episode": (
            actor_decisions / training_episodes
        ),
        "training_outcomes": dict(training_outcomes),
        "mean_plan_duration": sum(
            _metric(summary.diagnostics, "mean_plan_duration")
            * _metric(summary.diagnostics, "actor_decisions")
            for summary in ordered
        )
        / actor_decisions,
        "p95_plan_duration": max(
            _metric(summary.diagnostics, "p95_plan_duration")
            for summary in ordered
        ),
        "mean_patch_lines": sum(
            _metric(summary.diagnostics, "mean_patch_lines")
            * _metric(summary.diagnostics, "actor_decisions")
            for summary in ordered
        )
        / actor_decisions,
        "mean_active_lines": sum(
            _metric(summary.diagnostics, "mean_active_lines")
            * _metric(summary.diagnostics, "actor_decisions")
            for summary in ordered
        )
        / actor_decisions,
        "elapsed_seconds": elapsed,
        "games_per_second": len(games) / max(elapsed, 1e-9),
        "turns_per_second": primitive_turns / max(elapsed, 1e-9),
        "decisions_per_second": (
            (actor_decisions + historical_decisions) / max(elapsed, 1e-9)
        ),
        "training_decisions_per_second": actor_decisions / max(elapsed, 1e-9),
        "primitive_turns_per_second": primitive_turns / max(elapsed, 1e-9),
        "critical_rank": critical,
        "ranks": [
            {
                "rank": summary.rank,
                "device": summary.device,
                "games": len(summary.games),
                "actor_decisions": int(
                    _metric(summary.diagnostics, "actor_decisions")
                ),
                "elapsed_seconds": elapsed_values[summary.rank],
                "turns_per_second": _metric(
                    summary.diagnostics,
                    "turns_per_second",
                ),
                "mean_inference_batch": _metric(
                    summary.diagnostics,
                    "mean_inference_batch",
                ),
            }
            for summary in ordered
        ],
        "event_source_counts": _event_counts(ordered),
    }
    diagnostics.update(
        {name: _metric(critical_diagnostics, name) for name in timing_names}
    )
    return AggregatedPlanRollout(
        games=games,
        historical_opponent_id=historical_ids.pop(),
        historical_opponent_update=historical_updates.pop(),
        diagnostics=diagnostics,
    )


__all__ = [
    "AggregatedPlanRollout",
    "PlanRolloutSummary",
    "aggregate_plan_rollouts",
    "summarize_plan_rollout",
]
