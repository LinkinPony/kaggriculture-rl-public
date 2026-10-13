"""Isolate native feature encoding on real replay states, excluding Python parsing."""

import hashlib
import importlib.util
import json
import os
import sys
import time
import zipfile
from pathlib import Path
from typing import Any

import hydra
import numpy as np
import orjson
from omegaconf import DictConfig, OmegaConf


@hydra.main(version_base=None, config_path="../../../../configs", config_name="encoding_profile")
def main(configuration: DictConfig) -> None:
    """Time both contracts on identical complete states with a single CPU core."""
    options = configuration.benchmark
    os.sched_setaffinity(0, {min(os.sched_getaffinity(0))})
    library = Path(options.engine).resolve()
    name = "kagg_revue.native._revue_core"
    spec = importlib.util.spec_from_file_location(name, library)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)

    from kagg_revue.artifacts.io import digest, write_json
    from kagg_revue.datasets.observations import ReplayObservations
    from kagg_revue.datasets.sequences.prepare import Preparation
    from kagg_revue.policy.contracts import ContractLayout

    manifest = json.loads(Path(options.manifest).read_text())
    settings = dict(manifest["configuration"])
    settings.pop("partition", None)
    layouts = {
        label: ContractLayout.resolve(
            Preparation.model_validate({**settings, "agronomy": flag}).geometry()
        )
        for label, flag in (("v2", False), ("v4", True))
    }
    selected = json.loads(Path(options.audit).read_text())["checked_episodes"]
    records = {row["task"]["episode_id"]: row for row in manifest["shards"]}
    totals = dict.fromkeys(layouts, 0.0)
    hashes = {label: hashlib.sha256() for label in layouts}
    samples: list[dict[str, Any]] = []
    for chosen in selected[: int(options.episodes)]:
        task = records[chosen["episode_id"]]["task"]
        with zipfile.ZipFile(task["path"]) as archive:
            replay = orjson.loads(archive.read(task["member"]))
        sequences = [ReplayObservations() for _ in range(2)]
        sessions = [
            module.ContractSession(replay["configuration"], layouts["v4"].observation.units)
            for _ in range(2)
        ]
        buffers = {
            label: np.empty((1, layout.observation.features), np.float16)
            for label, layout in layouts.items()
        }
        for step, pair in enumerate(replay["steps"][:-1]):
            for seat, state in enumerate(pair):
                sessions[seat].update(sequences[seat].update(state["observation"], step))
                if step % int(options.stride):
                    continue
                timing = {}
                for label, buffer in buffers.items():
                    sessions[seat].observe_into(buffer)
                    started = time.perf_counter()
                    for _ in range(int(options.repeats)):
                        sessions[seat].observe_into(buffer)
                    timing[label] = time.perf_counter() - started
                    totals[label] += timing[label]
                    hashes[label].update(buffer.tobytes())
                samples.append(
                    {"episode": task["episode_id"], "step": step, "seat": seat, "seconds": timing}
                )
    result = {
        "configuration": OmegaConf.to_container(options, resolve=True),
        "native_sha256": digest(library),
        "calls_per_contract": len(samples) * int(options.repeats),
        "seconds": totals,
        "observation_sha256": {label: value.hexdigest() for label, value in hashes.items()},
        "samples": samples,
    }
    write_json(Path(options.report), result)
    print(json.dumps({key: value for key, value in result.items() if key != "samples"}), flush=True)


if __name__ == "__main__":
    main()
