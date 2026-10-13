"""Hydra entry point for immutable daily collection and resumable SE analysis."""

import json
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import Any

import hydra
from omegaconf import DictConfig, OmegaConf
from pydantic import Field, model_validator

from kagg_revue.artifacts.io import digest, write_json
from kagg_revue.configuration import FrozenSettings
from kagg_revue.datasets.land.catalog import collect
from kagg_revue.datasets.land.extraction import extract
from kagg_revue.datasets.land.reporting import render


class Survey(FrozenSettings):
    """Freeze source scope and bound CPU work without allocating training GPUs."""

    root: Path = Path("data/external")
    raw: Path
    output: Path
    include_public: bool = True
    workers: int = Field(default=6, ge=1, le=32)

    @model_validator(mode="after")
    def validate_paths(self) -> "Survey":
        """Keep source inputs and generated reports in their repository domains."""
        for path, prefix in (
            (self.root, ("data", "external")),
            (self.raw, ("data", "external")),
            (self.output, ("outputs",)),
        ):
            if path.is_absolute() or ".." in path.parts or path.parts[: len(prefix)] != prefix:
                raise ValueError("use repository data/external inputs and outputs reports")
            if not path.resolve().is_relative_to(Path.cwd().resolve()):
                raise ValueError("paths must stay inside the repository")
        return self


def run(config: Survey) -> None:
    """Collect new dates, reuse inputs and checkpoint one result per episode."""
    manifest = collect(config.root, config.raw, config.include_public)
    tasks = json.loads(Path(manifest["catalog"]["path"]).read_text())
    print(
        json.dumps(
            {
                key: manifest[key]
                for key in ("daily_episodes", "local_supplement_episodes", "unique_episodes")
            }
        ),
        flush=True,
    )
    config.output.mkdir(parents=True, exist_ok=True)
    identity = {
        "catalog_sha256": manifest["catalog"]["sha256"],
        "extractor_sha256": digest(Path(__file__).with_name("extraction.py")),
    }
    identity_path = config.output / "identity.json"
    if identity_path.exists() and json.loads(identity_path.read_text()) != identity:
        raise ValueError("analysis identity differs; select a new output directory")
    write_json(identity_path, identity)
    write_json(config.output / "resolved-config.json", config.model_dump(mode="json"))
    progress = config.output / "episodes.jsonl"
    results: list[dict[str, Any]] = []
    if progress.exists():
        results = [json.loads(line) for line in progress.read_text().splitlines()]
    seen = {r["episode_id"] for r in results}
    if len(seen) != len(results) or not seen <= {t["episode_id"] for t in tasks}:
        raise ValueError("analysis progress contains duplicate or unrelated episodes")
    with ProcessPoolExecutor(max_workers=config.workers) as pool, progress.open("a") as stream:
        for result in pool.map(
            extract, [task for task in tasks if task["episode_id"] not in seen], chunksize=4
        ):
            stream.write(json.dumps(result, ensure_ascii=False) + "\n")
            stream.flush()
            results.append(result)
            if len(results) % 100 == 0 or len(results) == len(tasks):
                print(
                    json.dumps(
                        {
                            "completed": len(results),
                            "total": len(tasks),
                            "failures": sum("error" in r for r in results),
                        }
                    ),
                    flush=True,
                )
    report = render(config.output, manifest, results)
    write_json(
        config.output / "analysis-code.json",
        {str(path): digest(path) for path in sorted(Path(__file__).parent.glob("*.py"))},
    )
    print(json.dumps({"all": report["all"], "latest_daily": report["latest_daily"]}), flush=True)
    if report["failures"]:
        raise RuntimeError("some replays failed analysis; see report.json")


@hydra.main(version_base=None, config_path="../../../../configs", config_name="daily_land")
def main(configuration: DictConfig) -> None:
    """Resolve the collection and analysis configuration through Hydra."""
    run(Survey.model_validate(OmegaConf.to_container(configuration.survey, resolve=True)))


if __name__ == "__main__":
    main()
