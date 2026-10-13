"""Evaluate scheduled checkpoints of a live training run on one fixed panel."""

import json
import os
import time
from pathlib import Path
from typing import Any

import hydra
import numpy as np
from numpy.typing import NDArray
from omegaconf import DictConfig, OmegaConf
from pydantic import Field, model_validator

from kagg_revue.artifacts.io import write_json
from kagg_revue.configuration import FrozenSettings
from kagg_revue.evaluation.checkpoints import reporting
from kagg_revue.evaluation.checkpoints.panel import PanelStudy
from kagg_revue.evaluation.checkpoints.panel import run as run_panel


class Baseline(FrozenSettings):
    """A candidate of a completed panel, compared seed by seed with each checkpoint."""

    study: Path
    candidate: str


class Progress(FrozenSettings):
    """The same opponents, seeds and decoding for every scheduled checkpoint."""

    run: Path
    prefix: str
    updates: tuple[int, ...] = Field(min_length=1)
    temperature: float = Field(default=0.0, ge=0, allow_inf_nan=False)
    poll_seconds: float = Field(default=60.0, gt=0)
    window: int = Field(default=20, gt=0)
    baseline: Baseline | None = None
    study: PanelStudy

    @model_validator(mode="after")
    def validate_schedule(self) -> "Progress":
        """Require increasing positive updates and leave candidates to the schedule."""
        if (
            list(self.updates) != sorted(set(self.updates))
            or self.updates[0] <= 0
            or self.study.candidates
        ):
            raise ValueError("progress needs increasing updates and a candidate-free panel")
        return self


REPORTED = (
    "composite_score",
    "score_ci95",
    "family_scores",
    "wins",
    "draws",
    "losses",
    "mean_cash_margin",
)


def _opponents(manifest: dict[str, Any]) -> list[tuple[Any, ...]]:
    keys = ("name", "group", "checkpoint_sha256", "temperature")
    return [tuple(row.get(key) for key in keys) for row in manifest["opponents"]]


def _values(
    manifest: dict[str, Any], directory: Path, candidate: str
) -> tuple[NDArray[np.float64], list[int]]:
    rows = [row for row in reporting.read_games(directory) if row["candidate"] == candidate]
    values, _, seeds = reporting.panel_values(manifest, rows, [candidate])
    return values[0], seeds


def paired(
    baseline: Baseline, manifest: dict[str, Any], directory: Path, candidate: str
) -> dict[str, Any]:
    """Bootstrap the candidate-minus-baseline score over shared environment seeds."""
    reference = json.loads((baseline.study / "manifest.json").read_text())
    if _opponents(reference) != _opponents(manifest):
        raise ValueError("baseline panel used different opponents")
    base, base_seeds = _values(reference, baseline.study / "panel", baseline.candidate)
    own, seeds = _values(manifest, directory, candidate)
    if seeds != base_seeds:
        raise ValueError("baseline panel used different environment seeds")
    delta = own - base
    indices = np.random.default_rng(9302026).integers(len(seeds), size=(8192, len(seeds)))
    return {
        "difference": float(delta.mean()),
        "difference_ci95": np.quantile(delta[indices].mean(axis=1), [0.025, 0.975]).tolist(),
    }


def training(run: Path, update: int, window: int) -> dict[str, float | None]:
    """Mean anchor KL and non-self-play score over the updates ending at a checkpoint."""
    rows = [json.loads(line) for line in (run / "metrics.jsonl").read_text().splitlines()]
    recent = [row for row in rows if update - window < row["update"] <= update]
    kls = [row["optimization"]["reference_kl"] for row in recent]
    games = wins = 0.0
    for row in recent:
        for name, population in row["populations"].items():
            if name != "self_play":
                games += population["games"]
                wins += population["wins"] + 0.5 * population["ties"]
    return {
        "reference_kl": sum(kls) / len(kls) if kls else None,
        "pool_score": wins / games if games else None,
    }


