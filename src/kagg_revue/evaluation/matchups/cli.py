"""Run reproducible replay accounting for explicitly selected opponents."""

import json
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import Any

import hydra
from omegaconf import DictConfig, OmegaConf
from pydantic import Field

from kagg_revue.artifacts.io import write_json
from kagg_revue.configuration import FrozenSettings
from kagg_revue.evaluation.matchups.extraction import extract
from kagg_revue.evaluation.matchups.reporting import summarize


class Analysis(FrozenSettings):
    """Bind the immutable API snapshot, replay manifest and output directory."""

    manifest: Path
    output: Path
    submission_id: int
    workers: int = Field(default=4, ge=1, le=16)


def run(config: Analysis) -> None:
    """Audit every selected replay without consulting its outcome for selection."""
    manifest = json.loads(config.manifest.read_text())
    if manifest["failures"]:
        raise ValueError("replay acquisition is incomplete")
    metadata = {row["id"]: row for row in manifest["episodes"]}
    if set(metadata) != {row["episode_id"] for row in manifest["replays"]}:
        raise ValueError("downloaded episodes differ from selection")
    jobs = [{**metadata[r["episode_id"]], **r} for r in manifest["replays"]]
    write_json(config.output / "configuration.json", config.model_dump(mode="json"))
    results: list[dict[str, Any]] = []
    detailed: list[dict[str, Any]] = []
    with ProcessPoolExecutor(max_workers=config.workers) as pool:
        for result in pool.map(extract, jobs):
            write_json(config.output / f"episode-{result['episode_id']}.json", result)
            detailed.append(result)
            own = next(p for p in result["players"] if p["submission_id"] == config.submission_id)
            opp = next(p for p in result["players"] if p["submission_id"] != config.submission_id)
            row = {k: v for k, v in result.items() if k != "players"}
            row.update(
                {
                    "seat": own["seat"],
                    "opponent": opp["name"],
                    "opponent_submission": opp["submission_id"],
                    "own_cash": own["cash"][-1],
                    "opponent_cash": opp["cash"][-1],
                }
            )
            results.append(row)
            print(json.dumps(row, ensure_ascii=False), flush=True)
    write_json(config.output / "summary.json", {"episodes": results})
    summarize(detailed, config.submission_id, config.output)


@hydra.main(version_base=None, config_path="../../../../configs", config_name="matchup_analysis")
def main(configuration: DictConfig) -> None:
    """Read the replay accounting configuration through Hydra."""
    run(Analysis.model_validate(OmegaConf.to_container(configuration.analysis, resolve=True)))


if __name__ == "__main__":
    main()
