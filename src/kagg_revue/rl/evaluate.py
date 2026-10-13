"""Independent closed-loop evaluation of an actor-critic challenger."""

from __future__ import annotations

import json
import time
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

import torch

from kagg_revue.bc.dataset import sha256_file
from kagg_revue.bc.evaluate import (
    AgentFactory,
    actor_path_from_report,
    run_paired_panel,
    summarize_games,
)
from kagg_revue.core.backend import BackendApi
from kagg_revue.core.observability import ScalarLogger, synchronize, throughput
from kagg_revue.core.provenance import source_identity
from kagg_revue.policy.runtime import BaselineAgent, TurnPolicyAgent
from kagg_revue.rl.config import RlSettings


def _integer(value: object, name: str) -> int:
    if not isinstance(value, int | float) or isinstance(value, bool):
        raise TypeError(f"{name} is not numeric")
    return int(value)


def _row_key(row: Mapping[str, object]) -> tuple[str, int, int]:
    return (
        str(row["opponent_id"]),
        _integer(row["seed"], "seed"),
        _integer(row["candidate_seat"], "candidate_seat"),
    )


def compare_paired_outcomes(
    challenger_rows: Sequence[Mapping[str, object]],
    incumbent_rows: Sequence[Mapping[str, object]],
) -> dict[str, int]:
    """Compare direct W/D/L outcomes on identical opponent, seed and seat keys."""
    challenger = {_row_key(row): _integer(row["outcome"], "outcome") for row in challenger_rows}
    incumbent = {_row_key(row): _integer(row["outcome"], "outcome") for row in incumbent_rows}
    if len(challenger) != len(challenger_rows) or len(incumbent) != len(incumbent_rows):
        raise ValueError("paired comparison contains duplicate match keys")
    if challenger.keys() != incumbent.keys():
        raise ValueError("challenger and incumbent match panels are not paired")
    differences = [challenger[key] - incumbent[key] for key in challenger]
    return {
        "games": len(differences),
        "wins": sum(value > 0 for value in differences),
        "ties": sum(value == 0 for value in differences),
        "losses": sum(value < 0 for value in differences),
    }


def _strict_wdl_improvement(summary: Mapping[str, object]) -> bool:
    return _integer(summary["wins"], "wins") > _integer(summary["losses"], "losses")


def advancement_decision(
    *,
    selection_population: Mapping[str, object],
    selection_head_to_head: Mapping[str, object],
    confirmation_population: Mapping[str, object] | None,
    confirmation_head_to_head: Mapping[str, object] | None,
    evidence_valid: bool,
    clean_source: bool,
    public_opponents: int,
) -> dict[str, object]:
    """Apply a W/D/L-only eligibility gate without mutating the incumbent."""
    selection_passed = _strict_wdl_improvement(selection_population) and _strict_wdl_improvement(
        selection_head_to_head
    )
    confirmation_passed = (
        confirmation_population is not None
        and confirmation_head_to_head is not None
        and _strict_wdl_improvement(confirmation_population)
        and _strict_wdl_improvement(confirmation_head_to_head)
    )
    reasons: list[str] = []
    if public_opponents < 1:
        reasons.append("no_authenticated_public_notebook_opponent")
    if not evidence_valid:
        reasons.append("match_completion_or_timeout_gate_failed")
    if not selection_passed:
        reasons.append("selection_wdl_did_not_improve")
    if selection_passed and not confirmation_passed:
        reasons.append("confirmation_wdl_did_not_improve")
    if not clean_source:
        reasons.append("source_revision_is_dirty")
    eligible = not reasons
    return {
        "status": "eligible_for_manual_promotion" if eligible else "retain_incumbent",
        "promotion_eligible": eligible,
        "incumbent_mutated": False,
        "selection_passed": selection_passed,
        "confirmation_passed": confirmation_passed,
        "decision_surface": "paired complete-match W/D/L only",
        "reasons": reasons,
    }


def _actor_factory(backend: BackendApi, settings: RlSettings, artifact: Path) -> AgentFactory:
    def factory(configuration: Mapping[str, Any]) -> TurnPolicyAgent:
        return TurnPolicyAgent(
            backend,
            configuration,
            artifact,
            settings.evaluation_device,
            settings.unit_limit,
            cpu_threads=settings.cpu_threads,
        )

    return factory


