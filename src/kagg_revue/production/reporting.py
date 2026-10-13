"""Direct-outcome reports shared with the read-only training dashboard."""

import json
import shutil
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np

from kagg_revue.artifacts.io import digest, write_json
from kagg_revue.production.config import Settings


def qualify_prefix_pipeline(settings: Settings, source: Any) -> None:
    """Publish measured cold/steady cadence after three full prefix PPO updates."""
    with (settings.output_dir / "metrics.jsonl").open() as stream:
        records = [json.loads(line) for line in stream]
    active = [
        row
        for row in records
        if all(
            rank["optimization"]["actor_steps"] > 0 and rank["optimization"]["critic_steps"] > 0
            for rank in row["workers"]
        )
    ][-3:]
    if len(active) != 3 or active[-1]["update"] - active[0]["update"] != 2:
        return
    checkpoints = [
        settings.output_dir / "checkpoints" / f"update-{row['update']:04d}.pt" for row in active
    ]
    if not all(path.is_file() for path in checkpoints):
        return
    evidence = []
    preserved = settings.output_dir / "qualification" / "checkpoints"
    preserved.mkdir(parents=True, exist_ok=True)
    for path in checkpoints:
        destination = preserved / path.name
        if not destination.exists():
            destination.hardlink_to(path)
        evidence.append({"path": str(destination), "sha256": digest(destination)})
    ranks = []
    for rank in range(len(settings.devices)):
        steady = [row["workers"][rank] for row in active[1:]]
        ranks.append(
            {
                "rank": rank,
                "rollout_seconds": float(
                    np.mean([r["rollout"]["rollout_seconds"] for r in steady])
                ),
                "inference_seconds": float(
                    np.mean([r["rollout"]["inference_seconds"] for r in steady])
                ),
                "collation_seconds": float(
                    np.mean([r["rollout"]["collation_seconds"] for r in steady])
                ),
                "learner_seconds": float(
                    np.mean([r["optimization"]["learner_seconds"] for r in steady])
                ),
                "peak_allocated_bytes": max(r["peak_allocated_bytes"] for r in steady),
                "peak_reserved_bytes": max(r["peak_reserved_bytes"] for r in steady),
                "host_rss_bytes": max(r["host_rss_bytes"] for r in steady),
            }
        )
    write_json(
        settings.output_dir / "qualification.json",
        {
            "qualified_for_unattended_training": True,
            "quality_promotion": False,
            "source": source,
            "initial_checkpoint": {
                "path": str(settings.checkpoint),
                "sha256": digest(settings.checkpoint),
            }
            if settings.checkpoint
            else None,
            "checkpoints": evidence,
            "cold_start": records[0],
            "first_actor_update": active[0],
            "steady_state_ranks": ranks,
            "steady_update_seconds": float(np.mean([row["update_seconds"] for row in active[1:]])),
            "steady_physical_games_per_second": float(
                np.mean([row["physical_games_per_second"] for row in active[1:]])
            ),
        },
    )


def evaluation_report(
    settings: Settings,
    panels: dict[str, dict[str, Any]],
    source: Any,
    *,
    checkpoint: Path | None = None,
    seed: int | None = None,
) -> None:
    """Expose independently evaluated matches against the frozen evaluation panel."""
    outcomes = {}
    for name, panel in panels.items():
        outcomes[name] = {
            "games": len(panel["games"]),
            **{key: panel[key] for key in ("wins", "ties", "losses", "mean_cash_difference")},
            "mean_terminal_cash": panel["mean_cash"],
            "p10_terminal_cash": panel["p10_cash"],
            "sample": panel.get("sample", False),
            "temperature": panel.get("temperature"),
        }
    if checkpoint is not None:
        paired_path = settings.output_dir / "selection" / f"{checkpoint.stem}.npz"
        paired_path.parent.mkdir(parents=True, exist_ok=True)
        games = next(iter(panels.values()))["games"]
        np.savez_compressed(
            paired_path,
            seeds=np.array([game["seed"] for game in games], dtype=np.int64),
            seats=np.array([game["seat"] for game in games], dtype=np.int8),
            opponents=np.array([game["opponent"] for game in games]),
            cash=np.array([[game["cash"], game["opponent_cash"]] for game in games]),
            outcomes=np.array([game["outcome"] for game in games], dtype=np.int8),
        )
    latest = (
        checkpoint or settings.output_dir / "checkpoints" / f"update-{settings.ppo.updates:04d}.pt"
    )
    write_json(
        settings.output_dir / "evaluation-report.json",
        {
            "generated_at": datetime.now(UTC).isoformat(),
            "decision_surface": "complete paired official-rule frozen-opponent matches",
            "execution": {"backend": "native", "deployment_budget_qualified": False},
            "completion": {"complete": True},
            "source": source,
            "checkpoint": {"path": str(latest), "sha256": digest(latest)},
            "seed_start": settings.confirmation_seed if seed is None else seed,
            "outcomes": outcomes,
        },
    )


def retain_checkpoints(directory: Path, keep: int) -> None:
    """Bound generated optimizer storage after the latest checkpoint is safely published."""
    if keep <= 0:
        return
    paths = sorted(directory.glob("update-*.pt"), key=lambda path: int(path.stem.split("-")[-1]))
    for path in paths[:-keep]:
        path.unlink()


def publish_selection(
    settings: Settings, result: dict[str, Any], source: Any, checkpoint: Path, update: int
) -> None:
    """Keep direct paired evidence and a recoverable best selection checkpoint."""
    record = {
        "update": update,
        **{
            key: result[key]
            for key in ("wins", "ties", "losses", "mean_cash", "p10_cash", "mean_cash_difference")
        },
    }
    with (settings.output_dir / "selection-metrics.jsonl").open("a") as stream:
        stream.write(json.dumps(record) + "\n")
    evaluation_report(
        settings,
        {f"selection update {update}": result},
        source,
        checkpoint=checkpoint,
        seed=settings.evaluation_seed,
    )
    best_path = checkpoint.parent / "best-selection.json"
    previous = json.loads(best_path.read_text()) if best_path.exists() else None

    def quality(value: dict[str, Any]) -> int:
        # Equal-sized panels: this ranks wins plus half credit for draws.
        # Terminal cash is diagnostic and must not break equal-outcome ties.
        return int(value["wins"]) - int(value["losses"])

    if previous is None or quality(record) > quality(previous):
        temporary = checkpoint.parent / "best-selection.partial"
        shutil.copyfile(checkpoint, temporary)
        destination = checkpoint.parent / "best-selection.pt"
        temporary.replace(destination)
        write_json(
            best_path,
            {
                **record,
                "checkpoint_sha256": digest(destination),
                "source_revision": source["revision"],
            },
        )
    print(json.dumps({"phase": "selection", **record}), flush=True)


def check_metrics_resume(path: Path, previous_update: int) -> None:
    """Reject accidental appends to an unrelated or newer completed experiment."""
    import json

    last = 0
    if path.exists():
        with path.open() as stream:
            for line in stream:
                last = int(json.loads(line)["update"])
    if last not in {0, previous_update}:
        raise ValueError("output metrics do not end at the selected resume checkpoint")
