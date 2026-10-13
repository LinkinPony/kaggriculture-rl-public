"""Complete-match screening for empirical replay-route proposals."""

from __future__ import annotations

import json
import statistics
import time
from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

import numpy as np

from kagg_revue.bc.actions import EncodedTurnAction, ReplayActionEncoder
from kagg_revue.bc.dataset import sha256_file
from kagg_revue.core.backend import BackendApi, load_backend
from kagg_revue.core.provenance import source_identity
from kagg_revue.opponents.native_batch import (
    create_native_opponent_session,
    step_native_opponent_batch,
)
from kagg_revue.proposals.config import ReplayRouteEvaluationSettings
from kagg_revue.proposals.replay import (
    ReplayRoute,
    discover_replay_routes,
    load_replay_route,
)


@dataclass(frozen=True)
class ReplayRouteGame:
    """One complete official-rule result for a fixed replay route."""

    route_id: str
    opponent_id: str
    seed: int
    seat: int
    outcome: int
    terminal_cash: float
    opponent_cash: float

    def record(self) -> dict[str, object]:
        """Return a stable JSON record."""
        return {
            "route_id": self.route_id,
            "opponent_id": self.opponent_id,
            "seed": self.seed,
            "seat": self.seat,
            "outcome": self.outcome,
            "terminal_cash": self.terminal_cash,
            "opponent_cash": self.opponent_cash,
        }


def _environment_integer(settings: ReplayRouteEvaluationSettings, name: str) -> int:
    value = settings.environment[name]
    if not isinstance(value, int) or isinstance(value, bool):
        raise TypeError(f"replay environment {name} must be an integer")
    return value


def _jobs(settings: ReplayRouteEvaluationSettings) -> tuple[tuple[int, int, str], ...]:
    return tuple(
        (seed, seat, opponent_id)
        for opponent_id in settings.opponents
        for seed in settings.seeds
        for seat in (0, 1)
    )


def _summary(games: Sequence[ReplayRouteGame]) -> dict[str, object]:
    if not games:
        raise ValueError("replay route summary needs completed games")

    def summarize(rows: Sequence[ReplayRouteGame]) -> dict[str, float | int]:
        return {
            "games": len(rows),
            "wins": sum(game.outcome > 0 for game in rows),
            "ties": sum(game.outcome == 0 for game in rows),
            "losses": sum(game.outcome < 0 for game in rows),
            "mean_terminal_cash": statistics.fmean(game.terminal_cash for game in rows),
            "mean_cash_difference": statistics.fmean(
                game.terminal_cash - game.opponent_cash for game in rows
            ),
        }

    return {
        "all": summarize(games),
        "opponents": {
            opponent_id: summarize(tuple(game for game in games if game.opponent_id == opponent_id))
            for opponent_id in sorted({game.opponent_id for game in games})
        },
    }


def _baseline_games(
    path: Path,
    settings: ReplayRouteEvaluationSettings,
) -> tuple[dict[tuple[str, int, int], Mapping[str, Any]], dict[str, int]]:
    report = cast(Mapping[str, Any], json.loads(path.read_text(encoding="utf-8")))
    panel = report.get("panel")
    if not isinstance(panel, Mapping):
        raise ValueError("baseline evaluation lacks a panel identity")
    if tuple(panel.get("opponents", ())) != settings.opponents:
        raise ValueError("baseline opponents differ from replay-route evaluation")
    if tuple(panel.get("seeds", ())) != settings.seeds or panel.get("paired_seats") is not True:
        raise ValueError("baseline seed/seat panel differs from replay-route evaluation")
    raw_games = report.get("games")
    if not isinstance(raw_games, list):
        raise ValueError("baseline evaluation lacks per-game outcomes")
    indexed: dict[tuple[str, int, int], Mapping[str, Any]] = {}
    for raw_game in raw_games:
        if not isinstance(raw_game, Mapping):
            raise ValueError("baseline game record is invalid")
        game = cast(Mapping[str, Any], raw_game)
        key = (str(game["opponent_id"]), int(game["seed"]), int(game["seat"]))
        if key in indexed:
            raise ValueError("baseline evaluation repeats a game identity")
        indexed[key] = game
    expected = {(opponent, seed, seat) for seed, seat, opponent in _jobs(settings)}
    if set(indexed) != expected:
        raise ValueError("baseline games do not exactly cover the replay-route panel")
    outcomes = [int(game["outcome"]) for game in indexed.values()]
    return indexed, {
        "games": len(outcomes),
        "wins": sum(outcome > 0 for outcome in outcomes),
        "ties": sum(outcome == 0 for outcome in outcomes),
        "losses": sum(outcome < 0 for outcome in outcomes),
    }


