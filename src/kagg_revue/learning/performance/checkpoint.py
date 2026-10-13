"""Measure full optimizer snapshots while live CUDA weights are immediately mutated."""

import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

import hydra
import torch
from omegaconf import DictConfig

from kagg_revue.artifacts.io import digest, write_json
from kagg_revue.artifacts.serialization import save
from kagg_revue.artifacts.snapshot import Snapshot, capture


def equal(first: Any, second: Any) -> bool:
    """Compare every tensor and metadata value, including Adam, RNG, PFSP and lineage."""
    if isinstance(first, torch.Tensor):
        return isinstance(second, torch.Tensor) and torch.equal(first, second)
    if isinstance(first, dict):
        return first.keys() == second.keys() and all(equal(first[k], second[k]) for k in first)
    if isinstance(first, (tuple, list)):
        return (
            type(first) is type(second)
            and len(first) == len(second)
            and all(equal(a, b) for a, b in zip(first, second, strict=True))
        )
    return bool(first == second)


def write(snapshot: Snapshot, target: Path) -> tuple[str, float]:
    """Measure background completion after freezing all live tensors."""
    began = time.perf_counter()
    checksum = save(snapshot.wait(), target)
    return checksum, time.perf_counter() - began


@hydra.main(version_base=None, config_path="../../../../configs", config_name="checkpoint_profile")
def main(configuration: DictConfig) -> None:
    """Use a real 399 MB RL checkpoint without modifying its original file."""
    torch.set_num_threads(2)
    device = torch.device("cuda:0")
    torch.cuda.set_device(device)
    original = Path(configuration.benchmark.checkpoint)
    report = Path(configuration.benchmark.report)
    report.parent.mkdir(parents=True, exist_ok=True)
    baseline = torch.load(original, map_location="cpu", weights_only=False)
    results = []
    with ThreadPoolExecutor(max_workers=1) as pool:
        for repeat in range(2):
            live = torch.load(original, weights_only=False)
            torch.cuda.synchronize(device)
            started = time.perf_counter()
            snapshot = capture(live, device)
            snapshot_seconds = time.perf_counter() - started
            target = report.with_name(f"checkpoint-probe-{repeat}.pt")

            future = pool.submit(write, snapshot, target)
            for value in live["model"].values():
                if value.is_floating_point():
                    value.add_(100)
            checksum, background_seconds = future.result()
            elapsed = time.perf_counter() - started
            restored = torch.load(target, map_location="cpu", weights_only=False)
            matched = equal(baseline, restored)
            if not matched or digest(target) != checksum:
                raise ValueError("asynchronous save changed the frozen checkpoint")
            result = {
                "repeat": repeat,
                "snapshot_seconds": snapshot_seconds,
                "background_seconds": background_seconds,
                "total_seconds": elapsed,
                "bytes": target.stat().st_size,
                "exact_payload_after_live_mutation": matched,
                "sha256_verified": True,
            }
            results.append(result)
            print(result, flush=True)
            write_json(report, {"checkpoint": str(original), "results": results})
            target.unlink()
            del live, snapshot, restored


if __name__ == "__main__":
    main()
