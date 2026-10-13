"""Frozen-candidate confirmation on disjoint script and neural paired panels."""

import json
from pathlib import Path
from typing import Any

import hydra
import torch
import torch.multiprocessing as mp
from omegaconf import DictConfig, OmegaConf

from kagg_revue.artifacts.io import digest, write_json
from kagg_revue.evaluation.neural import NeuralMatches
from kagg_revue.policy.checkpoints import load_policy
from kagg_revue.production.artifacts import provenance
from kagg_revue.production.config import FrozenSettings, Settings
from kagg_revue.production.evaluation import panel
from kagg_revue.production.expert.train import _comparison


class ConfirmationSettings(FrozenSettings):
    """Bind a chosen candidate before inspecting the larger confirmation population."""

    production: Settings
    candidate: Path


def _rank(rank: int, resolved: dict[str, Any]) -> None:
    config = ConfirmationSettings.model_validate(resolved)
    p = config.production
    assert p.checkpoint is not None
    device = torch.device(p.devices[rank])
    torch.cuda.set_device(device)
    torch.set_num_threads(p.cpu_threads)
    policy, unused = load_policy(p.checkpoint, torch.device("cpu"))
    del unused
    policy = policy.to(device).eval().requires_grad_(False)
    neural = None
    if rank == 1:
        opponent, unused = load_policy(p.checkpoint, torch.device("cpu"))
        del unused
        neural = NeuralMatches(p, policy, opponent.to(device).eval().requires_grad_(False))
    baseline = neural.run(p.confirmation_seed) if neural else panel(p, policy, p.confirmation_seed)
    candidate, unused = load_policy(config.candidate, torch.device("cpu"))
    policy.load_state_dict(candidate.state_dict())
    del candidate, unused
    result = neural.run(p.confirmation_seed) if neural else panel(p, policy, p.confirmation_seed)
    comparison = _comparison(result, baseline)
    write_json(
        p.output_dir / ("neural.json" if neural else "scripts.json"),
        {
            "baseline": baseline,
            "candidate": result,
            "paired": comparison,
            "peak_allocated_bytes": torch.cuda.max_memory_allocated(device),
        },
    )
    print(
        {
            "population": "neural" if neural else "scripts",
            "paired": comparison,
            "wins": result["wins"],
            "ties": result["ties"],
            "losses": result["losses"],
        },
        flush=True,
    )


@hydra.main(version_base=None, config_path="../../../../configs", config_name="production_confirm")
def main(configuration: DictConfig) -> None:
    """Run both independent population panels with their exact frozen artifacts."""
    config = ConfirmationSettings.model_validate(
        OmegaConf.to_container(configuration, resolve=True)
    )
    p = config.production
    if len(p.devices) != 2 or p.checkpoint is None:
        raise ValueError("confirmation requires two device shards and a frozen reference")
    source = provenance(p)
    if not source["clean"]:
        raise ValueError("confirmation requires a clean source revision")
    write_json(p.output_dir / "source.json", source)
    write_json(p.output_dir / "resolved-config.json", config.model_dump(mode="json"))
    mp.spawn(_rank, args=(config.model_dump(mode="json"),), nprocs=2, join=True)  # type: ignore[attr-defined, no-untyped-call]
    scripts = json.loads((p.output_dir / "scripts.json").read_text())
    neural = json.loads((p.output_dir / "neural.json").read_text())
    write_json(
        p.output_dir / "report.json",
        {
            "source": source,
            "resolved_configuration": config.model_dump(mode="json"),
            "baseline": {"path": str(p.checkpoint), "sha256": digest(p.checkpoint)},
            "candidate": {"path": str(config.candidate), "sha256": digest(config.candidate)},
            "scripts": scripts,
            "neural": neural,
            "eligible_for_training_qualification": scripts["paired"]["wdl_gain"] >= 0
            and neural["paired"]["wdl_gain"] > 0,
            "deployment_budget_qualified": False,
        },
    )


if __name__ == "__main__":
    main()