def _paired_baseline(
    games: Sequence[ReplayRouteGame],
    baseline: Mapping[tuple[str, int, int], Mapping[str, Any]],
) -> dict[str, int]:
    deltas = [
        game.outcome - int(baseline[(game.opponent_id, game.seed, game.seat)]["outcome"])
        for game in games
    ]
    return {
        "terminal_outcome_better": sum(delta > 0 for delta in deltas),
        "terminal_outcome_same": sum(delta == 0 for delta in deltas),
        "terminal_outcome_worse": sum(delta < 0 for delta in deltas),
    }


def _selection_gate(
    summary: Mapping[str, Any],
    baseline_summary: Mapping[str, int],
) -> dict[str, object]:
    overall = cast(Mapping[str, int], summary["all"])
    opponents = cast(Mapping[str, Mapping[str, int]], summary["opponents"])
    incumbent = opponents["kaito_v48"]
    population_noninferior = (
        overall["wins"] >= baseline_summary["wins"]
        and overall["losses"] <= baseline_summary["losses"]
    )
    incumbent_head_to_head_positive = incumbent["wins"] > incumbent["losses"]
    return {
        "population_wdl_noninferior": population_noninferior,
        "incumbent_head_to_head_positive": incumbent_head_to_head_positive,
        "passes": population_noninferior and incumbent_head_to_head_positive,
    }


