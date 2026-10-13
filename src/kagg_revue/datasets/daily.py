"""Audit recent official replay trajectories without training on their actions."""

import csv
import gzip
import io
import json
import time
import zipfile
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import Any

import hydra
import numpy as np
import orjson
from omegaconf import DictConfig, OmegaConf
from pydantic import Field, model_validator

from kagg_revue.artifacts.io import digest, write_json
from kagg_revue.bc.replay import archive_identity, daily_episode_metadata
from kagg_revue.configuration import FrozenSettings
from kagg_revue.datasets.observations import ReplayObservations, difference
from kagg_revue.native import _revue_core as backend
from kagg_revue.native.reference import OfficialGame, load_reference


class Audit(FrozenSettings):
    """One immutable daily archive and a stratified complete-trajectory audit."""

    archive: Path
    index: Path
    date: str
    output_dir: Path
    episodes: int = Field(default=64, gt=0)
    workers: int = Field(default=8, gt=0)
    module_version: str = "1.32.7"
    reference_directory: Path | None = None

    @model_validator(mode="after")
    def validate_paths(self) -> "Audit":
        """Keep reusable inputs in data/external and generated reports in outputs."""
        for path, prefix in (
            (self.archive, ("data", "external")),
            (self.index, ("data", "external")),
            (self.output_dir, ("outputs",)),
        ):
            if path.is_absolute() or ".." in path.parts or path.parts[: len(prefix)] != prefix:
                raise ValueError("audit paths must use the repository data/artifact directories")
        if self.archive.parent != self.index.parent:
            raise ValueError("daily archive and downloaded index must share their raw directory")
        if self.reference_directory is not None and (
            self.reference_directory.is_absolute()
            or ".." in self.reference_directory.parts
            or self.reference_directory.parts[:2] != ("data", "external")
        ):
            raise ValueError("official reference artifacts belong under data/external")
        return self


def audit_episode(task: tuple[str, str, str, str | None]) -> dict[str, Any]:
    """Compare public and private state at every recorded turn in both seats."""
    archive, episode_id, version, reference_directory = task
    if Path(archive).suffix == ".gz":
        raw = gzip.decompress(Path(archive).read_bytes())
    else:
        with zipfile.ZipFile(archive) as zipped:
            raw = zipped.read(f"{episode_id}.json")
    replay = orjson.loads(raw)
    configuration = replay["configuration"]
    result = {
        "episode_id": episode_id,
        "module_version": replay["module_version"],
        "seed": replay["info"]["seed"],
        "agents": replay["info"]["TeamNames"],
        "terminal_cash": [
            s["observation"]["farms"][i]["money"] for i, s in enumerate(replay["steps"][-1])
        ],
        "checked_observations": 0,
        "matched": False,
    }
    if (
        replay["module_version"] != version
        or replay["name"] != "kaggriculture"
        or len(replay["steps"]) != configuration["episodeSteps"]
        or replay["statuses"] != ["DONE", "DONE"]
    ):
        return {**result, "error": "wrong environment/version or incomplete episode"}
    engine = backend.Engine(seed=result["seed"], configuration=configuration)
    official = (
        OfficialGame(load_reference(Path(reference_directory)), configuration, result["seed"])
        if reference_directory is not None
        else None
    )
    sequences = [ReplayObservations() for _ in range(2)]
    fields = ("player", "day", "hour", "farms", "private", "market", "town")
    for step, states in enumerate(replay["steps"]):
        if step:
            engine.step(states[0]["action"], states[1]["action"])
            if official is not None:
                official.step([state["action"] for state in states])
        for seat in (0, 1):
            native = engine.observation(seat)
            expected = sequences[seat].update(states[seat]["observation"], step)
            mismatch = difference(
                {key: native[key] for key in fields}, {key: expected[key] for key in fields}
            )
            if mismatch:
                return {**result, "error": mismatch, "step": step, "seat": seat}
            if official is not None:
                reference = official.observation(seat)
                mismatch = difference(
                    {key: reference[key] for key in fields},
                    {key: expected[key] for key in fields},
                )
                if mismatch:
                    return {
                        **result,
                        "error": f"official interpreter: {mismatch}",
                        "step": step,
                        "seat": seat,
                    }
            result["checked_observations"] += 1
    return {
        **result,
        "matched": bool(engine.done),
        "reordered_inventory_frames": sum(s.reordered_inventories for s in sequences),
        "inventory_order_checked": True,
        "official_interpreter_checked": official is not None,
    }


