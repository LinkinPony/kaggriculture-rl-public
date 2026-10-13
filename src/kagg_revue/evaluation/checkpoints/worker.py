"""Execute a resumable shard of frozen checkpoint comparisons."""

import json
import os
import time
from pathlib import Path

import hydra
import torch
from omegaconf import DictConfig, OmegaConf

from kagg_revue.artifacts.io import digest, write_json
from kagg_revue.evaluation.checkpoints.config import Options, Task
from kagg_revue.evaluation.checkpoints.runtime import Matches
from kagg_revue.native import _revue_core


@hydra.main(
    version_base=None, config_path="../../../../configs", config_name="evaluation_checkpoints"
)
def main(configuration: DictConfig) -> None:
    """Apply an allocator ceiling before CUDA initialization, then commit whole batches."""
    options = Options.model_validate(OmegaConf.to_container(configuration.comparison, resolve=True))
    if options.shard >= options.shards:
        raise ValueError("shard index exceeds worker count")
    torch.set_num_threads(2)
    torch.set_num_interop_threads(1)
    device = torch.device(options.device)
    torch.cuda.set_device(device)
    torch.cuda.set_per_process_memory_fraction(options.memory_fraction, device)
    manifest = json.loads(options.manifest.read_text())
    if digest(Path(_revue_core.__file__)) != manifest["native_sha256"]:
        raise ValueError("evaluation native engine differs from the training engine")
    tasks = [Task.model_validate(row) for row in json.loads(options.schedule.read_text())]
    if len({t.name for t in tasks}) != len(tasks):
        raise ValueError("duplicate scheduled batch")
    options.output.mkdir(parents=True, exist_ok=True)
    write_json(
        options.output / f"worker-{options.shard}-config.json", options.model_dump(mode="json")
    )
    status = options.output / f"worker-{options.shard}-status.json"
    matches: Matches | None = None
    try:
        for index, task in enumerate(tasks):
            if index % options.shards != options.shard:
                continue
            destination = options.output / "batches" / f"{task.name}.json"
            if destination.exists():
                saved = json.loads(destination.read_text())
                if saved["task"] != task.model_dump(mode="json"):
                    raise ValueError("completed batch differs from the frozen schedule")
                continue
            write_json(
                status,
                {"status": "running", "pid": os.getpid(), "task": task.name, "time": time.time()},
            )
            if matches is None:
                matches = Matches(options, manifest)
            result = matches.run(task)
            write_json(destination, result)
            print(json.dumps({k: v for k, v in result.items() if k != "games"}), flush=True)
        if matches is not None:
            matches.verify_weights()
        write_json(
            status,
            {
                "status": "complete",
                "pid": os.getpid(),
                "time": time.time(),
                "weights_unchanged": True,
            },
        )
    except Exception as error:
        write_json(
            status,
            {"status": "failed", "pid": os.getpid(), "error": repr(error), "time": time.time()},
        )
        raise
    finally:
        if matches is not None:
            matches.close()


if __name__ == "__main__":
    main()