def _evaluate_route(
    backend: BackendApi,
    route: ReplayRoute,
    settings: ReplayRouteEvaluationSettings,
) -> tuple[list[ReplayRouteGame], dict[str, object]]:
    jobs = _jobs(settings)
    engines = [
        backend.engine(seed=seed, configuration=settings.environment)
        for seed, _seat, _opponent in jobs
    ]
    candidate_players = np.asarray([seat for _seed, seat, _opponent in jobs], dtype=np.int64)
    opponent_ids = tuple(opponent for _seed, _seat, opponent in jobs)
    maximum_market_orders = _environment_integer(settings, "maxMarketOrdersPerTurn")
    opponent_sessions = [
        create_native_opponent_session(opponent_id, maximum_market_orders)
        for opponent_id in opponent_ids
    ]
    codec = ReplayActionEncoder(cast(Mapping[str, Any], backend.action_codec_spec()))
    width = route.maximum_possible_units + maximum_market_orders
    tokens = np.zeros((len(jobs), width), dtype=np.int64)
    quantities = np.zeros_like(tokens)
    decision_counts = np.zeros(len(jobs), dtype=np.int64)
    unit_counts = np.zeros(len(jobs), dtype=np.int64)
    repairs: Counter[str] = Counter()
    cache: dict[tuple[int, int], EncodedTurnAction] = {}
    done = np.zeros(len(jobs), dtype=np.bool_)
    primitive_turns = 0
    encoding_seconds = 0.0
    started = time.perf_counter()
    while not bool(done.all()):
        step = int(engines[0].step_index)
        if any(int(engine.step_index) != step for engine in engines):
            raise RuntimeError("replay-route lanes lost lockstep")
        if step >= len(route.actions):
            raise RuntimeError("replay route ended before the complete match")
        tokens.fill(0)
        quantities.fill(0)
        decision_counts.fill(0)
        unit_counts[:] = np.fromiter(
            (
                engine.policy_session(int(player), route.maximum_possible_units).unit_count
                for engine, player in zip(engines, candidate_players, strict=True)
            ),
            dtype=np.int64,
            count=len(jobs),
        )
        encoding_started = time.perf_counter()
        for unit_count in np.unique(unit_counts):
            key = (step, int(unit_count))
            encoded = cache.get(key)
            if encoded is None:
                encoded = codec.encode(
                    route.actions[step],
                    unit_count=int(unit_count),
                    max_market_orders=maximum_market_orders,
                )
                cache[key] = encoded
            count = len(encoded.tokens)
            if count > width:
                raise RuntimeError("replay route exceeded its proven action-width bound")
            rows = np.flatnonzero(unit_counts == unit_count)
            tokens[rows, :count] = encoded.tokens
            quantities[rows, :count] = encoded.quantities
            decision_counts[rows] = count
            for name, repair_count in encoded.repairs.items():
                repairs[name] += int(rows.size) * repair_count
        encoding_seconds += time.perf_counter() - encoding_started
        done = step_native_opponent_batch(
            backend,
            engines,
            candidate_players,
            opponent_ids,
            opponent_sessions,
            tokens,
            quantities,
            decision_counts,
            unit_counts,
            settings.cpu_workers,
        )
        primitive_turns += len(jobs)

    games: list[ReplayRouteGame] = []
    for (seed, seat, opponent_id), engine in zip(jobs, engines, strict=True):
        terminal_cash = float(engine.money(seat))
        opponent_cash = float(engine.money(1 - seat))
        outcome = int(terminal_cash > opponent_cash) - int(terminal_cash < opponent_cash)
        games.append(
            ReplayRouteGame(
                route_id=route.reference.route_id,
                opponent_id=opponent_id,
                seed=seed,
                seat=seat,
                outcome=outcome,
                terminal_cash=terminal_cash,
                opponent_cash=opponent_cash,
            )
        )
    elapsed = time.perf_counter() - started
    diagnostics: dict[str, object] = {
        "elapsed_seconds": elapsed,
        "primitive_turns": primitive_turns,
        "turns_per_second": primitive_turns / elapsed,
        "action_encoding_seconds": encoding_seconds,
        "encoded_action_cache_entries": len(cache),
        "action_repairs": dict(sorted(repairs.items())),
    }
    return games, diagnostics


