"""Compare initialization strengths using complete sampled paired matches."""

from typing import Any

import hydra
import torch
from omegaconf import DictConfig, OmegaConf
from pydantic import Field, NonNegativeFloat

from kagg_revue.artifacts.io import digest, write_json
from kagg_revue.policy.checkpoints import load_policy, save_policy
from kagg_revue.policy.contracts import ContractLayout
from kagg_revue.production.artifacts import provenance
from kagg_revue.production.config import FrozenSettings, Settings
from kagg_revue.production.evaluation import panel


class SweepSettings(FrozenSettings):
    """Declare initialization strengths without imposing a short-term quality gate."""

    production: Settings
    biases: tuple[NonNegativeFloat, ...] = Field(min_length=1)


def sweep(configuration: SweepSettings) -> None:
    """Weaken one frozen empirical prior without refitting or changing sampling."""
    settings = configuration.production
    if settings.checkpoint is None:
        raise ValueError("a sweep requires an explicit frozen initializer")
    if (settings.output_dir / "protocol.json").exists():
        raise FileExistsError("use a new output directory for each declared sweep")
    device = torch.device(settings.devices[0])
    if device.type == "cuda":
        torch.cuda.set_device(device)
    torch.set_num_threads(settings.cpu_threads)
    policy, checkpoint = load_policy(settings.checkpoint, device)
    if not policy.layout.work or policy.layout != ContractLayout.resolve(settings):
        raise ValueError("the initializer must match the resolved work policy")
    if checkpoint.get("epoch") != 0 or "update" in checkpoint:
        raise ValueError("bias sweeps require an untrained empirical initializer")
    source_bias = float(checkpoint["settings"]["bc"]["greedy_prior_bias"])
    biases = sorted(set(configuration.biases), reverse=True)
    if source_bias not in biases or max(biases) != source_bias:
        raise ValueError("include the frozen control and only weaker strengths")
    source = provenance(settings)
    initializer = {"path": str(settings.checkpoint), "sha256": digest(settings.checkpoint)}
    write_json(settings.output_dir / "source.json", source)
    write_json(settings.output_dir / "resolved-config.json", configuration.model_dump(mode="json"))
    write_json(
        settings.output_dir / "protocol.json",
        {
            "initializer": initializer,
            "source_bias": source_bias,
            "candidate_biases": biases,
            "decision": "characterize starting points; initial losses do not reject a run",
            "seed_start": settings.evaluation_seed,
            "games": settings.evaluation_games,
            "confirmation_seed_reserved": settings.confirmation_seed,
            "training": "only initialization changes; fresh optimizers and unchanged PPO settings",
            "promotion": "requires separate disjoint confirmation; no deployment authority",
        },
    )
    original = policy.prior.detach().clone()
    preferred = original.argmax(-1, keepdim=True)
    control_greedy = panel(settings, policy, settings.evaluation_seed)
    write_json(settings.output_dir / "control-greedy.json", control_greedy)
    results: list[dict[str, Any]] = []
    for bias in biases:
        destination = settings.output_dir / f"bias-{bias:g}"
        resolved = settings.model_dump(mode="json")
        resolved["output_dir"] = str(destination)
        resolved["bc"]["greedy_prior_bias"] = bias
        candidate = Settings.model_validate(resolved)
        candidate_source = {**source, "profile": candidate.model_dump(mode="json")}
        with torch.no_grad():
            policy.prior.copy_(original)
            policy.prior.scatter_add_(
                -1, preferred, torch.full_like(preferred, bias - source_bias, dtype=original.dtype)
            )
        path = destination / "initial.pt"
        save_policy(
            path,
            policy,
            candidate,
            epoch=0,
            parent=initializer,
            provenance=candidate_source,
            baseline_checkpoint=str(settings.checkpoint),
        )
        result = panel(candidate, policy, settings.evaluation_seed, sample=True)
        result["checkpoint"] = {"path": str(path), "sha256": digest(path)}
        write_json(destination / "sampled-selection.json", result)
        write_json(destination / "source.json", candidate_source)
        write_json(destination / "resolved-config.json", candidate.model_dump(mode="json"))
        record = {"bias": bias, **{key: value for key, value in result.items() if key != "games"}}
        results.append(record)
        print(record, flush=True)
    write_json(
        settings.output_dir / "comparison.json",
        {"results": results},
    )


@hydra.main(version_base=None, config_path="../../../configs", config_name="production_exploration")
def main(configuration: DictConfig) -> None:
    """Resolve the declared experiment before running any matches."""
    sweep(SweepSettings.model_validate(OmegaConf.to_container(configuration, resolve=True)))


if __name__ == "__main__":
    main()
