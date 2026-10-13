"""Hydra entry point for reproducible full-population daily behavior analysis."""

from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import Any

import hydra
import numpy as np
import orjson
from omegaconf import DictConfig, OmegaConf
from pydantic import Field, model_validator

from kagg_revue.artifacts.io import digest, write_json
from kagg_revue.configuration import FrozenSettings
from kagg_revue.datasets.behavior.acquisition import acquire
from kagg_revue.datasets.behavior.extraction import extract_episode


class Survey(FrozenSettings):
    """Bound the archive window, CPU parallelism and artifact destinations."""

    raw: Path
    reuse: list[Path]
    days: int = Field(default=3, gt=0)
    workers: int = Field(default=8, gt=0)
    output: Path
    minimum_games: int = Field(default=10, ge=2)

    @model_validator(mode="after")
    def validate_paths(self) -> "Survey":
        """Keep reusable raw sources and generated analysis in their own roots."""
        for path, prefix in [
            (self.raw, ("data", "external")),
            *((path, ("data", "external")) for path in self.reuse),
            (self.output, ("outputs",)),
        ]:
            if path.is_absolute() or ".." in path.parts or path.parts[: len(prefix)] != prefix:
                raise ValueError(f"invalid analysis artifact path: {path}")
        return self


def run(config: Survey) -> None:
    """Acquire, extract once, and summarize every trajectory with a source key."""
    manifest, tasks = acquire(config.raw, config.reuse, config.days)
    config.output.mkdir(parents=True, exist_ok=True)
    write_json(config.output / "resolved-config.json", config.model_dump(mode="json"))
    write_json(config.output / "sources.json", manifest)
    source_key = {
        "archive_sha256": [row["sha256"] for row in manifest["daily_archives"]],
        "extractor_sha256": digest(Path(__file__).with_name("extraction.py")),
    }
    key_path = config.output / "extraction.json"
    rows_path = config.output / "trajectories.json"
    hashes_path = config.output / "fingerprints.npz"
    if key_path.exists() and orjson.loads(key_path.read_bytes())["source_key"] == source_key:
        cached = orjson.loads(key_path.read_bytes())
        if (
            digest(rows_path) != cached["trajectories_sha256"]
            or digest(hashes_path) != cached["fingerprints_sha256"]
        ):
            raise ValueError("cached analysis artifacts differ from their recorded hashes")
        rows = orjson.loads(rows_path.read_bytes())
        with np.load(hashes_path, allow_pickle=False) as arrays:
            hashes = arrays["hashes"]
        print(f"Reused authenticated extraction: {len(rows)} trajectories", flush=True)
    else:
        rows = []
        fingerprints = []
        with ProcessPoolExecutor(max_workers=config.workers) as pool:
            for index, result in enumerate(pool.map(extract_episode, tasks, chunksize=2), start=1):
                for row in result:
                    fingerprints.append(np.asarray(row.pop("hashes"), dtype=np.uint64))
                    rows.append(row)
                if index % 50 == 0 or index == len(tasks):
                    print(f"Extracted {index}/{len(tasks)} episodes", flush=True)
        hashes = np.asarray(fingerprints, dtype=np.uint64)
        rows_path.write_bytes(orjson.dumps(rows))
        np.savez_compressed(hashes_path, hashes=hashes)
        write_json(
            key_path,
            {
                "source_key": source_key,
                "episodes": len(tasks),
                "trajectories": len(rows),
                "action_turns": int(hashes.shape[0] * hashes.shape[1]),
                "fingerprints_sha256": digest(hashes_path),
                "trajectories_sha256": digest(rows_path),
            },
        )
    from kagg_revue.datasets.behavior.metrics import analyze

    report: dict[str, Any] = analyze(rows, hashes, config.minimum_games)
    write_json(config.output / "report.json", report)
    from kagg_revue.datasets.behavior.reporting import render

    render(report, rows, hashes, config.output)
    from kagg_revue.datasets.behavior.confirmation import confirm
    from kagg_revue.datasets.behavior.diagnostics import diagnose

    confirm(config.output, config.workers)
    diagnose(config.output)
    write_json(
        config.output / "analysis-code.json",
        {
            str(path): digest(path)
            for path in sorted(Path(__file__).parent.iterdir())
            if path.is_file()
        },
    )
    print(f"Analysis complete: {config.output / 'report.md'}", flush=True)


@hydra.main(version_base=None, config_path="../../../../configs", config_name="daily_behavior")
def main(configuration: DictConfig) -> None:
    """Resolve the immutable analysis settings before acquiring any artifacts."""
    run(Survey.model_validate(OmegaConf.to_container(configuration.survey, resolve=True)))


if __name__ == "__main__":
    main()
