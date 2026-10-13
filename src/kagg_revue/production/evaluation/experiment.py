"""Audit completed training arms against their frozen paired controls."""

import json
from pathlib import Path
from typing import Any

import hydra
import numpy as np
from omegaconf import DictConfig, OmegaConf
from pydantic import Field, model_validator

from kagg_revue.artifacts.io import digest, write_json
from kagg_revue.evaluation.comparison import paired_scores
from kagg_revue.production.config import FrozenSettings


class ComparisonSettings(FrozenSettings):
    """Explicit completed runs and a separately measured selection control."""

    output_dir: Path
    runs: dict[str, Path] = Field(min_length=2)
    baseline_selection: Path
    protocol: Path

    @model_validator(mode="after")
    def validate_paths(self) -> "ComparisonSettings":
        """Keep experiment inputs and generated reports in the artifact tree."""
        for path in (self.output_dir, self.baseline_selection, self.protocol, *self.runs.values()):
            if path.is_absolute() or ".." in path.parts or path.parts[:1] != ("outputs",):
                raise ValueError("experiment paths must stay under repository outputs/")
        return self


def _selection(path: Path) -> dict[str, Any]:
    with np.load(path) as arrays:
        return {
            "games": [
                {"seed": int(seed), "seat": int(seat), "opponent": str(name), "outcome": int(wdl)}
                for seed, seat, name, wdl in zip(
                    arrays["seeds"],
                    arrays["seats"],
                    arrays["opponents"],
                    arrays["outcomes"],
                    strict=True,
                )
            ]
        }


def compare(settings: ComparisonSettings) -> dict[str, Any]:
    """Verify terminal run artifacts before computing paired confirmation changes."""
    inputs: dict[str, str] = {}

    def read(path: Path) -> Any:
        inputs[str(path)] = digest(path)
        return json.loads(path.read_text())

    protocol = read(settings.protocol)
    baseline = read(settings.baseline_selection)
    arms = {}
    final_panels: dict[str, dict[str, dict[str, Any]]] = {}
    for name, directory in settings.runs.items():
        status = read(directory / "run-status.json")
        if status["status"] != "complete":
            raise ValueError(f"{name} has not completed; preserve and inspect its live process")
        config = read(directory / "resolved-config.json")
        training = read(directory / "training-report.json")
        if training["completed_update"] != config["ppo"]["updates"]:
            raise ValueError("training stopped before the configured comparison budget")
        final = directory / "checkpoints" / f"update-{training['completed_update']:04d}.pt"
        inputs[str(final)] = digest(final)
        metrics = directory / "metrics.jsonl"
        inputs[str(metrics)] = digest(metrics)
        records = [json.loads(line) for line in metrics.read_text().splitlines()]
        if (
            not records
            or records[-1]["update"] != training["completed_update"]
            or sum(row["physical_games"] for row in records) != training["physical_games"]
            or any(
                right["update"] != left["update"] + 1
                for left, right in zip(records, records[1:], strict=False)
            )
        ):
            raise ValueError("training metrics do not cover the declared experiment budget")
        curves = {}
        for path in sorted((directory / "selection").glob("update-*.npz")):
            inputs[str(path)] = digest(path)
            curves[path.stem] = paired_scores(baseline, _selection(path))
        confirmation = {}
        final_panels[name] = {}
        for mode, suffix in (("greedy", ""), ("sampled", "-sampled")):
            control = read(directory / f"baseline-confirmation{suffix}.json")
            candidate = read(directory / f"confirmation{suffix}.json")
            for result in (control, candidate):
                if result["sample"] != (mode == "sampled"):
                    raise ValueError("confirmation execution mode differs from the report name")
            if control.get("temperature") != candidate.get("temperature"):
                raise ValueError("paired confirmation requires matching execution temperatures")
            final_panels[name][mode] = candidate
            confirmation[mode] = {
                "control": {key: control[key] for key in ("wins", "ties", "losses")},
                "candidate": {key: candidate[key] for key in ("wins", "ties", "losses")},
                "paired": paired_scores(control, candidate),
            }
        arms[name] = {
            "directory": str(directory),
            "final_checkpoint": str(final),
            "prefix_trace_lambda": config["ppo"]["prefix_trace_lambda"],
            "physical_games": training["physical_games"],
            "official_transitions": sum(row["official_transitions"] for row in records),
            "actor_steps": sum(row["workers"][0]["optimization"]["actor_steps"] for row in records),
            "training_seconds": training["training_seconds"],
            "final_actor_learning_rate": records[-1]["actor_learning_rate"],
            "selection": curves,
            "confirmation": confirmation,
        }
    names = list(arms)
    for path in (Path(__file__), Path(__file__).with_name("comparison.py")):
        inputs[str(path.resolve().relative_to(Path.cwd()))] = digest(path)
    result = {
        "inputs_sha256": inputs,
        "protocol_limitations": protocol.get("limitations", []),
        "selection_is_exploratory": True,
        "confirmation_scope": "Final checkpoints at the predeclared budget on frozen opponents.",
        "arms": arms,
        "cross_arm_confirmation": {
            f"{right}_minus_{left}": {
                mode: paired_scores(final_panels[left][mode], final_panels[right][mode])
                for mode in ("greedy", "sampled")
            }
            for i, left in enumerate(names)
            for right in names[i + 1 :]
        },
        "quality_promotion": False,
        "deployment_budget_qualified": False,
    }
    write_json(settings.output_dir / "comparison.json", result)
    return result


@hydra.main(
    version_base=None, config_path="../../../../configs", config_name="neural_credit_comparison"
)
def main(configuration: DictConfig) -> None:
    """Write a fingerprinted report only after both planned arms have finished."""
    settings = ComparisonSettings.model_validate(
        OmegaConf.to_container(configuration, resolve=True)
    )
    result = compare(settings)
    for name, arm in result["arms"].items():
        print(name, json.dumps(arm["confirmation"]), flush=True)


if __name__ == "__main__":
    main()
