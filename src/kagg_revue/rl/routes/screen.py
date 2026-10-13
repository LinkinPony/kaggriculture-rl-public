"""Complete-match complementarity screen for synchronized Kaito routes."""

from __future__ import annotations

import json
import statistics
import subprocess
import time
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any, cast

import numpy as np
from numpy.typing import NDArray

from kagg_revue.core.backend import BackendApi, load_backend
from kagg_revue.core.provenance import source_identity
from kagg_revue.opponents.kaito.native import create_native_session as kaito_session
from kagg_revue.opponents.kaito.routes import ROUTE_NAMES
from kagg_revue.opponents.native_batch import (
    create_native_opponent_session,
    step_native_opponent_batch,
)
from kagg_revue.rl.capabilities.direct_control import collect_paired_direct_control
from kagg_revue.rl.routes.config import RoutePpoSettings
from kagg_revue.rl.routes.rollout import RouteJob
from kagg_revue.rl.routes.screen_config import RouteScreenSettings
from kagg_revue.rl.routes.train import _artifact_identities, _resolve


def _revision(root: Path) -> str:
    return subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def _jobs(settings: RoutePpoSettings) -> tuple[RouteJob, ...]:
    seeds = range(
        settings.selection_seed_start,
        settings.selection_seed_start + settings.evaluation_seed_count,
    )
    return tuple(
        (seed, seat, opponent)
        for opponent in settings.opponents
        for seed in seeds
        for seat in (0, 1)
    )


def _summary(games: Sequence[Mapping[str, Any]]) -> dict[str, object]:
    def rows_summary(rows: Sequence[Mapping[str, Any]]) -> dict[str, float | int]:
        outcomes = [int(game["outcome"]) for game in rows]
        return {
            "games": len(rows),
            "wins": sum(value > 0 for value in outcomes),
            "ties": sum(value == 0 for value in outcomes),
            "losses": sum(value < 0 for value in outcomes),
            "mean_terminal_cash": statistics.fmean(
                float(game["terminal_cash"]) for game in rows
            ),
            "mean_cash_difference": statistics.fmean(
                float(game["terminal_cash"]) - float(game["opponent_cash"])
                for game in rows
            ),
        }

    return {
        "all": rows_summary(games),
        "opponents": {
            opponent: rows_summary(
                tuple(game for game in games if game["opponent_id"] == opponent)
            )
            for opponent in sorted({str(game["opponent_id"]) for game in games})
        },
    }


def _game_outcome(game: Mapping[str, object]) -> int:
    value = game["outcome"]
    if not isinstance(value, int) or isinstance(value, bool):
        raise TypeError("route screen game outcome must be an integer")
    return value


def _evaluate_route(
    backend: BackendApi,
    settings: RoutePpoSettings,
    jobs: Sequence[RouteJob],
    route_index: int,
) -> tuple[list[dict[str, object]], dict[str, float | int]]:
    engines = [
        backend.engine(seed=seed, configuration=settings.environment)
        for seed, _seat, _opponent in jobs
    ]
    players = np.asarray([seat for _seed, seat, _opponent in jobs], dtype=np.int64)
    opponent_ids = tuple(opponent for _seed, _seat, opponent in jobs)
    market_orders = settings.environment["maxMarketOrdersPerTurn"]
    if not isinstance(market_orders, int) or isinstance(market_orders, bool):
        raise TypeError("route screen market order capacity must be an integer")
    sessions = [kaito_session(market_orders) for _ in jobs]
    opponent_sessions = [
        create_native_opponent_session(opponent, market_orders) for opponent in opponent_ids
    ]
    routes = np.full(len(jobs), route_index, dtype=np.int64)
    width = market_orders + settings.rollout.unit_limit
    tokens = np.zeros((len(jobs), width), dtype=np.int64)
    quantities = np.zeros_like(tokens)
    decision_counts = np.zeros(len(jobs), dtype=np.int64)
    unit_counts = np.zeros(len(jobs), dtype=np.int64)
    done: NDArray[np.bool_] = np.zeros(len(jobs), dtype=np.bool_)
    primitive_turns = 0
    started = time.perf_counter()
    while not bool(done.all()):
        backend.kaito_v48_route_action_numeric_batch(
            engines,
            players,
            sessions,
            routes,
            tokens,
            quantities,
            decision_counts,
            unit_counts,
            min(settings.rollout.cpu_workers, len(jobs)),
        )
        done = step_native_opponent_batch(
            backend,
            engines,
            players,
            opponent_ids,
            opponent_sessions,
            tokens,
            quantities,
            decision_counts,
            unit_counts,
            settings.rollout.cpu_workers,
        )
        primitive_turns += len(jobs)
    games: list[dict[str, object]] = []
    for (seed, seat, opponent), engine in zip(jobs, engines, strict=True):
        terminal_cash = float(engine.money(seat))
        opponent_cash = float(engine.money(1 - seat))
        outcome = int(terminal_cash > opponent_cash) - int(terminal_cash < opponent_cash)
        games.append(
            {
                "route_index": route_index,
                "route_name": ROUTE_NAMES[route_index],
                "opponent_id": opponent,
                "seed": seed,
                "seat": seat,
                "outcome": outcome,
                "terminal_cash": terminal_cash,
                "opponent_cash": opponent_cash,
            }
        )
    elapsed = time.perf_counter() - started
    return games, {
        "elapsed_seconds": elapsed,
        "primitive_turns": primitive_turns,
        "turns_per_second": primitive_turns / elapsed,
    }


