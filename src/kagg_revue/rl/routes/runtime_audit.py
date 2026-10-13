"""Per-turn parity and official-budget accounting for route PPO."""

from __future__ import annotations

import json
import statistics
import subprocess
import time
from collections.abc import Mapping
from pathlib import Path
from typing import Any, cast

import numpy as np

from kagg_revue.bc.actions import ReplayActionEncoder
from kagg_revue.bc.dataset import sha256_file
from kagg_revue.core.backend import load_backend
from kagg_revue.core.provenance import source_identity
from kagg_revue.opponents.kaito.native import create_native_session as kaito_session
from kagg_revue.opponents.kaito.routes import ROUTE_NAMES
from kagg_revue.opponents.native_batch import (
    create_native_opponent_session,
    step_native_opponent_batch,
)
from kagg_revue.rl.routes.config import RoutePpoSettings
from kagg_revue.rl.routes.runtime import RoutePolicyRuntime, load_route_model
from kagg_revue.rl.routes.runtime_audit_config import RouteRuntimeAuditSettings
from kagg_revue.rl.routes.train import _artifact_identities, _resolve


def _revision(root: Path) -> str:
    return subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def _resolve_audit(
    settings: RouteRuntimeAuditSettings,
    root: Path,
) -> RouteRuntimeAuditSettings:
    def path(value: Path) -> Path:
        return value.resolve() if value.is_absolute() else (root / value).resolve()

    return settings.model_copy(
        update={
            "checkpoint_path": path(settings.checkpoint_path),
            "confirmation_report": path(settings.confirmation_report),
            "output_dir": path(settings.output_dir),
        }
    )


def _confirmation_games(path: Path) -> dict[tuple[str, int, int], Mapping[str, Any]]:
    raw = cast(Mapping[str, Any], json.loads(path.read_text(encoding="utf-8")))
    games = raw.get("games")
    if not isinstance(games, list):
        raise ValueError("route confirmation report lacks per-game outcomes")
    result: dict[tuple[str, int, int], Mapping[str, Any]] = {}
    for value in games:
        if not isinstance(value, Mapping):
            raise ValueError("route confirmation game is not a mapping")
        game = cast(Mapping[str, Any], value)
        key = (str(game["opponent_id"]), int(game["seed"]), int(game["seat"]))
        if key in result:
            raise ValueError("route confirmation report repeats a game")
        result[key] = game
    return result


def _action_differs(
    left_tokens: np.ndarray[Any, np.dtype[np.int64]],
    left_quantities: np.ndarray[Any, np.dtype[np.int64]],
    left_count: int,
    left_units: int,
    right_tokens: np.ndarray[Any, np.dtype[np.int64]],
    right_quantities: np.ndarray[Any, np.dtype[np.int64]],
    right_count: int,
    right_units: int,
    market_stop_token: int,
) -> bool:
    if left_count > left_units and int(left_tokens[left_count - 1]) == market_stop_token:
        left_count -= 1
    if right_count > right_units and int(right_tokens[right_count - 1]) == market_stop_token:
        right_count -= 1
    if left_count != right_count or left_units != right_units:
        return True
    return not (
        np.array_equal(left_tokens[:left_count], right_tokens[:right_count])
        and np.array_equal(
            left_quantities[:left_count],
            right_quantities[:right_count],
        )
    )


