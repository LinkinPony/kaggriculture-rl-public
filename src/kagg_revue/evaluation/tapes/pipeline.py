"""Hydra entry: freeze tapes, then replay them against every candidate package."""

import json
import os
import shutil
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import hydra
from omegaconf import DictConfig, OmegaConf

from kagg_revue.artifacts.io import digest, write_json
from kagg_revue.evaluation.tapes import runner
from kagg_revue.evaluation.tapes.config import Study
from kagg_revue.evaluation.tapes.reporting import summarize
from kagg_revue.evaluation.tapes.selection import freeze


def _runtime(study: Study) -> Path:
    """Copy the engine extension so isolated workers import it as a top-level module."""
    target = study.output / "runtime"
    copy = target / study.engine.name
    if not copy.exists():
        target.mkdir(parents=True, exist_ok=True)
        shutil.copy2(study.engine, copy)
    write_json(target / "identity.json", {"source": str(study.engine), "sha256": digest(copy)})
    return target


def _identities(study: Study) -> list[dict[str, Any]]:
    rows = []
    for candidate in study.candidates:
        main = candidate.package / "main.py"
        if not main.exists():
            raise FileNotFoundError(f"candidate package has no main.py: {candidate.package}")
        archive = candidate.package.parent / "submission.tar.gz"
        rows.append(
            {
                "label": candidate.label,
                "package": str(candidate.package),
                "submission": candidate.submission,
                "main_sha256": digest(main),
                "archive_sha256": digest(archive) if archive.exists() else None,
            }
        )
    return rows


def _tasks(study: Study, tapes: list[dict[str, Any]], runtime: Path) -> list[dict[str, Any]]:
    """Interleave candidates so partial progress stays balanced across the cohort."""
    tasks = []
    for index in range(0, len(tapes), study.chunk):
        name = f"{index // study.chunk:04d}"
        jobs = [str(Path(tape["path"]).resolve()) for tape in tapes[index : index + study.chunk]]
        for candidate in study.candidates:
            output = study.output / "results" / candidate.label / f"{name}.json"
            tasks.append(
                {
                    "label": candidate.label,
                    "name": name,
                    "package": str(candidate.package.resolve()),
                    "engine": str(runtime.resolve()),
                    "jobs": jobs,
                    "checkpoints": list(study.checkpoints),
                    "output": str(output.resolve()),
                }
            )
    return tasks


def _execute(task: dict[str, Any], timeout: int) -> str:
    output = Path(task["output"])
    if output.exists():
        return "cached"
    output.parent.mkdir(parents=True, exist_ok=True)
    path = output.with_suffix(".task.json")
    write_json(path, task)
    environment = {key: value for key, value in os.environ.items() if key != "PYTHONPATH"}
    environment |= {
        "OMP_NUM_THREADS": "1",
        "MKL_NUM_THREADS": "1",
        "OPENBLAS_NUM_THREADS": "1",
        "CUDA_VISIBLE_DEVICES": "",
    }
    with output.with_suffix(".log").open("w") as log:
        subprocess.run(
            [sys.executable, runner.__file__, str(path)],
            env=environment,
            stdout=log,
            stderr=subprocess.STDOUT,
            timeout=timeout,
            check=True,
        )
    return "done"


def run(study: Study) -> dict[str, Any]:
    """Resume from published chunks; a failed chunk is reported, never silently scored."""
    study.output.mkdir(parents=True, exist_ok=True)
    selection = json.loads(freeze(study.tapes, study.output, study.checkpoints).read_text())
    runtime = _runtime(study)
    write_json(
        study.output / "study.json",
        {"settings": study.model_dump(mode="json"), "candidates": _identities(study)},
    )
    tasks = _tasks(study, selection["tapes"], runtime)
    failures: list[dict[str, Any]] = []
    completed = 0
    with ThreadPoolExecutor(max_workers=study.workers) as pool:
        futures = {pool.submit(_execute, task, study.task_timeout): task for task in tasks}
        for future in as_completed(futures):
            task = futures[future]
            try:
                future.result()
                completed += 1
            except Exception as error:
                failures.append(
                    {"label": task["label"], "name": task["name"], "error": repr(error)}
                )
            write_json(
                study.output / "progress.json",
                {
                    "updated_utc": datetime.now(UTC).isoformat(),
                    "tasks": len(tasks),
                    "completed": completed,
                    "failures": failures,
                },
            )
    return summarize(study)


@hydra.main(version_base=None, config_path="../../../../configs", config_name="evaluation_tapes")
def main(configuration: DictConfig) -> None:
    """Run the configured tape study and print the headline table."""
    study = Study.model_validate(OmegaConf.to_container(configuration.study, resolve=True))
    report = run(study)
    print(json.dumps(report["ranking"], indent=2), flush=True)


if __name__ == "__main__":
    main()