def screen_route_library(
    raw_training: RoutePpoSettings,
    raw_screen: RouteScreenSettings,
    repository_root: Path,
) -> dict[str, object]:
    """Measure route complementarity without granting the oracle policy authority."""
    root = repository_root.resolve()
    training = _resolve(raw_training, root)
    output_dir = (root / raw_screen.output_dir).resolve()
    if not output_dir.is_relative_to((root / "outputs").resolve()):
        raise ValueError("route screen output escaped outputs/")
    if output_dir.exists():
        raise FileExistsError(f"route screen output already exists: {output_dir}")
    source = cast(Mapping[str, object], source_identity(root))
    if bool(source["worktree_dirty"]):
        raise RuntimeError("formal route screen requires a clean worktree")
    backend = load_backend(root)
    artifacts = _artifact_identities(backend, training)
    jobs = _jobs(training)
    market_orders = training.environment["maxMarketOrdersPerTurn"]
    if not isinstance(market_orders, int) or isinstance(market_orders, bool):
        raise TypeError("route screen market order capacity must be an integer")
    direct = collect_paired_direct_control(
        backend,
        training.environment,
        jobs,
        maximum_market_orders=market_orders,
        cpu_workers=training.rollout.cpu_workers,
    )
    route_games: list[list[dict[str, object]]] = []
    route_reports: list[dict[str, object]] = []
    started = time.perf_counter()
    for route_index, route_name in enumerate(ROUTE_NAMES):
        games, execution = _evaluate_route(backend, training, jobs, route_index)
        route_games.append(games)
        deltas = [
            _game_outcome(game) - int(direct.outcomes[index])
            for index, game in enumerate(games)
        ]
        route_report = {
            "route_index": route_index,
            "route_name": route_name,
            "outcomes": _summary(games),
            "paired_direct": {
                "better": sum(value > 0 for value in deltas),
                "same": sum(value == 0 for value in deltas),
                "worse": sum(value < 0 for value in deltas),
            },
            "execution": execution,
        }
        route_reports.append(route_report)
        print(json.dumps(route_report, sort_keys=True), flush=True)

    oracle_better = 0
    oracle_same = 0
    oracle_worse = 0
    memberships = {route_name: 0 for route_name in ROUTE_NAMES}
    for game_index in range(len(jobs)):
        outcomes = [_game_outcome(games[game_index]) for games in route_games]
        best = max(outcomes)
        delta = best - int(direct.outcomes[game_index])
        oracle_better += delta > 0
        oracle_same += delta == 0
        oracle_worse += delta < 0
        for route_index, outcome in enumerate(outcomes):
            if outcome == best:
                memberships[ROUTE_NAMES[route_index]] += 1

    output_dir.mkdir(parents=True)
    report: dict[str, object] = {
        "schema_version": "kaito-route-library-complete-match-screen-v1",
        "role": (
            "candidate-language complementarity diagnostic only; the per-game oracle "
            "has no deployment or promotion authority"
        ),
        "decision_surface": "complete official-rule terminal W/D/L",
        "cash_role": "diagnostic only",
        "source": {"revision": _revision(root), **dict(source)},
        "artifact_identities": artifacts,
        "panel": {
            "opponents": list(training.opponents),
            "seed_start": training.selection_seed_start,
            "seed_count": training.evaluation_seed_count,
            "paired_seats": True,
            "games_per_route": len(jobs),
        },
        "direct_control": {
            "wins": int(np.sum(direct.outcomes > 0)),
            "ties": int(np.sum(direct.outcomes == 0)),
            "losses": int(np.sum(direct.outcomes < 0)),
        },
        "routes": route_reports,
        "per_game_route_oracle_vs_direct": {
            "better": oracle_better,
            "same": oracle_same,
            "worse": oracle_worse,
            "best_route_membership": memberships,
        },
        "games": [game for games in route_games for game in games],
        "elapsed_seconds": time.perf_counter() - started,
    }
    report_path = output_dir / "evaluation-report.json"
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    (output_dir / "resolved-settings.json").write_text(
        json.dumps(
            {
                "route_ppo": training.model_dump(mode="json"),
                "screen": raw_screen.model_dump(mode="json"),
            },
            indent=2,
            sort_keys=True,
            default=str,
        ),
        encoding="utf-8",
    )
    return {
        "report": str(report_path),
        "routes": len(route_reports),
        "oracle": report["per_game_route_oracle_vs_direct"],
    }


__all__ = ["screen_route_library"]
