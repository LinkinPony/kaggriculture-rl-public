"""Re-encode frozen teacher episodes without changing labels, seats or partitions."""

import json
import multiprocessing
from concurrent.futures import ProcessPoolExecutor
from dataclasses import asdict
from pathlib import Path
from typing import Any

import hydra
from omegaconf import DictConfig, OmegaConf

from kagg_revue.artifacts.io import digest, write_json
from kagg_revue.datasets.sequences.prepare import Preparation, encode_episode
from kagg_revue.policy.contracts import ContractLayout


def reencode(config: Preparation, source: Path) -> dict[str, Any]:
    """Rebuild observations from raw replays and authenticate unchanged supervision."""
    if config.output.resolve() == source.parent.resolve():
        raise ValueError("feature migration requires a separate dataset directory")
    original = json.loads(source.read_text())
    config.output.mkdir(parents=True, exist_ok=True)
    resolved = config.model_dump(mode="json")
    identity = {**resolved, "source": str(source), "source_sha256": digest(source)}
    path = config.output / "preparation.json"
    if path.exists() and json.loads(path.read_text()) != identity:
        raise ValueError("cannot change a frozen re-encoding in place")
    write_json(path, identity)
    records = original["shards"]
    encoded = []
    with ProcessPoolExecutor(
        max_workers=config.workers, mp_context=multiprocessing.get_context("spawn")
    ) as pool:
        results = pool.map(
            encode_episode, ((resolved, row["task"]) for row in records), chunksize=1
        )
        for old, new in zip(records, results, strict=True):
            if new.get("excluded") or any(
                new[key] != old[key]
                for key in ("task", "rows", "usable_rows", "quantity_clipped_rows", "episodes")
            ):
                raise ValueError("feature migration changed teacher provenance or coverage")
            for key in ("actions", "eligible"):
                if new["hashes"][key] != old["hashes"][key]:
                    raise ValueError("feature migration changed supervision")
            encoded.append(new)
            if len(encoded) % 32 == 0:
                print(json.dumps({"encoded": len(encoded), "total": len(records)}), flush=True)
    manifest = {
        **original,
        "configuration": {**resolved, "partition": "episode-seed"},
        "layout": asdict(ContractLayout.resolve(config.geometry())),
        "shards": encoded,
        "feature_migration": {
            "source": str(source),
            "source_sha256": identity["source_sha256"],
            "labels_and_eligibility_identical": True,
            "episode_seats_and_partitions_identical": True,
        },
    }
    write_json(config.output / "manifest.json", manifest)
    return {"coverage": manifest["coverage"], "sha256": digest(config.output / "manifest.json")}


@hydra.main(version_base=None, config_path="../../../../configs", config_name="sequences_agronomy")
def main(configuration: DictConfig) -> None:
    """Resolve a separate observation version against a frozen source manifest."""
    config = Preparation.model_validate(OmegaConf.to_container(configuration.data, resolve=True))
    print(json.dumps(reencode(config, Path(configuration.source))), flush=True)


if __name__ == "__main__":
    main()
