"""Complete-game conformance against the authenticated original Python agents."""

from __future__ import annotations

import hashlib
import json
import multiprocessing
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
from typing import Any

from kagg_revue.opponents.compilation.diagnostics import source_diagnostics, stable
from kagg_revue.opponents.compilation.sources import CANDIDATES
from kagg_revue.opponents.portfolios.catalog import ACTIVE_IDS
from kagg_revue.opponents.portfolios.native import create_native_session, native_action
from kagg_revue.opponents.public import PublicAgentRuntime, load_public_agent_manifest


def qualify_game(job: dict[str, Any]) -> dict[str, Any]:
    """Compare every parsed action and both complete engine trajectories."""
    from kagg_revue.native import _revue_native as native

    records = load_public_agent_manifest(Path(job["manifest"])).by_id()
    names = job["agents"]
    engine = native.Engine(job["seed"], {})
    shadow = engine.clone()
    configuration = engine.configuration
    originals = [PublicAgentRuntime(records[name], Path.cwd(), configuration) for name in names]
    sessions = [create_native_session(name) for name in names]
    forks: list[Any] | None = None
    source_seconds = [0.0, 0.0]
    native_seconds = [0.0, 0.0]
    fingerprints = [hashlib.sha256(), hashlib.sha256()]
    started = time.perf_counter()
    comparisons = 0
    compiled = {candidate.agent_id for candidate in CANDIDATES}
    for step in range(719):
        actions = []
        converted = []
        for seat in range(2):
            observation = engine.observation(seat)
            before = time.perf_counter()
            source_action = originals[seat].act(observation)
            source_seconds[seat] += time.perf_counter() - before
            before = time.perf_counter()
            action = native_action(sessions[seat], shadow, seat)
            native_seconds[seat] += time.perf_counter() - before
            expected = native.canonical_opponent_action(source_action, 10)
            actual = native.canonical_opponent_action(action, 10)
            if actual != expected:
                return {
                    **job,
                    "passed": False,
                    "step": step,
                    "seat": seat,
                    "expected": expected,
                    "actual": actual,
                    "source_raw": source_action,
                    "native_raw": action,
                }
            if forks is not None:
                fork_action = native_action(forks[seat], shadow, seat)
                if native.canonical_opponent_action(fork_action, 10) != actual:
                    raise AssertionError("cloned native opponent state diverged")
            if names[seat] in compiled:
                source_details = source_diagnostics(originals[seat])
                native_details = stable(native.native_opponent_diagnostics(sessions[seat]))
                if source_details != native_details:
                    return {
                        **job,
                        "passed": False,
                        "step": step,
                        "seat": seat,
                        "reason": "controller diagnostics differ",
                        "expected": source_details,
                        "actual": native_details,
                    }
            fingerprints[seat].update(json.dumps(actual, sort_keys=True).encode())
            actions.append(source_action)
            converted.append(action)
            comparisons += 1
        # A copied session must retain every route's private controller state.
        if step % 72 == 0:
            forks = [session.clone() for session in sessions]
        if job.get("perturb") and step % 37 == 0:
            actions[0] = converted[0] = {"farmer": ["DIG"], "hands": [], "market": []}
        engine.step(*actions)
        shadow.step(*converted)
        if engine.observation(0) != shadow.observation(0) or engine.observation(
            1
        ) != shadow.observation(1):
            raise AssertionError(f"engine trajectory differs at {step}")
    return {
        **job,
        "passed": True,
        "actions": comparisons,
        "money": [engine.money(seat) for seat in range(2)],
        "fingerprints": [digest.hexdigest() for digest in fingerprints],
        "source_seconds": source_seconds,
        "native_seconds": native_seconds,
        "wall_seconds": time.perf_counter() - started,
    }


def qualify(
    manifest: Path,
    seeds: list[int],
    workers: int,
    output: Path,
    perturb: bool = False,
    agents: list[str] | None = None,
) -> dict[str, Any]:
    """Run both seats of every pairing, plus mirrored games, in fresh processes."""
    output.mkdir(parents=True, exist_ok=True)
    selected = tuple(
        name for name in ACTIVE_IDS if name in load_public_agent_manifest(manifest).by_id()
    )
    if agents is not None:
        if not agents or len(agents) != len(set(agents)) or not set(agents) <= set(selected):
            raise ValueError("qualification agents must be distinct active manifest identities")
        selected = tuple(agents)
    jobs = [
        {"manifest": str(manifest), "agents": [left, right], "seed": seed, "perturb": perturb}
        for seed in seeds
        for left in selected
        for right in selected
    ]
    rows = []
    with ProcessPoolExecutor(
        max_workers=workers, mp_context=multiprocessing.get_context("spawn"), max_tasks_per_child=1
    ) as pool:
        pending = [pool.submit(qualify_game, job) for job in jobs]
        for future in as_completed(pending):
            row = future.result()
            rows.append(row)
            print(json.dumps(row), flush=True)
            (output / "games.json").write_text(json.dumps(rows, indent=2) + "\n")
    from kagg_revue.native import _revue_native as native

    report = {
        "passed": all(row["passed"] for row in rows),
        "games": len(rows),
        "actions": sum(row.get("actions", 0) for row in rows),
        "manifest_sha256": hashlib.sha256(manifest.read_bytes()).hexdigest(),
        "binary_sha256": hashlib.sha256(Path(native.__file__).read_bytes()).hexdigest(),
    }
    (output / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    return report
