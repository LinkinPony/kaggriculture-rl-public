"""Count teacher-specific market exposure in the exact BC minibatch objective."""

import json
from collections import defaultdict
from pathlib import Path
from typing import Any

import hydra
import numpy as np
from omegaconf import DictConfig, OmegaConf

from kagg_revue.artifacts.io import digest, write_json
from kagg_revue.evaluation.diagnosis.imitation import Options
from kagg_revue.evaluation.diagnosis.statistics import MARKET_NAMES


def count(options: Options) -> dict[str, Any]:
    """Count active labels and their exact domain-normalized coefficients per batch."""
    if digest(options.manifest) != options.manifest_sha256:
        raise ValueError("BC dataset manifest changed")
    manifest = json.loads(options.manifest.read_text())
    units = manifest["layout"]["observation"]["units"]
    protocol = json.loads((options.run / "resolved-config.json").read_text())
    bc_run = Path(protocol["initial_weights"]["run"])
    bc = json.loads((bc_run / "resolved-config.json").read_text())
    source = bc["demonstrations"]
    if source["sha256"] != options.manifest_sha256:
        raise ValueError("diagnostic dataset differs from the BC starting point's data")
    turns = manifest["layout"]["observation"]["turns"]
    batch_size, remainder = divmod(source["batch_rows"], turns)
    if remainder or not batch_size:
        raise ValueError("BC configuration does not contain whole trajectories")
    trajectories: dict[str, list[tuple[str, np.ndarray[Any, Any]]]] = defaultdict(list)
    for shard in manifest["shards"]:
        paths = {key: options.manifest.parent / shard[key] for key in ("actions", "eligible")}
        for key, path in paths.items():
            if digest(path) != shard["hashes"][key]:
                raise ValueError("BC labels changed")
        actions = np.load(paths["actions"], mmap_mode="r")
        eligible = np.load(paths["eligible"], mmap_mode="r")
        for index, teacher in enumerate(shard["task"]["seats"]):
            operations = actions[:, index, 8 * units :: 2]
            active = (
                np.concatenate(
                    (
                        np.ones((len(operations), 1), dtype=bool),
                        np.logical_and.accumulate(operations[:, :-1] != 0, axis=1),
                    ),
                    axis=1,
                )
                & eligible[:, index, None]
            )
            counts = np.bincount(operations[active].astype(np.int64), minlength=23)
            trajectories[shard["split"]].append((teacher["name"], counts))
    result: dict[str, Any] = {}
    # SequenceDataset.configure uses one RNG and consumes train then val permutations.
    rng = np.random.default_rng([bc["seed"], 71])
    for split in ("train", "val"):
        rows = trajectories[split]
        order = rng.permutation(len(rows))
        coefficients: dict[str, np.ndarray[Any, Any]] = defaultdict(lambda: np.zeros((2, 23)))
        exposure: dict[str, np.ndarray[Any, Any]] = defaultdict(
            lambda: np.zeros(23, dtype=np.int64)
        )
        sizes: dict[str, int] = defaultdict(int)
        batches = 0
        for start in range(0, len(rows), batch_size):
            selected = [rows[int(i)] for i in order[start : start + batch_size]]
            total = sum((entry[1] for entry in selected), np.zeros(23, dtype=np.int64))
            batches += 1
            for name, counts in selected:
                coefficients[name][0] += counts / max(1, int(total.sum()))
                quantities = counts.copy()
                quantities[[0, 1, 21, 22]] = 0
                coefficients[name][1] += quantities / max(1, int(total[2:21].sum()))
                exposure[name] += counts
                sizes[name] += 1
        result[split] = {
            "trajectories": len(rows),
            "batches": batches,
            "teachers": {
                name: {
                    "trajectories": sizes[name],
                    "counts": dict(zip(MARKET_NAMES, exposure[name].tolist(), strict=True)),
                    "market_operation_domain_share": float(coefficients[name][0].sum() / batches),
                    "market_quantity_domain_share": float(coefficients[name][1].sum() / batches),
                    "operation_coefficients": dict(
                        zip(MARKET_NAMES, (coefficients[name][0] / batches).tolist(), strict=True)
                    ),
                }
                for name in sorted(exposure)
            },
        }
    return {
        "dataset_sha256": options.manifest_sha256,
        "grouping_seed": bc["seed"],
        "trajectories_per_batch": batch_size,
        "splits": result,
        "scope": "Relative coefficients within each market domain, not gradient magnitudes. "
        "Each market domain has 1/5 of the grouped BC objective weight.",
    }


@hydra.main(version_base=None, config_path="../../../../configs", config_name="diagnosis_imitation")
def main(config: DictConfig) -> None:
    """Reuse the frozen diagnostic dataset and save its label exposure census."""
    options = Options.model_validate(OmegaConf.to_container(config.analysis, resolve=True))
    write_json(options.output / "census.json", count(options))


if __name__ == "__main__":
    main()
