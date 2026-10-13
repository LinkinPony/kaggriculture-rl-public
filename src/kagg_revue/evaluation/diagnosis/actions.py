"""Measure order-insensitive market choices without teacher action prefixes."""

import json
import time
from pathlib import Path
from typing import Any, Literal

import hydra
import numpy as np
import torch
from omegaconf import DictConfig, OmegaConf
from pydantic import Field

from kagg_revue.artifacts.io import digest, write_json
from kagg_revue.configuration import FrozenSettings
from kagg_revue.evaluation.diagnosis.imitation import arrays
from kagg_revue.evaluation.diagnosis.statistics import MARKET_NAMES
from kagg_revue.policy.checkpoints import load_policy
from kagg_revue.policy.memory.policy import MemoryPolicy


class Options(FrozenSettings):
    """Select one pinned actor for independent full-context greedy decoding."""

    output: Path
    snapshot: Path
    manifest: Path
    manifest_sha256: str
    model: Literal["bc", "ppo"]
    device: str
    chunk_turns: int = Field(default=48, ge=1)


def present(actions: np.ndarray[Any, Any], work: int) -> np.ndarray[Any, Any]:
    """Convert the active ordered market prefix to a set of operations per turn."""
    operations = actions[:, work::2]
    active = np.concatenate(
        (
            np.ones((len(operations), 1), dtype=bool),
            np.logical_and.accumulate(operations[:, :-1] != 0, axis=1),
        ),
        axis=1,
    )
    return np.asarray(((operations[..., None] == np.arange(23)) & active[..., None]).any(axis=1))


def summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Pool matched turn counts; these predictions do not advance the environment."""
    result = {}
    for name in MARKET_NAMES[2:]:
        totals = np.array([row["counts"][name] for row in rows]).sum(0)
        reference, predicted, matched = (int(value) for value in totals)
        result[name] = {
            "teacher_turns": reference,
            "predicted_turns": predicted,
            "matched_turns": matched,
            "recall": matched / reference if reference else None,
            "precision": matched / predicted if predicted else None,
        }
    return result


@hydra.main(version_base=None, config_path="../../../../configs", config_name="diagnosis_actions")
def main(config: DictConfig) -> None:
    """Decode full free actions on exactly the same observed validation histories."""
    options = Options.model_validate(OmegaConf.to_container(config.analysis, resolve=True))
    options.output.mkdir(parents=True, exist_ok=True)
    write_json(options.output / f"{options.model}-config.json", options.model_dump(mode="json"))
    if digest(options.manifest) != options.manifest_sha256:
        raise ValueError("diagnostic manifest changed")
    manifest = json.loads(options.manifest.read_text())
    snapshot = json.loads(options.snapshot.read_text())
    source = snapshot["actors"][options.model]
    if digest(Path(source["path"])) != source["sha256"]:
        raise ValueError("diagnostic checkpoint changed")
    torch.set_num_threads(2)
    device = torch.device(options.device)
    if device.type == "cuda":
        torch.cuda.set_device(device)
        torch.cuda.set_per_process_memory_fraction(0.06, device)
        torch.backends.cuda.matmul.allow_bf16_reduced_precision_reduction = False
    actor, payload = load_policy(Path(source["path"]), device)
    assert isinstance(actor, MemoryPolicy)
    actor.eval()
    del payload
    rows = []
    started = time.monotonic()
    with torch.inference_mode(), (options.output / f"{options.model}.jsonl").open("w") as stream:
        for shard in manifest["shards"]:
            if shard["split"] != "val":
                continue
            data = arrays(options.manifest.parent, shard)
            for index, teacher in enumerate(shard["task"]["seats"]):
                state = actor.memory.temporal.empty(1, device)
                pieces = []
                for start in range(0, len(data["observations"]), options.chunk_turns):
                    stop = min(start + options.chunk_turns, len(data["observations"]))
                    obs = torch.from_numpy(
                        np.array(data["observations"][start:stop, index : index + 1])
                    ).to(device)
                    steps = torch.arange(start, stop, device=device)
                    with torch.autocast(
                        device.type, dtype=torch.bfloat16, enabled=device.type == "cuda"
                    ):
                        selected, _, state = actor.sequence(
                            obs, steps, state, actions=None, sample=False
                        )
                    pieces.append(selected[:, 0].cpu().numpy())
                predicted = np.concatenate(pieces)
                eligible = data["eligible"][:, index, None]
                reference = present(data["actions"][:, index], actor.layout.work_factors) & eligible
                generated = present(predicted, actor.layout.work_factors) & eligible
                counts = np.stack(
                    (reference.sum(0), generated.sum(0), (reference & generated).sum(0)), axis=1
                )
                row = {
                    "episode_id": shard["task"]["episode_id"],
                    "seed": shard["task"]["seed"],
                    "teacher": teacher,
                    "counts": dict(zip(MARKET_NAMES, counts.tolist(), strict=True)),
                }
                rows.append(row)
                stream.write(json.dumps(row) + "\n")
                stream.flush()
                np.savez_compressed(
                    options.output / f"{options.model}-{row['episode_id']}-{teacher['seat']}.npz",
                    actions=predicted.astype(np.int16),
                )
                print(
                    json.dumps(
                        {
                            "model": options.model,
                            "trajectories": len(rows),
                            "seconds": time.monotonic() - started,
                        }
                    ),
                    flush=True,
                )
    write_json(
        options.output / f"{options.model}-report.json",
        {
            "configuration": options.model_dump(mode="json"),
            "checkpoint": source,
            "trajectories": len(rows),
            "all": summarize(rows),
            "by_teacher": {
                name: summarize([row for row in rows if row["teacher"]["name"] == name])
                for name in sorted({row["teacher"]["name"] for row in rows})
            },
            "scope": "Greedy complete actions, no teacher action prefixes, all 719 observations "
            "with full causal memory. Turn-level membership ignores order and quantity. "
            "Teacher states remain fixed: this is not an on-policy rollout or T=1 win rate.",
        },
    )


if __name__ == "__main__":
    main()