def audit_route_runtime(
    raw_training: RoutePpoSettings,
    raw_audit: RouteRuntimeAuditSettings,
    repository_root: Path,
) -> dict[str, object]:
    """Audit reference actions, terminal parity, and 1s+60s accounting."""
    root = repository_root.resolve()
    training = _resolve(raw_training, root)
    audit = _resolve_audit(raw_audit, root)
    output_root = (root / "outputs").resolve()
    paths = (audit.checkpoint_path, audit.confirmation_report, audit.output_dir)
    if any(not path.is_relative_to(output_root) for path in paths):
        raise ValueError("route runtime audit path escaped outputs/")
    if not audit.checkpoint_path.is_file() or not audit.confirmation_report.is_file():
        raise FileNotFoundError("route runtime audit input is missing")
    if audit.output_dir.exists():
        raise FileExistsError(f"route runtime audit output exists: {audit.output_dir}")
    source = cast(Mapping[str, object], source_identity(root))
    if bool(source["worktree_dirty"]):
        raise RuntimeError("formal route runtime audit requires a clean worktree")
    backend = load_backend(root)
    artifacts = _artifact_identities(backend, training)
    initialization_started = time.perf_counter()
    model, checkpoint = load_route_model(
        audit.checkpoint_path,
        prior_logit=audit.prior_logit,
    )
    initialization_seconds = time.perf_counter() - initialization_started
    if checkpoint.get("artifact_identities") != artifacts:
        raise ValueError("route runtime checkpoint artifacts differ from current runtime")
    expected_games = _confirmation_games(audit.confirmation_report)
    jobs = tuple(
        (seed, seat, opponent)
        for opponent in training.opponents
        for seed in range(audit.seed_start, audit.seed_start + audit.seed_count)
        for seat in (0, 1)
    )
    missing = {
        (opponent, seed, seat) for seed, seat, opponent in jobs
    } - set(expected_games)
    if missing:
        raise ValueError("route runtime audit jobs are absent from confirmation report")
    engines = [
        backend.engine(seed=seed, configuration=training.environment)
        for seed, _seat, _opponent in jobs
    ]
    resolved_environment = cast(dict[str, object], dict(engines[0].configuration))
    players = np.asarray([seat for _seed, seat, _opponent in jobs], dtype=np.int64)
    opponent_ids = tuple(opponent for _seed, _seat, opponent in jobs)
    runtimes = [
        RoutePolicyRuntime(
            engine.configuration,
            model,
            unit_limit=training.rollout.unit_limit,
        )
        for engine in engines
    ]
    market_orders = resolved_environment["maxMarketOrdersPerTurn"]
    if not isinstance(market_orders, int) or isinstance(market_orders, bool):
        raise TypeError("route runtime market order capacity must be an integer")
    opponent_sessions = [
        create_native_opponent_session(opponent, market_orders)
        for opponent in opponent_ids
    ]
    parity_sessions = [kaito_session(market_orders) for _ in jobs]
    codec_spec = cast(Mapping[str, Any], backend.action_codec_spec())
    codec = ReplayActionEncoder(codec_spec)
    market_stop_token = int(codec_spec["market_stop_token"])
    width = market_orders + training.rollout.unit_limit
    tokens = np.zeros((len(jobs), width), dtype=np.int64)
    quantities = np.zeros_like(tokens)
    counts = np.zeros(len(jobs), dtype=np.int64)
    units = np.zeros(len(jobs), dtype=np.int64)
    parity_tokens = np.zeros_like(tokens)
    parity_quantities = np.zeros_like(tokens)
    parity_counts = np.zeros_like(counts)
    parity_units = np.zeros_like(units)
    routes = np.zeros(len(jobs), dtype=np.int64)
    done = np.zeros(len(jobs), dtype=np.bool_)
    remaining_overage = np.full(
        len(jobs),
        training.remaining_overage_seconds,
        dtype=np.float64,
    )
    timings: list[int] = []
    action_mismatches = 0
    mismatch_samples: list[dict[str, object]] = []
    calls = np.zeros(len(jobs), dtype=np.int64)
    started = time.perf_counter()
    while not bool(done.all()):
        step = int(engines[0].step_index)
        tokens.fill(0)
        quantities.fill(0)
        counts.fill(0)
        units.fill(0)
        for index, (engine, player, runtime) in enumerate(
            zip(engines, players, runtimes, strict=True)
        ):
            observation = cast(Mapping[str, Any], engine.observation(int(player)))
            action_started = time.perf_counter_ns()
            action = runtime.act(observation)
            elapsed_ns = time.perf_counter_ns() - action_started
            timings.append(elapsed_ns)
            calls[index] += 1
            elapsed_seconds = elapsed_ns / 1_000_000_000
            remaining_overage[index] -= max(
                0.0,
                elapsed_seconds - training.act_timeout_seconds,
            )
            encoded = codec.encode(
                action,
                unit_count=1 + len(action.get("hands", [])),
                max_market_orders=market_orders,
            )
            count = len(encoded.tokens)
            tokens[index, :count] = encoded.tokens
            quantities[index, :count] = encoded.quantities
            counts[index] = count
            units[index] = encoded.unit_decisions
            selected = str(runtime.diagnostics(int(player))["selected_route"])
            routes[index] = ROUTE_NAMES.index(selected)
        backend.kaito_v48_route_action_numeric_batch(
            engines,
            players,
            parity_sessions,
            routes,
            parity_tokens,
            parity_quantities,
            parity_counts,
            parity_units,
            min(training.rollout.cpu_workers, len(jobs)),
        )
        for index, job in enumerate(jobs):
            differs = _action_differs(
                tokens[index],
                quantities[index],
                int(counts[index]),
                int(units[index]),
                parity_tokens[index],
                parity_quantities[index],
                int(parity_counts[index]),
                int(parity_units[index]),
                market_stop_token,
            )
            if not differs:
                continue
            action_mismatches += 1
            if len(mismatch_samples) < 8:
                mismatch_samples.append(
                    {
                        "opponent_id": job[2],
                        "seed": job[0],
                        "seat": job[1],
                        "step": step,
                        "selected_route": int(routes[index]),
                    }
                )
        done = step_native_opponent_batch(
            backend,
            engines,
            players,
            opponent_ids,
            opponent_sessions,
            tokens,
            quantities,
            counts,
            units,
            training.rollout.cpu_workers,
        )

    terminal_mismatches: list[dict[str, object]] = []
    outcomes: list[int] = []
    for (seed, seat, opponent), engine in zip(jobs, engines, strict=True):
        cash = float(engine.money(seat))
        opponent_cash = float(engine.money(1 - seat))
        outcome = int(cash > opponent_cash) - int(cash < opponent_cash)
        outcomes.append(outcome)
        expected = expected_games[(opponent, seed, seat)]
        if (
            cash != float(expected["terminal_cash"])
            or opponent_cash != float(expected["opponent_cash"])
            or outcome != int(expected["outcome"])
        ):
            terminal_mismatches.append(
                {
                    "opponent_id": opponent,
                    "seed": seed,
                    "seat": seat,
                    "actual": [cash, opponent_cash, outcome],
                    "expected": [
                        expected["terminal_cash"],
                        expected["opponent_cash"],
                        expected["outcome"],
                    ],
                }
            )
    timing_ns = np.asarray(timings, dtype=np.int64)
    errors = sum(
        int(runtime.diagnostics(seat)["errors"])
        for runtime, (_seed, seat, _opponent) in zip(runtimes, jobs, strict=True)
    )
    official_budget_passes = bool(
        timing_ns.size
        and remaining_overage.min() >= 0.0
        and errors == 0
    )
    parity_passes = action_mismatches == 0 and not terminal_mismatches
    maximum_ms = float(timing_ns.max()) / 1_000_000
    report: dict[str, object] = {
        "schema_version": "event-route-ppo-runtime-audit-v1",
        "source": {"revision": _revision(root), **dict(source)},
        "checkpoint": {
            "path": str(audit.checkpoint_path.relative_to(root)),
            "sha256": sha256_file(audit.checkpoint_path),
            "source_revision": checkpoint["source_revision"],
            "prior_logit": audit.prior_logit,
        },
        "confirmation_report": {
            "path": str(audit.confirmation_report.relative_to(root)),
            "sha256": sha256_file(audit.confirmation_report),
        },
        "artifact_identities": artifacts,
        "panel": {
            "opponents": list(training.opponents),
            "seed_start": audit.seed_start,
            "seed_count": audit.seed_count,
            "paired_seats": True,
            "games": len(jobs),
        },
        "outcomes": {
            "wins": sum(value > 0 for value in outcomes),
            "ties": sum(value == 0 for value in outcomes),
            "losses": sum(value < 0 for value in outcomes),
        },
        "parity": {
            "passes": parity_passes,
            "action_calls": int(calls.sum()),
            "normalization": "ignore one optional trailing MARKET:STOP token",
            "action_mismatches": action_mismatches,
            "action_mismatch_samples": mismatch_samples,
            "terminal_mismatches": terminal_mismatches,
        },
        "official_budget": {
            "passes": official_budget_passes,
            "act_timeout_seconds": training.act_timeout_seconds,
            "initial_overage_seconds": training.remaining_overage_seconds,
            "minimum_remaining_overage_seconds": float(remaining_overage.min()),
            "errors": errors,
            "calls": int(timing_ns.size),
            "p50_ms": float(np.percentile(timing_ns, 50)) / 1_000_000,
            "p95_ms": float(np.percentile(timing_ns, 95)) / 1_000_000,
            "p99_ms": float(np.percentile(timing_ns, 99)) / 1_000_000,
            "max_ms": maximum_ms,
            "mean_ms": statistics.fmean(timing_ns) / 1_000_000,
            "shared_model_initialization_ms": initialization_seconds * 1000.0,
        },
        "runtime_boundary": {
            "engine": "native official-rule parity backend",
            "official_engine_parity": False,
            "observation": "official observation dictionary",
            "encoder": "native official-observation numeric ABI",
            "executor": "Python Kaito v48 reference runtime",
            "device": "CPU",
            "deployment_package_status": "research runtime; packaging remains pending",
        },
        "resolved_environment": resolved_environment,
        "elapsed_seconds": time.perf_counter() - started,
    }
    audit.output_dir.mkdir(parents=True)
    report_path = audit.output_dir / "runtime-audit-report.json"
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    (audit.output_dir / "resolved-settings.json").write_text(
        json.dumps(
            {
                "route_ppo": training.model_dump(mode="json"),
                "audit": audit.model_dump(mode="json"),
            },
            indent=2,
            sort_keys=True,
            default=str,
        ),
        encoding="utf-8",
    )
    if not parity_passes or not official_budget_passes:
        raise RuntimeError("route runtime failed parity or official-budget audit")
    return {
        "report": str(report_path),
        "games": len(jobs),
        "action_calls": int(timing_ns.size),
        "max_ms": maximum_ms,
        "parity_passes": parity_passes,
        "official_budget_passes": official_budget_passes,
    }


__all__ = ["audit_route_runtime"]