def evaluate_replay_routes(
    settings: ReplayRouteEvaluationSettings,
    repository_root: Path,
) -> dict[str, object]:
    """Evaluate structurally selected routes on common seeds and paired seats."""
    root = repository_root.resolve()
    output_dir = (root / settings.output_dir).resolve()
    if output_dir.exists():
        raise FileExistsError(f"replay-route output already exists: {output_dir}")
    manifest_path = (root / settings.source_manifest).resolve()
    baseline_path = (root / settings.baseline_report).resolve()
    if not manifest_path.is_file() or not baseline_path.is_file():
        raise FileNotFoundError("replay-route manifest or baseline report is missing")
    source = source_identity(root)
    if source["worktree_dirty"]:
        raise RuntimeError("formal replay-route evaluation requires a clean worktree")

    backend = load_backend(root)
    engine = backend.engine(seed=settings.seed_start, configuration=settings.environment)
    resolved_environment = cast(dict[str, object], dict(engine.configuration))
    maximum_market_orders = _environment_integer(settings, "maxMarketOrdersPerTurn")
    episode_steps = _environment_integer(settings, "episodeSteps")
    codec = ReplayActionEncoder(cast(Mapping[str, Any], backend.action_codec_spec()))
    references, selection = discover_replay_routes(
        root,
        manifest_path,
        settings.source_agent_name,
        settings.prefix_turns,
        settings.route_ids,
        episode_steps,
        maximum_market_orders,
        codec,
    )
    baseline_games, baseline_summary = _baseline_games(baseline_path, settings)

    all_games: list[ReplayRouteGame] = []
    route_reports: list[dict[str, object]] = []
    started = time.perf_counter()
    for index, reference in enumerate(references, start=1):
        route = load_replay_route(reference, episode_steps, maximum_market_orders)
        games, diagnostics = _evaluate_route(backend, route, settings)
        all_games.extend(games)
        outcomes = _summary(games)
        route_report: dict[str, object] = {
            "route": {
                "route_id": reference.route_id,
                "episode_id": reference.episode_id,
                "source_seat": reference.seat,
                "source_path": str(reference.source_path.relative_to(root)),
                "source_sha256": reference.source_sha256,
                "prefix_sha256": reference.prefix_sha256,
                "prefix_cluster_size": reference.cluster_size,
                "action_sha256": route.action_sha256,
                "turns": len(route.actions),
                "hire_requests": route.hire_requests,
                "source_maximum_units": route.source_maximum_units,
                "maximum_possible_units": route.maximum_possible_units,
            },
            "outcomes": outcomes,
            "paired_baseline": _paired_baseline(games, baseline_games),
            "selection_gate": _selection_gate(outcomes, baseline_summary),
            "execution": diagnostics,
        }
        route_reports.append(route_report)
        print(
            json.dumps(
                {
                    "completed_routes": index,
                    "total_routes": len(references),
                    "route_id": reference.route_id,
                    "outcomes": outcomes["all"],
                    "selection_gate": route_report["selection_gate"],
                },
                sort_keys=True,
            ),
            flush=True,
        )

    output_dir.mkdir(parents=True)
    resolved_path = output_dir / "resolved-settings.json"
    resolved_path.write_text(
        json.dumps(settings.model_dump(mode="json"), indent=2, sort_keys=True),
        encoding="utf-8",
    )
    games_path = output_dir / "route-games.json"
    games_path.write_text(
        json.dumps([game.record() for game in all_games], indent=2, sort_keys=True),
        encoding="utf-8",
    )
    native_identity = cast(Mapping[str, object], backend.identity["native_module"])
    report: dict[str, object] = {
        "schema_version": "empirical-replay-route-complete-match-evaluation-v1",
        "proposal_role": "noncausal empirical proposal; never an oracle or value target",
        "decision_surface": "complete official-rule terminal W/D/L",
        "cash_role": "terminal diagnostic only",
        "source": source,
        "source_manifest": {
            "path": str(manifest_path),
            "sha256": sha256_file(manifest_path),
        },
        "selection": selection,
        "panel": {
            "opponents": list(settings.opponents),
            "seeds": list(settings.seeds),
            "paired_seats": True,
            "games_per_route": len(_jobs(settings)),
        },
        "baseline": {
            "path": str(baseline_path),
            "sha256": sha256_file(baseline_path),
            "outcomes": baseline_summary,
        },
        "selection_rule": {
            "population": "wins >= baseline wins and losses <= baseline losses",
            "incumbent": "wins > losses in direct matches against kaito_v48",
            "requires_both": True,
        },
        "routes": route_reports,
        "execution": {
            "elapsed_seconds": time.perf_counter() - started,
            "cpu_workers": settings.cpu_workers,
            "resolved_environment": resolved_environment,
            "native_extension": native_identity,
            "act_timeout_seconds": settings.act_timeout_seconds,
            "remaining_overage_seconds": settings.remaining_overage_seconds,
            "official_timeout_gate": False,
        },
        "artifacts": {
            "resolved_settings": {
                "path": str(resolved_path),
                "sha256": sha256_file(resolved_path),
            },
            "route_games": {
                "path": str(games_path),
                "sha256": sha256_file(games_path),
                "games": len(all_games),
            },
        },
        "promotion_authority": False,
    }
    report_path = output_dir / "evaluation-report.json"
    report_path.write_text(
        json.dumps(report, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return report


__all__ = ["ReplayRouteGame", "evaluate_replay_routes"]
