"""Bounded BC-to-self-play integration, including archived optimizer recovery."""

import json
import os
from pathlib import Path
from typing import Any

import hydra
import numpy as np
import torch
from omegaconf import DictConfig, OmegaConf

from kagg_revue.artifacts.io import digest, write_json
from kagg_revue.learning import state as artifacts
from kagg_revue.learning.adapter import runtime_settings
from kagg_revue.learning.config import Experiment
from kagg_revue.learning.performance.qualification import _training


def subset(source: Path, directory: Path) -> Path:
    """Select complete episodes for engineering checks, preserving all array hashes."""
    existing = directory / "manifest.json"
    if existing.exists():
        stored = json.loads(existing.read_text())
        if stored["qualification_source"] != {"path": str(source), "sha256": digest(source)}:
            raise ValueError("qualification subset has a different source")
        return existing
    directory.mkdir(parents=True, exist_ok=False)
    manifest = json.loads(source.read_text())
    records = []
    for split in ("train", "selection", "confirmation"):
        record = next(r for r in manifest["shards"] if r["split"] == split)
        mask = np.zeros(record["rows"], dtype=np.bool_)
        episodes = record["episodes"][:2]
        for episode in episodes:
            mask[episode["row_start"] : episode["row_stop"]] = True
        for key in record["hashes"]:
            os.link(source.parent / record[key], directory / record[key])
        path = directory / record["observations"].replace("-observations.npy", "-selection.npy")
        np.save(path, mask)
        record["row_selection"] = path.name
        record["hashes"]["row_selection"] = digest(path)
        record["episodes"] = episodes
        records.append(record)
    manifest.update(
        shards=records,
        row_selection_required=True,
        qualification_source={"path": str(source), "sha256": digest(source)},
        scope="Complete-episode engineering subset; no algorithm comparison.",
    )
    result = directory / "manifest.json"
    write_json(result, manifest)
    return result


def finite(value: Any) -> bool:
    """Check floating tensors throughout models, optimizers and saved runtime state."""
    if isinstance(value, torch.Tensor):
        return bool(torch.isfinite(value).all())
    if isinstance(value, dict):
        return all(finite(item) for item in value.values())
    if isinstance(value, (list, tuple)):
        return all(finite(item) for item in value)
    return True


def verify(directory: Path) -> dict[str, Any]:
    """Authenticate the latest full PPO checkpoint and actual self-play population."""
    state = json.loads((directory / "state.json").read_text())
    checkpoint = directory / state["latest"]
    if digest(checkpoint) != state["members"][state["latest"]]:
        raise ValueError("checkpoint hash differs from the committed run ledger")
    payload = torch.load(checkpoint, map_location="cpu", weights_only=False)
    required = {"model", "critic", "actor_optimizer", "critic_optimizer", "rng", "lineage"}
    if not required <= payload.keys() or not finite(payload):
        raise ValueError("checkpoint omits optimizer state or contains nonfinite tensors")
    workers = payload["rng"]["workers"]
    if len(workers) != 2 or torch.equal(workers[0]["cuda"], workers[1]["cuda"]):
        raise ValueError("checkpoint must preserve two distinct GPU random streams")
    protocol = state["protocol"]
    if protocol["population"]["fraction"] or protocol.get("script_population"):
        raise ValueError("training protocol is not pure self-play")
    if any(row["opponent"] is not None for row in state["records"]):
        raise ValueError("a historical opponent entered the self-play run")
    optimizer_steps = {
        key: sorted({int(v["step"]) for v in payload[key]["state"].values() if "step" in v})
        for key in ("actor_optimizer", "critic_optimizer")
    }
    return {
        "passed": True,
        "run": str(directory),
        "update": state["completed_update"],
        "checkpoint": str(checkpoint),
        "sha256": digest(checkpoint),
        "optimizer_steps": optimizer_steps,
        "finite_tensors": True,
        "distinct_rank_rng": True,
        "protocol": protocol,
        "latest_record": state["records"][-1],
    }


@hydra.main(
    version_base=None,
    config_path=str(Path(__file__).resolve().parents[4] / "configs"),
    config_name="learning_budget",
)
def main(configuration: DictConfig) -> None:
    """Use production geometry and real data, then stop and recover the isolated run."""
    base = Experiment.model_validate(OmegaConf.to_container(configuration.experiment, resolve=True))
    assert base.demonstrations is not None
    manifest = subset(base.demonstrations.manifest, Path("outputs/datasets/budget-qualification"))
    values = base.model_dump(mode="json")
    values.update(
        output_dir=str(
            configuration.get(
                "qualification_run", "outputs/learning/budget-26m-qualification-20260911"
            )
        ),
        seed=66002,
        updates=4,
        checkpoint_interval=1,
    )
    values["demonstrations"].update(
        manifest=str(manifest), sha256=digest(manifest), checkpoint_shards=1, behavior_games=2
    )
    values["population"]["snapshot_interval"] = 4
    values["evaluation"].update(interval=4, games=4)
    config = Experiment.model_validate(values)
    artifacts.create(config, runtime_settings(config))
    stopped = _training(config.output_dir, config.output_dir / "qualification-stop.log", 2)
    before = verify(config.output_dir)
    resumed = _training(
        config.output_dir, config.output_dir / "qualification-resume.log", None, archived=True
    )
    after = verify(config.output_dir)
    if after["update"] != 4 or before["update"] >= 4:
        raise ValueError("qualification did not exercise a fresh resumed update")
    write_json(
        Path("outputs/analysis/budget-20260911/qualification.json"),
        {"stopped": stopped, "before": before, "resumed": resumed, "after": after},
    )
    print(json.dumps({"phase": "qualification_passed", "update": after["update"]}), flush=True)


if __name__ == "__main__":
    main()
