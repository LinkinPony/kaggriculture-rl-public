"""Finish an unattended training experiment with artifact-bound paired matches."""

import json
import time
from pathlib import Path
from typing import Any

import hydra
import torch
from omegaconf import DictConfig, OmegaConf
from pydantic import Field

from kagg_revue.artifacts.io import digest, write_json
from kagg_revue.policy.checkpoints import load_policy
from kagg_revue.policy.contracts import ContractLayout
from kagg_revue.production.artifacts import provenance
from kagg_revue.production.config import FrozenSettings, Settings
from kagg_revue.production.evaluation import panel


class CompletionSettings(FrozenSettings):
    """Bind a finite training run and its reserved confirmation size."""

    production: Settings
    confirmation_games: int = Field(gt=0)
    poll_seconds: float = Field(gt=0)


def complete(configuration: CompletionSettings) -> None:
    """Wait in a companion tmux window, then evaluate sequentially on one GPU."""
    training = configuration.production
    directory = training.output_dir
    while True:
        status = json.loads((directory / "run-status.json").read_text())
        if status["status"] == "complete":
            break
        if status["status"] != "running":
            raise RuntimeError(f"training did not complete: {status}")
        time.sleep(configuration.poll_seconds)
    report = json.loads((directory / "training-report.json").read_text())
    if report["completed_update"] != training.ppo.updates:
        raise ValueError("training completion does not match the declared update budget")
    latest = directory / "checkpoints" / f"update-{training.ppo.updates:04d}.pt"
    best = directory / "checkpoints" / "best-selection.pt"
    device = torch.device(training.devices[0])
    if device.type == "cuda":
        torch.cuda.set_device(device)
    torch.set_num_threads(training.cpu_threads)
    policy, payload = load_policy(best, device)
    baseline = Path(payload["baseline_checkpoint"])
    del policy, payload
    destination = directory / "confirmation"
    if (destination / "comparison.json").exists():
        raise FileExistsError("confirmation has already completed for this run")
    results: dict[str, dict[str, Any]] = {}
    cached: dict[str, dict[str, Any]] = {}
    for name, checkpoint in (("baseline", baseline), ("best", best), ("final", latest)):
        fingerprint = digest(checkpoint)
        if fingerprint in cached:
            results[name] = cached[fingerprint]
            continue
        policy, payload = load_policy(checkpoint, device)
        values = training.model_dump(mode="json")
        values.update(
            mode="evaluate",
            checkpoint=str(checkpoint),
            output_dir=str(destination / name),
            evaluation_games=configuration.confirmation_games,
        )
        values["bc"]["greedy_prior_bias"] = payload["settings"]["bc"]["greedy_prior_bias"]
        settings = Settings.model_validate(values)
        if policy.layout != ContractLayout.resolve(settings):
            raise ValueError("confirmation profile and checkpoint semantics disagree")
        record: dict[str, Any] = {"checkpoint": {"path": str(checkpoint), "sha256": fingerprint}}
        for sample in (False, True):
            mode = "sampled" if sample else "greedy"
            mode_values = {**values, "output_dir": str(destination / name / mode)}
            mode_values["evaluation_sample"] = sample
            evaluation = Settings.model_validate(mode_values)
            source = provenance(evaluation)
            write_json(evaluation.output_dir / "source.json", source)
            write_json(
                evaluation.output_dir / "resolved-config.json", evaluation.model_dump(mode="json")
            )
            result = panel(evaluation, policy, evaluation.confirmation_seed, sample=sample)
            result["checkpoint"] = record["checkpoint"]
            write_json(evaluation.output_dir / "result.json", result)
            record[mode] = {key: value for key, value in result.items() if key != "games"}
            if name != "baseline":
                original = json.loads((destination / "baseline" / mode / "result.json").read_text())
                pairs = list(zip(result["games"], original["games"], strict=True))
                for candidate, control in pairs:
                    if any(candidate[key] != control[key] for key in ("seed", "seat", "opponent")):
                        raise ValueError("confirmation games do not form common-seed seat pairs")
                changes = [
                    candidate["outcome"] - control["outcome"] for candidate, control in pairs
                ]
                record[mode]["paired_vs_baseline"] = {
                    "better": sum(change > 0 for change in changes),
                    "same": sum(change == 0 for change in changes),
                    "worse": sum(change < 0 for change in changes),
                }
        results[name] = cached[fingerprint] = record
        print({"checkpoint": name, **record}, flush=True)
        del policy, payload
        if device.type == "cuda":
            torch.cuda.empty_cache()
    write_json(
        destination / "comparison.json",
        {"results": results, "deployment_budget_qualified": False, "automatic_promotion": False},
    )


@hydra.main(version_base=None, config_path="../../../configs", config_name="production_completion")
def main(configuration: DictConfig) -> None:
    """Resolve the companion evaluation profile once before waiting."""
    complete(CompletionSettings.model_validate(OmegaConf.to_container(configuration, resolve=True)))


if __name__ == "__main__":
    main()
