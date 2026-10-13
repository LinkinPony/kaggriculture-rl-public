"""Build a small independent data fixture without sharing any learned weights."""

import copy
import os
from pathlib import Path
from typing import Any

import hydra
import numpy as np
import orjson
from omegaconf import DictConfig, OmegaConf

from kagg_revue.artifacts.io import digest, write_json
from kagg_revue.learning.league.config import MEMBERS, League


def fixture(config: League, output: Path) -> League:
    """Keep two training shards per expert and fixed, small held-out partitions."""
    source = config.sources()
    views = {}
    for name in MEMBERS:
        original = Path(source["views"][name]["manifest"])
        manifest = orjson.loads(original.read_bytes())
        directory = output / name
        directory.mkdir(parents=True, exist_ok=True)
        shards = []
        coverage = {}
        for split in ("train", "selection", "confirmation"):
            records = [r for r in manifest["shards"] if r["split"] == split][
                : 2 if split == "train" else 1
            ]
            count = 0
            for record in records:
                record = copy.deepcopy(record)
                for key in record["hashes"]:
                    if key == "row_selection":
                        continue
                    target = directory / record[key]
                    if not target.exists():
                        os.link(original.parent / record[key], target)
                mask = np.load(original.parent / record["row_selection"])
                indices = np.flatnonzero(mask)
                mask[indices[1024 if split == "train" else 512 :]] = False
                path = directory / record["row_selection"]
                np.save(path, mask)
                record["hashes"]["row_selection"] = digest(path)
                record["selected_rows"] = int(mask.sum())
                count += record["selected_rows"]
                shards.append(record)
            coverage[split] = {"usable_rows": count}
        manifest.update(shards=shards, coverage=coverage, qualification_only=True)
        write_json(directory / "manifest.json", manifest)
        views[name] = {
            "manifest": str(directory / "manifest.json"),
            "sha256": digest(directory / "manifest.json"),
            "coverage": coverage,
        }
    path = output / "strata.json"
    write_json(
        path, {"views": views, "source_sha256": config.strata_sha256, "qualification_only": True}
    )
    experiment = config.experiment.model_copy(
        update={
            "output_dir": Path("outputs/learning/league-qualification-20260909-v1"),
            "seed": 63011,
            "updates": 6,
            "train_seed": 3780000000,
        }
    )
    return config.model_copy(
        update={
            "strata": path,
            "strata_sha256": digest(path),
            "experiment": experiment,
            "bc_epochs": 1,
            "bc_checkpoint_shards": 1,
        }
    )


@hydra.main(version_base=None, config_path="../../../../configs", config_name="learning_league")
def main(configuration: DictConfig) -> None:
    """Materialize a reproducible independent launch fixture for pipeline checks."""
    options: Any = OmegaConf.to_container(configuration.league, resolve=True)
    options["experiment"] = OmegaConf.to_container(configuration.experiment, resolve=True)
    config = fixture(
        League.model_validate(options), Path("outputs/datasets/league-qualification-20260909")
    )
    values = config.model_dump(mode="json")
    experiment = values.pop("experiment")
    target = Path("outputs/analysis/league-20260909/qualification.yaml")
    OmegaConf.save(
        OmegaConf.create(
            {
                "experiment": experiment,
                "league": values,
                "hydra": {
                    "job": {"chdir": False},
                    "run": {"dir": "${experiment.output_dir}/hydra"},
                    "output_subdir": None,
                },
            }
        ),
        target,
    )
    print(str(target), flush=True)


if __name__ == "__main__":
    main()
