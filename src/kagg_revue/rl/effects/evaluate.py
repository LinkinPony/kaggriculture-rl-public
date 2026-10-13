"""Complete official-rule panels for atomic-effect checkpoints."""

from __future__ import annotations

import json
import statistics
import time
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

import torch

from kagg_revue.bc.dataset import sha256_file
from kagg_revue.core.backend import load_backend
from kagg_revue.core.provenance import source_identity
from kagg_revue.rl.effects.checkpoint import load_checkpoint
from kagg_revue.rl.effects.evaluation_config import EffectEvaluationSettings
from kagg_revue.rl.effects.population import effect_opponent_identities
from kagg_revue.rl.effects.rollout import EffectGameResult, EffectRolloutCollector
from kagg_revue.rl.effects.runtime import native_contract


def _write_json(path: Path, value: object) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(value, indent=2, sort_keys=True, default=str),
        encoding="utf-8",
    )
    temporary.replace(path)


def _integer(value: object, name: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise TypeError(f"effect evaluation {name} must be an integer")
    return value


def _mapping(value: object, name: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise TypeError(f"effect evaluation {name} must be a mapping")
    return cast(Mapping[str, object], value)


def _checkpoint_identity(
    settings: EffectEvaluationSettings,
    root: Path,
) -> tuple[Path, Mapping[str, object]]:
    checkpoint = (root / settings.checkpoint).resolve()
    report_path = (root / settings.training_report).resolve()
    if not checkpoint.is_file() or not report_path.is_file():
        raise FileNotFoundError("effect evaluation checkpoint or report is missing")
    report_value: object = json.loads(report_path.read_text(encoding="utf-8"))
    report = _mapping(report_value, "training report")
    if report.get("status") == "training_complete":
        selected = _mapping(report.get("best"), "best checkpoint")
    elif report.get("status") == "complete":
        selected = _mapping(report.get("final_metrics"), "final RL metrics")
    else:
        raise ValueError("effect evaluation requires a completed training report")
    identity = _mapping(selected.get("checkpoint"), "selected checkpoint identity")
    recorded_path = Path(str(identity.get("path"))).resolve()
    if recorded_path != checkpoint:
        raise ValueError("effect evaluation profile does not name the selected checkpoint")
    if (
        checkpoint.stat().st_size != _integer(identity.get("size_bytes"), "checkpoint size")
        or sha256_file(checkpoint) != str(identity.get("sha256"))
    ):
        raise ValueError("effect evaluation checkpoint differs from its training report")
    return checkpoint, report


def _summary(games: Sequence[EffectGameResult]) -> dict[str, int | float]:
    if not games:
        raise ValueError("effect evaluation produced no games")
    outcomes = [game.outcome for game in games]
    return {
        "games": len(games),
        "seeds": len({game.seed for game in games}),
        "wins": sum(outcome > 0 for outcome in outcomes),
        "ties": sum(outcome == 0 for outcome in outcomes),
        "losses": sum(outcome < 0 for outcome in outcomes),
        "mean_terminal_cash": statistics.fmean(game.terminal_cash for game in games),
        "mean_cash_difference": statistics.fmean(
            game.terminal_cash - game.opponent_cash for game in games
        ),
    }


def _game_record(panel: str, game: EffectGameResult) -> dict[str, object]:
    return {
        "panel": panel,
        "episode_id": game.episode_id,
        "opponent_id": game.opponent_id,
        "seed": game.seed,
        "candidate_seat": game.seat,
        "outcome": game.outcome,
        "terminal_cash": game.terminal_cash,
        "opponent_cash": game.opponent_cash,
        "cash_difference": game.terminal_cash - game.opponent_cash,
        "done": True,
    }


def _panel(
    name: str,
    seeds: Sequence[int],
    settings: EffectEvaluationSettings,
    backend: Any,
    model: Any,
    contract: Any,
    device: torch.device,
) -> tuple[dict[str, object], list[dict[str, object]]]:
    matchups: dict[str, object] = {}
    records: list[dict[str, object]] = []
    panel_started = time.perf_counter()
    for index, opponent_id in enumerate(settings.opponents, start=1):
        generator = torch.Generator(device=device).manual_seed(
            settings.selection_seed_start + settings.confirmation_seed_start + index
        )
        collector = EffectRolloutCollector(
            backend,
            model,
            contract,
            settings.environment,
            unit_limit=settings.unit_limit,
            cpu_workers=settings.cpu_workers,
            device=device,
            action_generator=generator,
            maximum_graph_variants=settings.maximum_graph_variants,
            sample_actions=False,
        )
        jobs = tuple(
            (seed, seat, opponent_id)
            for seed in seeds
            for seat in (0, 1)
        )
        try:
            result = collector.evaluate_jobs(jobs)
        finally:
            collector.close()
        summary = _summary(result.games)
        matchups[opponent_id] = {
            "outcomes": summary,
            "execution": result.diagnostics,
        }
        records.extend(_game_record(name, game) for game in result.games)
        print(
            json.dumps(
                {
                    "panel": name,
                    "completed_opponents": index,
                    "total_opponents": len(settings.opponents),
                    "opponent": opponent_id,
                    "outcomes": summary,
                },
                sort_keys=True,
            ),
            flush=True,
        )
        del result, collector
        if device.type == "cuda":
            torch.cuda.empty_cache()
    outcomes = [_integer(record.get("outcome"), "game outcome") for record in records]
    return (
        {
            "name": name,
            "seeds": list(seeds),
            "outcomes": {
                "games": len(outcomes),
                "wins": sum(value > 0 for value in outcomes),
                "ties": sum(value == 0 for value in outcomes),
                "losses": sum(value < 0 for value in outcomes),
            },
            "matchups": matchups,
            "elapsed_seconds": time.perf_counter() - panel_started,
        },
        records,
    )


def _positive_wdl(panel: Mapping[str, object]) -> bool:
    outcomes = _mapping(panel.get("outcomes"), "panel outcomes")
    return _integer(outcomes.get("wins"), "wins") > _integer(
        outcomes.get("losses"), "losses"
    )


def _positive_lineages(panel: Mapping[str, object]) -> list[str]:
    matchups = _mapping(panel.get("matchups"), "panel matchups")
    result: list[str] = []
    for opponent, raw_matchup in matchups.items():
        matchup = _mapping(raw_matchup, f"{opponent} matchup")
        outcomes = _mapping(matchup.get("outcomes"), f"{opponent} outcomes")
        if _integer(outcomes.get("wins"), "wins") > _integer(
            outcomes.get("losses"), "losses"
        ):
            result.append(str(opponent))
    return result


def evaluate_effect_checkpoint(
    settings: EffectEvaluationSettings,
    repository_root: Path,
) -> dict[str, object]:
    """Evaluate one authenticated BC checkpoint on disjoint paired panels."""
    root = repository_root.resolve()
    source = source_identity(root)
    if source["worktree_dirty"]:
        raise RuntimeError("formal effect evaluation requires a clean source revision")
    output_dir = (root / settings.output_dir).resolve()
    if not output_dir.is_relative_to((root / "outputs").resolve()):
        raise ValueError("effect evaluation output escaped outputs/")
    if output_dir.exists():
        raise FileExistsError(f"effect evaluation output already exists: {output_dir}")
    checkpoint, training_report = _checkpoint_identity(settings, root)
    device = torch.device(settings.device)
    if device.type == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("effect evaluation requested CUDA without an available GPU")
    torch.set_num_threads(settings.cpu_workers)
    backend = load_backend(root)
    engine = backend.engine(settings.selection_seed_start, settings.environment)
    environment = cast(dict[str, object], engine.configuration)
    settings = settings.model_copy(update={"environment": environment})
    contract = native_contract(backend, environment)
    model, checkpoint_metadata = load_checkpoint(checkpoint, contract, device)
    model.eval()
    actor = model.actor.architecture
    if (
        actor.unit_shape[1] != settings.unit_limit
        or actor.board_shape[-1] != _integer(environment.get("boardSize"), "board size")
        or actor.max_history
        < _integer(environment.get("episodeSteps"), "episode steps") - 1
    ):
        raise ValueError("effect evaluation checkpoint differs from its runtime profile")
    identities = effect_opponent_identities(
        backend,
        root,
        {opponent: 1.0 / len(settings.opponents) for opponent in settings.opponents},
        settings.public_agent_manifest,
    )
    output_dir.mkdir(parents=True)
    _write_json(output_dir / "resolved-settings.json", settings.model_dump(mode="json"))
    started = time.perf_counter()
    selection, selection_games = _panel(
        "selection",
        tuple(
            range(
                settings.selection_seed_start,
                settings.selection_seed_start + settings.selection_seed_count,
            )
        ),
        settings,
        backend,
        model,
        contract,
        device,
    )
    selection_passed = _positive_wdl(selection) and bool(_positive_lineages(selection))
    confirmation: dict[str, object] | None = None
    confirmation_games: list[dict[str, object]] = []
    if selection_passed:
        confirmation, confirmation_games = _panel(
            "confirmation",
            tuple(
                range(
                    settings.confirmation_seed_start,
                    settings.confirmation_seed_start
                    + settings.confirmation_seed_count,
                )
            ),
            settings,
            backend,
            model,
            contract,
            device,
        )
    confirmation_passed = (
        confirmation is not None
        and _positive_wdl(confirmation)
        and bool(_positive_lineages(confirmation))
    )
    games = [*selection_games, *confirmation_games]
    games_path = output_dir / "games.json"
    _write_json(games_path, games)
    report: dict[str, object] = {
        "schema_version": "atomic-effect-closed-loop-evaluation-v1",
        "generated_at": datetime.now(UTC).isoformat(),
        "purpose": "Checkpoint closed-loop eligibility; no deployment promotion authority",
        "source": source,
        "training_source": training_report.get("source"),
        "checkpoint": {
            "path": str(settings.checkpoint),
            "sha256": sha256_file(checkpoint),
            "size_bytes": checkpoint.stat().st_size,
            "metadata": checkpoint_metadata.get("checkpoint_identity"),
        },
        "dataset": training_report.get("dataset"),
        "native_backend": backend.identity,
        "opponents": identities,
        "decision_surface": ["win", "loss", "tie"],
        "diagnostic_surface": ["terminal cash", "terminal cash difference"],
        "paired_seats": True,
        "selection": selection,
        "confirmation": confirmation
        or {
            "status": "skipped",
            "reason": "selection aggregate W/D/L gate did not pass",
            "seeds_reserved": list(
                range(
                    settings.confirmation_seed_start,
                    settings.confirmation_seed_start
                    + settings.confirmation_seed_count,
                )
            ),
        },
        "decision": {
            "formal_rl_warm_start_eligible": bool(confirmation_passed),
            "selection_passed": selection_passed,
            "confirmation_passed": bool(confirmation_passed),
            "selection_positive_lineages": _positive_lineages(selection),
            "confirmation_positive_lineages": (
                _positive_lineages(confirmation) if confirmation is not None else []
            ),
            "incumbent_mutated": False,
        },
        "execution": {
            "device": str(device),
            "gpu": torch.cuda.get_device_name(device) if device.type == "cuda" else None,
            "native_tape_retained": False,
            "sample_actions": False,
            "act_timeout_seconds": settings.act_timeout_seconds,
            "remaining_overage_seconds": settings.remaining_overage_seconds,
            "deployment_timeout_enforced": False,
            "deployment_authority": False,
            "elapsed_seconds": time.perf_counter() - started,
            "games": len(games),
        },
        "games_artifact": {
            "path": str(settings.output_dir / "games.json"),
            "sha256": sha256_file(games_path),
            "games": len(games),
        },
    }
    _write_json(output_dir / "evaluation-report.json", report)
    return report


__all__ = ["evaluate_effect_checkpoint"]
