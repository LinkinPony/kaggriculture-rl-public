"""Compare frozen BC and PPO actors on identical complete validation histories."""

import gc
import json
import time
from pathlib import Path
from typing import Any

import hydra
import numpy as np
import torch
from omegaconf import DictConfig, OmegaConf
from pydantic import Field

from kagg_revue.artifacts.io import digest, write_json
from kagg_revue.configuration import FrozenSettings
from kagg_revue.datasets.exclusions import validate_manifest
from kagg_revue.evaluation.diagnosis.statistics import aggregate, totals
from kagg_revue.learning.storage.artifacts import resolve
from kagg_revue.policy.checkpoints import load_policy
from kagg_revue.policy.memory.policy import MemoryPolicy


class Options(FrozenSettings):
    """Bound GPU usage and pin the input dataset and source run."""

    output: Path
    run: Path
    manifest: Path
    manifest_sha256: str
    device: str = "cuda:0"
    chunk_turns: int = Field(default=48, ge=1)
    memory_fraction: float = Field(default=0.06, gt=0, le=0.1)


def freeze(options: Options) -> dict[str, Any]:
    """Save actor-only snapshots of the BC starting point and latest complete PPO."""
    target = options.output / "snapshot.json"
    if target.exists():
        return json.loads(target.read_text())  # type: ignore[no-any-return]
    state = json.loads((options.run / "state.json").read_text())
    result: dict[str, Any] = {"run": str(options.run), "actors": {}}
    for name, member in {"bc": "initial.pt", "ppo": state["latest"]}.items():
        path = resolve(options.run, state, member)
        payload = torch.load(path, map_location="cpu", weights_only=False, mmap=True)
        saved = {
            key: payload[key]
            for key in ("model", "layout", "settings", "lineage", "update")
            if key in payload
        }
        destination = options.output / f"{name}.pt"
        torch.save(saved, destination)
        result["actors"][name] = {
            "member": member,
            "source_sha256": state["members"][member],
            "path": str(destination),
            "sha256": digest(destination),
        }
    write_json(target, result)
    return result


def arrays(root: Path, shard: dict[str, Any]) -> dict[str, np.ndarray[Any, Any]]:
    """Authenticate selected arrays before loading their full causal context."""
    result = {}
    for name in ("observations", "actions", "eligible"):
        path = (root / shard[name]).resolve()
        if not path.is_relative_to(root.resolve()) or digest(path) != shard["hashes"][name]:
            raise ValueError("validation array identity differs from the frozen manifest")
        result[name] = np.load(path, mmap_mode="r")
    return result


@torch.inference_mode()
def score(
    actor: MemoryPolicy, data: dict[str, np.ndarray[Any, Any]], seat: int, options: Options
) -> dict[str, list[float]]:
    """Recompute all history under one fixed model without updates or state resets."""
    device = next(actor.parameters()).device
    state = actor.memory.temporal.empty(1, device)
    combined: dict[str, list[float]] = {}
    turns = len(data["observations"])
    if turns != actor.layout.observation.turns:
        raise ValueError("incomplete validation trajectory")
    for start in range(0, turns, options.chunk_turns):
        stop = min(start + options.chunk_turns, turns)
        obs = torch.from_numpy(np.array(data["observations"][start:stop, seat : seat + 1])).to(
            device
        )
        chosen = torch.from_numpy(
            np.array(data["actions"][start:stop, seat : seat + 1], dtype=np.int64)
        ).to(device)
        eligible = torch.from_numpy(np.array(data["eligible"][start:stop, seat])).to(device)
        steps = torch.arange(start, stop, device=device)
        with torch.autocast(device.type, dtype=torch.bfloat16, enabled=device.type == "cuda"):
            _, logits, state = actor.sequence(obs, steps, state, chosen)
        fields = actor.field_weights(chosen[:, 0], steps, obs[:, 0]) * eligible[:, None]
        current = totals(logits[:, 0], chosen[:, 0], fields, actor.layout.observation.units)
        for key, values in current.items():
            old = combined.setdefault(key, [0.0] * len(values))
            combined[key] = [a + b for a, b in zip(old, values, strict=True)]
    return combined


@hydra.main(version_base=None, config_path="../../../../configs", config_name="diagnosis_imitation")
def main(config: DictConfig) -> None:
    """Evaluate all held-out trajectories with capped memory and retained per-game totals."""
    options = Options.model_validate(OmegaConf.to_container(config.analysis, resolve=True))
    options.output.mkdir(parents=True, exist_ok=True)
    write_json(options.output / "config.json", options.model_dump(mode="json"))
    torch.set_num_threads(2)
    if digest(options.manifest) != options.manifest_sha256:
        raise ValueError("dataset manifest identity changed")
    manifest = json.loads(options.manifest.read_text())
    validate_manifest(manifest)
    shards = [shard for shard in manifest["shards"] if shard["split"] == "val"]
    snapshot = freeze(options)
    device = torch.device(options.device)
    if device.type == "cuda":
        torch.cuda.set_device(device)
        torch.cuda.set_per_process_memory_fraction(options.memory_fraction, device)
        torch.backends.cuda.matmul.allow_bf16_reduced_precision_reduction = False
    started = time.monotonic()
    report: dict[str, Any] = {"snapshot": snapshot, "models": {}}
    for model, source in snapshot["actors"].items():
        path = Path(source["path"])
        if digest(path) != source["sha256"]:
            raise ValueError("diagnostic checkpoint changed")
        actor, payload = load_policy(path, device)
        assert isinstance(actor, MemoryPolicy)
        actor.eval()
        del payload
        rows = []
        with (options.output / f"{model}.jsonl").open("w") as stream:
            for shard in shards:
                data = arrays(options.manifest.parent, shard)
                for index, teacher in enumerate(shard["task"]["seats"]):
                    row = {
                        "episode_id": shard["task"]["episode_id"],
                        "seed": shard["task"]["seed"],
                        "teacher": teacher,
                        "hashes": shard["hashes"],
                        "totals": score(actor, data, index, options),
                    }
                    rows.append(row)
                    stream.write(json.dumps(row) + "\n")
                    stream.flush()
                    print(
                        json.dumps(
                            {
                                "model": model,
                                "trajectories": len(rows),
                                "seconds": time.monotonic() - started,
                            }
                        ),
                        flush=True,
                    )
        report["models"][model] = {
            "trajectories": len(rows),
            "all": aggregate(rows),
            "by_teacher": {
                name: aggregate([r for r in rows if r["teacher"]["name"] == name])
                for name in sorted({r["teacher"]["name"] for r in rows})
            },
        }
        write_json(options.output / "report.json", report)
        del actor
        gc.collect()
        if device.type == "cuda":
            torch.cuda.empty_cache()
    report["seconds"] = time.monotonic() - started
    write_json(options.output / "report.json", report)


if __name__ == "__main__":
    main()
