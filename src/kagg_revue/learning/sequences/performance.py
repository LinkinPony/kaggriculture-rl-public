"""Bounded hardware profiling of the final recurrent architecture, without model selection."""

import json
import time
from pathlib import Path
from typing import Any

import hydra
import numpy as np
import torch
from omegaconf import DictConfig, OmegaConf

from kagg_revue.artifacts.io import write_json
from kagg_revue.learning.adapter import runtime_settings
from kagg_revue.learning.config import Experiment
from kagg_revue.learning.initialization import random_policy
from kagg_revue.policy.contracts import ContractLayout
from kagg_revue.policy.memory.policy import MemoryPolicy
from kagg_revue.policy.spatial.model import log_probabilities


def profile(config: Experiment) -> dict[str, Any]:
    """Measure uncompiled compute scaling before choosing the compiled integration batch."""
    assert config.demonstrations is not None
    torch.set_num_threads(2)
    device = torch.device(config.device)
    torch.cuda.set_device(device)
    actor = random_policy(
        ContractLayout.resolve(runtime_settings(config)), config.seed, config.exploration
    ).to(device)
    assert isinstance(actor, MemoryPolicy)
    manifest = json.loads(config.demonstrations.manifest.read_text())
    root, record = config.demonstrations.manifest.parent, manifest["shards"][0]
    observations = torch.from_numpy(np.load(root / record["observations"])[384:432, :1].copy()).to(
        device
    )
    actions = torch.from_numpy(np.load(root / record["actions"])[384:432, :1].astype(np.int64)).to(
        device
    )
    clock = torch.arange(384, 432, device=device)
    results = []
    for batch in (8, 16, 32):
        current, targets = observations.repeat(1, batch, 1), actions.repeat(1, batch, 1)
        fields = actor.field_weights(
            targets.flatten(0, 1), clock[:, None].expand(-1, batch).flatten(), current.flatten(0, 1)
        )
        state = actor.memory.temporal.empty(batch, device)
        state.turns.copy_(torch.arange(384, device=device).repeat_interleave(4))
        durations = []
        torch.cuda.reset_peak_memory_stats(device)
        for attempt in range(5):
            actor.zero_grad(set_to_none=True)
            torch.cuda.synchronize(device)
            started = time.perf_counter()
            with torch.autocast(device.type, dtype=torch.bfloat16):
                _, logits, _ = actor.sequence(current, clock, state, targets)
                likelihood = log_probabilities(logits.flatten(0, 1), targets.flatten(0, 1))
                loss = -(likelihood * fields).sum() / fields.sum()
            loss.backward()  # type: ignore[no-untyped-call]
            torch.cuda.synchronize(device)
            if attempt:
                durations.append(time.perf_counter() - started)
        result = {
            "trajectories_per_gpu": batch,
            "rows": batch * len(clock),
            "seconds": sum(durations) / len(durations),
            "peak_allocated_bytes": torch.cuda.max_memory_allocated(device),
        }
        result["rows_per_second"] = result["rows"] / result["seconds"]
        results.append(result)
        print(json.dumps(result), flush=True)
        del current, targets, fields, state, logits, likelihood, loss
        actor.zero_grad(set_to_none=True)
    report = {
        "scope": "Eager fixed-weight BF16 forward/backward compute scaling, one 48-turn segment "
        "with a full 384-turn cache; excludes compilation, IO and collectives.",
        "results": results,
    }
    write_json(Path("outputs/analysis/gtrxl-20260916/batch-performance.json"), report)
    return report


@hydra.main(
    version_base=None, config_path="../../../../configs", config_name="learning_gtrxl_20260916"
)
def main(configuration: DictConfig) -> None:
    """Profile tensor batch sizes, without launching an architecture ablation."""
    config = Experiment.model_validate(
        OmegaConf.to_container(configuration.experiment, resolve=True)
    )
    profile(config)


if __name__ == "__main__":
    main()
