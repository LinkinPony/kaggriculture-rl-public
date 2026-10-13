"""Teacher agreement and policy entropy of a checkpoint sequence on held-out teacher play."""

import gc
import json
from pathlib import Path
from typing import Any

import hydra
import torch
from omegaconf import DictConfig, OmegaConf
from pydantic import Field

from kagg_revue.artifacts.io import digest, write_json
from kagg_revue.configuration import FrozenSettings
from kagg_revue.datasets.exclusions import validate_manifest
from kagg_revue.evaluation.diagnosis.imitation import Options as ScoreOptions
from kagg_revue.evaluation.diagnosis.imitation import arrays, score
from kagg_revue.evaluation.diagnosis.statistics import aggregate
from kagg_revue.policy.checkpoints import load_policy
from kagg_revue.policy.memory.policy import MemoryPolicy


class Checkpoint(FrozenSettings):
    """One actor file or full checkpoint, labelled by run and update."""

    name: str
    path: Path


class DriftOptions(FrozenSettings):
    """Validation teacher trajectories and the ordered checkpoints to score on them."""

    output: Path
    manifest: Path
    manifest_sha256: str
    checkpoints: tuple[Checkpoint, ...]
    device: str = "cuda:0"
    chunk_turns: int = Field(default=48, ge=1)
    memory_fraction: float = Field(default=0.06, gt=0, le=0.1)


def run(options: DriftOptions) -> dict[str, Any]:
    """Score every checkpoint on identical complete histories; resume finished ones."""
    if digest(options.manifest) != options.manifest_sha256:
        raise ValueError("dataset manifest identity changed")
    manifest = json.loads(options.manifest.read_text())
    validate_manifest(manifest)
    shards = [shard for shard in manifest["shards"] if shard["split"] == "val"]
    scoring = ScoreOptions(
        output=options.output,
        run=options.output,
        manifest=options.manifest,
        manifest_sha256=options.manifest_sha256,
        device=options.device,
        chunk_turns=options.chunk_turns,
        memory_fraction=options.memory_fraction,
    )
    device = torch.device(options.device)
    torch.cuda.set_device(device)
    torch.cuda.set_per_process_memory_fraction(options.memory_fraction, device)
    report_path = options.output / "report.json"
    report: dict[str, Any] = json.loads(report_path.read_text()) if report_path.exists() else {}
    for checkpoint in options.checkpoints:
        if checkpoint.name in report:
            continue
        actor, _ = load_policy(checkpoint.path, device)
        assert isinstance(actor, MemoryPolicy)
        actor.eval()
        rows = []
        for shard in shards:
            data = arrays(options.manifest.parent, shard)
            for index, teacher in enumerate(shard["task"]["seats"]):
                rows.append({"teacher": teacher, "totals": score(actor, data, index, scoring)})
        report[checkpoint.name] = {
            "path": str(checkpoint.path),
            "sha256": digest(checkpoint.path),
            "trajectories": len(rows),
            "all": aggregate(rows),
        }
        write_json(report_path, report)
        print(json.dumps({"checkpoint": checkpoint.name, "trajectories": len(rows)}), flush=True)
        del actor
        gc.collect()
        torch.cuda.empty_cache()
    return report


@hydra.main(version_base=None, config_path="../../../../configs", config_name="diagnosis_drift")
def main(config: DictConfig) -> None:
    """Resolve the configured checkpoint sequence and write report.json."""
    options = DriftOptions.model_validate(OmegaConf.to_container(config.analysis, resolve=True))
    options.output.mkdir(parents=True, exist_ok=True)
    torch.set_num_threads(2)
    run(options)


if __name__ == "__main__":
    main()
