"""Publish three disjoint-or-explicitly-overlapping views of one encoded corpus."""

import copy
import os
from collections import Counter
from pathlib import Path
from typing import Any

import hydra
import numpy as np
import orjson
from omegaconf import DictConfig, OmegaConf
from pydantic import Field, model_validator

from kagg_revue.artifacts.io import digest, write_json
from kagg_revue.configuration import FrozenSettings
from kagg_revue.datasets.strata.selection import classify

NAMES = ("a", "bc", "spataro")


class Stratification(FrozenSettings):
    """Freeze the corpus, train-only classification rule and output namespace."""

    base: Path
    survey: Path
    output: Path
    window: int = Field(default=24, gt=0)
    minimum_support: int = Field(default=3, ge=2)
    market_agreement: float = Field(default=0.9, ge=0, le=1)
    market_stability: float = Field(default=0.8, ge=0, le=1)
    specialist_name: str = "SpaTaro"

    @model_validator(mode="after")
    def validate_paths(self) -> "Stratification":
        """Require generated dataset and analysis artifacts inside outputs."""
        for path in (self.base, self.survey, self.output):
            if path.is_absolute() or ".." in path.parts or path.parts[:1] != ("outputs",):
                raise ValueError("strata must reference repository outputs")
        return self


def prepare(config: Stratification) -> dict[str, Any]:
    """Share immutable tensor files by hardlink and store only per-view row masks."""
    destination = config.output / "strata.json"
    if destination.exists():
        existing: dict[str, Any] = orjson.loads(destination.read_bytes())
        if existing["configuration"] != config.model_dump(mode="json"):
            raise ValueError("existing strata have a different protocol")
        return existing
    base = orjson.loads(config.base.read_bytes())
    integrity = orjson.loads((config.survey / "extraction.json").read_bytes())
    for filename, key in (
        ("trajectories.json", "trajectories_sha256"),
        ("fingerprints.npz", "fingerprints_sha256"),
    ):
        if digest(config.survey / filename) != integrity[key]:
            raise ValueError("survey fingerprints changed")
    rows = orjson.loads((config.survey / "trajectories.json").read_bytes())
    splits = {
        str(episode["episode_id"]): shard["split"]
        for shard in base["shards"]
        for episode in shard["episodes"]
    }
    if set(splits) != {row["episode_id"] for row in rows}:
        raise ValueError("survey and encoded corpus contain different episodes")
    with np.load(config.survey / "fingerprints.npz", allow_pickle=False) as arrays:
        a, windows = classify(
            rows,
            arrays["hashes"],
            splits,
            window=config.window,
            minimum_support=config.minimum_support,
            market_agreement=config.market_agreement,
            market_stability=config.market_stability,
        )
    indices = {(row["episode_id"], row["seat"]): index for index, row in enumerate(rows)}
    config.output.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(config.output / "window-labels.npz", a=a)
    summaries = {}
    for name in NAMES:
        directory = config.output / name
        directory.mkdir(exist_ok=True)
        shards = []
        coverage: dict[str, Any] = {}
        for split in ("train", "selection", "confirmation"):
            coverage[split] = {"usable_rows": 0, "episodes": 0, "display_name_rows": Counter()}
        for original in base["shards"]:
            shard = copy.deepcopy(original)
            origins = np.load(config.base.parent / shard["origins"], mmap_mode="r")
            covered = np.load(config.base.parent / shard["quantity_coverage"], mmap_mode="r")
            mask = np.zeros(shard["rows"], np.bool_)
            for episode in shard["episodes"]:
                start, stop = episode["row_start"], episode["row_stop"]
                for seat in (0, 1):
                    local = np.flatnonzero(origins[start:stop, 1] == seat) + start
                    trace = indices[(str(episode["episode_id"]), seat)]
                    flags = a[trace, origins[local, 0]]
                    if name == "bc":
                        flags = ~flags
                    elif name == "spataro":
                        flags = np.full(len(local), rows[trace]["name"] == config.specialist_name)
                    mask[local] = flags & covered[local]
                    coverage[shard["split"]]["display_name_rows"][rows[trace]["name"]] += int(
                        mask[local].sum()
                    )
            if not mask.any():
                continue
            for key, expected in shard["hashes"].items():
                source = config.base.parent / shard[key]
                if digest(source) != expected:
                    raise ValueError("encoded source array changed")
                target = directory / source.name
                if target.exists():
                    if not os.path.samefile(source, target):
                        raise ValueError("existing view does not share its source array")
                else:
                    os.link(source, target)
            path = directory / shard["observations"].replace(
                "-observations.npy", "-row_selection.npy"
            )
            np.save(path, mask)
            shard["row_selection"] = path.name
            shard["selected_rows"] = int(mask.sum())
            shard["hashes"]["row_selection"] = digest(path)
            shards.append(shard)
            coverage[shard["split"]]["usable_rows"] += shard["selected_rows"]
            coverage[shard["split"]]["episodes"] += sum(
                bool(mask[e["row_start"] : e["row_stop"]].any()) for e in shard["episodes"]
            )
        if not all(coverage[split]["usable_rows"] for split in coverage):
            raise ValueError(f"stratum {name} lacks a complete data partition")
        manifest = {
            **base,
            "shards": shards,
            "coverage": coverage,
            "stratum": name,
            "stratification": config.model_dump(mode="json"),
            "base_manifest_sha256": digest(config.base),
            "row_selection_required": True,
        }
        write_json(directory / "manifest.json", manifest)
        summaries[name] = {
            "manifest": str(directory / "manifest.json"),
            "sha256": digest(directory / "manifest.json"),
            "coverage": coverage,
        }
    result = {
        "configuration": config.model_dump(mode="json"),
        "base_manifest_sha256": digest(config.base),
        "survey_source_key": integrity["source_key"],
        "windows": windows,
        "views": summaries,
        "semantics": "A and B+C partition all representable rows. SpaTaro contains only its own "
        "seat and intentionally overlaps either view. Classification prototypes use train "
        "episodes only and exclude both seats of the classified episode.",
    }
    write_json(destination, result)
    return result


@hydra.main(
    version_base=None, config_path="../../../../configs", config_name="demonstration_strata"
)
def main(configuration: DictConfig) -> None:
    """Resolve and publish the frozen training strata."""
    result = prepare(
        Stratification.model_validate(OmegaConf.to_container(configuration.strata, resolve=True))
    )
    print(orjson.dumps(result["views"]).decode(), flush=True)


if __name__ == "__main__":
    main()
