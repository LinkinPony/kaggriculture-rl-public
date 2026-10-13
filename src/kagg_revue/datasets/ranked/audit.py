"""Audit per-frame decision status in every selected raw replay."""

import gzip
import json
import multiprocessing
import zipfile
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import Any

import hydra
import orjson
from omegaconf import DictConfig, OmegaConf

from kagg_revue.artifacts.io import digest, write_json
from kagg_revue.datasets.ranked.catalog import catalog
from kagg_revue.datasets.ranked.config import Preparation


def inspect_frames(task: dict[str, Any]) -> dict[str, Any]:
    """Keep terminal status separate from the status of each source decision."""
    path = Path(task["path"])
    if task.get("member"):
        with zipfile.ZipFile(path) as archive:
            raw = archive.read(task["member"])
    else:
        raw = gzip.decompress(path.read_bytes())
    replay = orjson.loads(raw)
    inactive = [
        {"turn": turn, "seat": seat, "status": state.get("status")}
        for turn, pair in enumerate(replay["steps"][:-1])
        for seat, state in enumerate(pair)
        if state.get("status") != "ACTIVE"
    ]
    return {
        "episode_id": task["episode_id"],
        "source": task["source"],
        "selected_seats": task["seats"],
        "frames": len(replay["steps"]),
        "terminal_statuses": replay["statuses"],
        "inactive": inactive,
    }


@hydra.main(
    version_base=None, config_path="../../../../configs", config_name="demonstrations_ranked"
)
def main(configuration: DictConfig) -> None:
    """Inspect complete source trajectories without changing their training roles."""
    config = Preparation.model_validate(OmegaConf.to_container(configuration.data, resolve=True))
    path = config.report_dir / "source-catalog.json"
    if not path.exists():
        catalog(config.model_copy(update={"frame_audit": None}))
    tasks = json.loads(path.read_text())
    invalid = []
    counts: Counter[str] = Counter()
    with ProcessPoolExecutor(
        max_workers=config.workers, mp_context=multiprocessing.get_context("spawn")
    ) as pool:
        for i, result in enumerate(pool.map(inspect_frames, tasks, chunksize=8), 1):
            counts[result["source"]] += 1
            if result["inactive"]:
                invalid.append(result)
            if i % 256 == 0:
                print(
                    json.dumps({"audited": i, "invalid": len(invalid), "total": len(tasks)}),
                    flush=True,
                )
    write_json(
        config.report_dir / "raw-frames-audit.json",
        {
            "catalog": str(path),
            "catalog_sha256": digest(path),
            "episodes": len(tasks),
            "source_episodes": dict(counts),
            "invalid": invalid,
        },
    )
    print(json.dumps({"episodes": len(tasks), "invalid": len(invalid)}), flush=True)


if __name__ == "__main__":
    main()