def _await(config: Progress, update: int) -> dict[str, Any]:
    while True:
        state: dict[str, Any] = json.loads((config.run / "state.json").read_text())
        if state["completed_update"] >= update:
            return state
        status = json.loads((config.run / "run-status.json").read_text())
        if status["status"] != "running":
            raise RuntimeError(f"training ended at {state['completed_update']} before {update}")
        os.kill(status["pid"], 0)
        time.sleep(config.poll_seconds)


def _percent(value: float | None) -> str:
    return "-" if value is None else f"{100 * value:.1f}%"


def _summary(config: Progress, rows: list[dict[str, Any]]) -> str:
    families = sorted(rows[0]["family_scores"]) if rows else []
    header = ["update", "panel", "95% CI", "minus baseline", *families, "anchor KL", "pool"]
    lines = [
        f"# {config.prefix} progress at T={config.temperature:g}",
        "",
        config.study.scope,
        "",
        "| " + " | ".join(header) + " |",
        "|" + "---:|" * len(header),
    ]
    for row in rows:
        low, high = row["score_ci95"]
        base = row.get("baseline")
        shift = (
            f"{100 * base['difference']:+.1f} ({100 * base['difference_ci95'][0]:+.1f}"
            f" to {100 * base['difference_ci95'][1]:+.1f})"
            if base
            else "-"
        )
        kl = row["training"]["reference_kl"]
        cells = [
            str(row["update"]),
            _percent(row["composite_score"]),
            f"{_percent(low)}–{_percent(high)}",
            shift,
            *(_percent(row["family_scores"][name]) for name in families),
            "-" if kl is None else f"{kl:.4f}",
            _percent(row["training"]["pool_score"]),
        ]
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines) + "\n"


def track(config: Progress) -> None:
    """Panel each scheduled checkpoint once it is committed; completed updates are kept."""
    root = config.study.output
    root.mkdir(parents=True, exist_ok=True)
    write_json(root / "progress-config.json", config.model_dump(mode="json"))
    history = root / "progress.jsonl"
    rows = (
        [json.loads(line) for line in history.read_text().splitlines()] if history.exists() else []
    )
    for update in config.updates:
        if any(row["update"] == update for row in rows):
            continue
        state = _await(config, update)
        member = f"checkpoints/update-{update:06d}.pt"
        if member not in state["members"]:
            raise ValueError(f"{member} is not retained by the training run")
        name = f"{config.prefix}-u{update:06d}"
        study = PanelStudy.model_validate(
            {
                **config.study.model_dump(mode="json"),
                "output": str(root / f"u{update:06d}"),
                "candidates": [
                    {
                        "name": name,
                        "run": str(config.run),
                        "member": member,
                        "temperature": config.temperature,
                    }
                ],
            }
        )
        result = run_panel(study)["results"][0]
        manifest = json.loads((study.output / "manifest.json").read_text())
        row: dict[str, Any] = {
            "update": update,
            "member": member,
            "checkpoint_sha256": state["members"][member],
            "evaluated_at": time.time(),
            **{key: result[key] for key in REPORTED},
            "training": training(config.run, update, config.window),
        }
        if config.baseline is not None:
            row["baseline"] = {
                **config.baseline.model_dump(mode="json"),
                **paired(config.baseline, manifest, study.output / "panel", name),
            }
        rows.append(row)
        with history.open("a") as stream:
            stream.write(json.dumps(row) + "\n")
        (root / "summary.md").write_text(_summary(config, rows))
        print(json.dumps({"update": update, "composite_score": row["composite_score"]}), flush=True)


@hydra.main(
    version_base=None,
    config_path="../../../../configs",
    config_name="evaluation_progress_s101101_20260930",
)
def main(configuration: DictConfig) -> None:
    """Follow one training run until every scheduled checkpoint has been evaluated."""
    track(Progress.model_validate(OmegaConf.to_container(configuration.progress, resolve=True)))


if __name__ == "__main__":
    main()