def _opponent_factories(
    backend: BackendApi, settings: RlSettings
) -> tuple[dict[str, AgentFactory], dict[str, dict[str, object]], int]:
    manifest = backend.load_public_agent_manifest(settings.public_agent_manifest)
    records = manifest.by_id()
    factories: dict[str, AgentFactory] = {}
    identities: dict[str, dict[str, object]] = {}
    public_count = 0
    for opponent_id in settings.evaluation_opponents:
        if opponent_id == "deterministic_incumbent":

            def baseline(configuration: Mapping[str, Any]) -> BaselineAgent:
                return BaselineAgent(backend, configuration)

            factories[opponent_id] = baseline
            identities[opponent_id] = {"kind": "repository_deterministic_policy"}
            continue
        if opponent_id not in records:
            raise KeyError(f"evaluation opponent is absent from the manifest: {opponent_id}")
        record = records[opponent_id]

        def public(configuration: Mapping[str, Any], record: Any = record) -> Any:
            return backend.public_agent_runtime(record, backend.repository_root, configuration)

        factories[opponent_id] = public
        identities[opponent_id] = {
            "kind": "public_notebook",
            "notebook_ref": record.notebook_ref,
            "notebook_id": record.notebook_id,
            "artifact_sha256": record.sha256,
        }
        public_count += 1
    return factories, identities, public_count


def _initial_actor_path(settings: RlSettings, training_report: Mapping[str, object]) -> Path:
    record = training_report.get("initial_actor")
    if not isinstance(record, Mapping):
        raise ValueError("RL training report lacks its initial actor identity")
    path = Path(str(record["path"]))
    if path.resolve() != settings.initial_actor.resolve():
        raise ValueError("evaluation profile names a different initial actor")
    if not path.is_file() or sha256_file(path) != str(record["sha256"]):
        raise ValueError("initial actor no longer matches the RL training report")
    return path


def _valid_rows(rows: Sequence[Mapping[str, object]], expected_transitions: int) -> bool:
    return all(
        bool(row["done"])
        and _integer(row["transitions"], "transitions") == expected_transitions
        and row["candidate_error"] is None
        and row["opponent_error"] is None
        for row in rows
    )


def _phase(
    name: str,
    seeds: Sequence[int],
    backend: BackendApi,
    settings: RlSettings,
    challenger_factory: AgentFactory,
    incumbent_factory: AgentFactory,
    opponent_factories: Mapping[str, AgentFactory],
) -> tuple[dict[str, object], list[dict[str, object]]]:
    started = time.perf_counter()
    challenger_population: list[dict[str, object]] = []
    incumbent_population: list[dict[str, object]] = []
    matchups: dict[str, object] = {}
    for opponent_id, opponent_factory in opponent_factories.items():
        challenger_rows, challenger_summary = run_paired_panel(
            backend,
            "challenger",
            challenger_factory,
            opponent_id,
            opponent_factory,
            seeds,
            settings,
        )
        incumbent_rows, incumbent_summary = run_paired_panel(
            backend,
            "incumbent",
            incumbent_factory,
            opponent_id,
            opponent_factory,
            seeds,
            settings,
        )
        challenger_population.extend(challenger_rows)
        incumbent_population.extend(incumbent_rows)
        matchups[opponent_id] = {
            "challenger": challenger_summary,
            "incumbent": incumbent_summary,
            "paired_outcome_comparison": compare_paired_outcomes(challenger_rows, incumbent_rows),
        }
    head_rows, head_summary = run_paired_panel(
        backend,
        "challenger",
        challenger_factory,
        "incumbent_actor",
        incumbent_factory,
        seeds,
        settings,
    )
    synchronize(torch.device(settings.evaluation_device))
    elapsed = time.perf_counter() - started
    rows = [*challenger_population, *incumbent_population, *head_rows]
    transitions = sum(_integer(row["transitions"], "transitions") for row in rows)
    return (
        {
            "name": name,
            "seeds": list(seeds),
            "matchups": matchups,
            "population": {
                "challenger": summarize_games(challenger_population),
                "incumbent": summarize_games(incumbent_population),
                "paired_outcome_comparison": compare_paired_outcomes(
                    challenger_population, incumbent_population
                ),
            },
            "head_to_head": head_summary,
            "execution": {
                "elapsed_seconds": elapsed,
                "games": len(rows),
                "transitions": transitions,
                "games_per_second": throughput(len(rows), elapsed),
                "transitions_per_second": throughput(transitions, elapsed),
            },
        },
        rows,
    )


def _comparison(phase: Mapping[str, object]) -> Mapping[str, object]:
    population = cast(Mapping[str, object], phase["population"])
    return cast(Mapping[str, object], population["paired_outcome_comparison"])