def run(config: Audit) -> None:
    """Authenticate downloads and audit rating quantiles without extracting raw ZIPs."""
    metadata = daily_episode_metadata(config.archive)
    identity = archive_identity(config.archive)
    with zipfile.ZipFile(config.index) as index:
        rows = list(csv.DictReader(io.StringIO(index.read("manifest.csv").decode())))
    latest = max(rows, key=lambda row: row["date"])
    if latest["date"] != config.date or int(latest["episode_count"]) != len(metadata):
        raise ValueError("archive date/count must match the latest downloaded official index entry")
    manifest = {
        "schema_version": "kaggriculture-raw-archive-v1",
        "download_verified_at": time.time(),
        "source_index": {
            "path": str(config.index),
            "sha256": digest(config.index),
            "dataset_url": "https://www.kaggle.com/datasets/kaggle/kaggriculture-episodes-index",
        },
        "selection": {"dates": [config.date], "semantics": "latest complete downloaded index day"},
        "license": "CC0-1.0",
        "daily_archives": [
            {
                **identity,
                "date": config.date,
                "dataset_url": f"https://www.kaggle.com/datasets/kaggle/"
                f"kaggriculture-episodes-{config.date}",
            }
        ],
    }
    manifest_path = config.archive.parent / "manifest.json"
    if manifest_path.exists():
        previous = json.loads(manifest_path.read_text())
        if previous["daily_archives"] != manifest["daily_archives"]:
            raise ValueError("existing manifest identifies a different archive; preserve it")
    else:
        write_json(manifest_path, manifest)
    ranked = sorted(metadata, key=lambda key: float(str(metadata[key]["average_score"])))
    selected = [
        ranked[index]
        for index in np.linspace(
            0,
            len(ranked) - 1,
            min(config.episodes, len(ranked)),
            dtype=int,
        )
    ]
    results = []
    with ProcessPoolExecutor(max_workers=config.workers) as workers:
        for result in workers.map(
            audit_episode,
            [
                (
                    str(config.archive),
                    key,
                    config.module_version,
                    str(config.reference_directory) if config.reference_directory else None,
                )
                for key in selected
            ],
        ):
            results.append(result)
            print(
                json.dumps(
                    {
                        "episode": result["episode_id"],
                        "matched": result["matched"],
                        "completed": len(results),
                        "total": len(selected),
                    }
                ),
                flush=True,
            )
    names = Counter(name for result in results for name in result["agents"])
    write_json(
        config.output_dir / "report.json",
        {
            "configuration": config.model_dump(mode="json"),
            "archive_sha256": identity["sha256"],
            "native_sha256": digest(Path(backend.__file__)),
            "selection": "evenly spaced rating ranks, including minimum and maximum",
            "total_archive_episodes": len(metadata),
            "audited_episodes": len(results),
            "matched_episodes": sum(result["matched"] for result in results),
            "checked_observations": sum(result["checked_observations"] for result in results),
            "display_name_counts": names,
            "episodes": results,
            "scope": (
                "replay trajectories only; display names do not identify independent "
                "policy versions"
            ),
        },
    )
    if not all(result["matched"] for result in results):
        raise RuntimeError("native engine differs from at least one current official replay")


@hydra.main(version_base=None, config_path="../../../configs", config_name="daily_audit")
def main(configuration: DictConfig) -> None:
    """Resolve paths and fixed sample size before opening replay artifacts."""
    run(Audit.model_validate(OmegaConf.to_container(configuration.audit, resolve=True)))


if __name__ == "__main__":
    main()