def evaluate_actor_critic(
    settings: RlSettings,
    backend: BackendApi,
    training_report: Mapping[str, object],
    repository_root: Path,
) -> dict[str, object]:
    """Evaluate the final challenger against its initial actor on held-out matches."""
    evaluation_device = torch.device(settings.evaluation_device)
    if evaluation_device.type == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("CUDA RL evaluation was requested but no GPU is available")
    torch.set_num_threads(settings.cpu_threads)
    report_path = settings.output_dir / "evaluation-report.json"
    games_path = settings.output_dir / "evaluation-games.json"
    if report_path.exists() or games_path.exists():
        raise FileExistsError("RL evaluation artifacts already exist in the run directory")
    challenger_path = actor_path_from_report(training_report)
    incumbent_path = _initial_actor_path(settings, training_report)
    challenger_factory = _actor_factory(backend, settings, challenger_path)
    incumbent_factory = _actor_factory(backend, settings, incumbent_path)
    opponents, opponent_identities, public_count = _opponent_factories(backend, settings)
    expected_transitions = _integer(settings.environment["episodeSteps"], "episodeSteps") - 1

    synchronize(evaluation_device)
    evaluation_started = time.perf_counter()
    selection, selection_rows = _phase(
        "selection",
        settings.selection_seeds,
        backend,
        settings,
        challenger_factory,
        incumbent_factory,
        opponents,
    )
    selection_valid = _valid_rows(selection_rows, expected_transitions)
    selection_passed = (
        selection_valid
        and _strict_wdl_improvement(_comparison(selection))
        and _strict_wdl_improvement(cast(Mapping[str, object], selection["head_to_head"]))
    )
    confirmation: dict[str, object] | None = None
    confirmation_rows: list[dict[str, object]] = []
    if selection_passed:
        confirmation, confirmation_rows = _phase(
            "confirmation",
            settings.confirmation_seeds,
            backend,
            settings,
            challenger_factory,
            incumbent_factory,
            opponents,
        )
    all_rows = [*selection_rows, *confirmation_rows]
    confirmation_valid = confirmation is not None and _valid_rows(
        confirmation_rows, expected_transitions
    )
    current_source = source_identity(repository_root)
    training_source = training_report.get("source")
    clean_source = (
        isinstance(training_source, Mapping)
        and not bool(training_source.get("worktree_dirty", True))
        and not bool(current_source["worktree_dirty"])
        and training_source.get("commit") == current_source["commit"]
        and training_source.get("source_tree_sha256") == current_source["source_tree_sha256"]
    )
    decision = advancement_decision(
        selection_population=_comparison(selection),
        selection_head_to_head=cast(Mapping[str, object], selection["head_to_head"]),
        confirmation_population=(_comparison(confirmation) if confirmation is not None else None),
        confirmation_head_to_head=(
            cast(Mapping[str, object], confirmation["head_to_head"])
            if confirmation is not None
            else None
        ),
        evidence_valid=selection_valid
        and (bool(confirmation_valid) if confirmation is not None else True),
        clean_source=clean_source,
        public_opponents=public_count,
    )
    games_path.write_text(json.dumps(all_rows, indent=2, sort_keys=True), encoding="utf-8")
    with ScalarLogger(settings.output_dir, settings.observability) as logger:
        logger.scalars("rl_evaluation/selection", selection, settings.updates + 1)
        if confirmation is not None:
            logger.scalars("rl_evaluation/confirmation", confirmation, settings.updates + 2)
    total_elapsed = time.perf_counter() - evaluation_started
    report: dict[str, object] = {
        "schema_version": "terminal-wdl-evaluation-v1",
        "generated_at": datetime.now(UTC).isoformat(),
        "purpose": "independent closed-loop incumbent/challenger decision",
        "source": current_source,
        "training_source": training_source,
        "resolved_settings": settings.model_dump(mode="json"),
        "decision_surface": ["win", "loss", "tie"],
        "diagnostic_surface": ["terminal cash", "cash difference"],
        "paired_seats": True,
        "selection": selection,
        "confirmation": confirmation
        or {
            "status": "skipped",
            "reason": "selection W/D/L gate did not pass",
            "seeds_reserved": list(settings.confirmation_seeds),
        },
        "decision": decision,
        "execution": {
            "device": settings.evaluation_device,
            "act_timeout_seconds": settings.act_timeout_seconds,
            "remaining_overage_seconds": settings.remaining_overage_seconds,
            "timeout_enforced": True,
            "expected_transitions_per_game": expected_transitions,
            "all_matches_valid": selection_valid
            and (bool(confirmation_valid) if confirmation is not None else True),
            "elapsed_seconds": total_elapsed,
            "games": len(all_rows),
            "games_per_second": throughput(len(all_rows), total_elapsed),
        },
        "backend": backend.identity,
        "opponents": opponent_identities,
        "incumbent_actor": {
            "path": str(incumbent_path),
            "sha256": sha256_file(incumbent_path),
        },
        "challenger_actor": {
            "path": str(challenger_path),
            "sha256": sha256_file(challenger_path),
        },
        "games_artifact": {
            "path": str(games_path),
            "sha256": sha256_file(games_path),
            "games": len(all_rows),
        },
    }
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    return report


__all__ = [
    "advancement_decision",
    "compare_paired_outcomes",
    "evaluate_actor_critic",
]
