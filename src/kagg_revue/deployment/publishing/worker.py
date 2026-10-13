"""Isolated CPU export plus a fresh-interpreter smoke check of the exact tar archive."""

import fcntl
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

from kagg_revue.artifacts.io import write_json
from kagg_revue.deployment.archive import unpack
from kagg_revue.deployment.bundle import build
from kagg_revue.deployment.config import Deployment
from kagg_revue.deployment.publishing.config import Publishing
from kagg_revue.deployment.publishing.metadata import describe


def smoke(archive: Path, checksum: str, interpreters: tuple[Path, ...]) -> dict[str, Any]:
    """Load the exact package in both supported ABIs and execute both initial seats."""
    from kagg_revue.native import _revue_core as native

    Path("tmp").mkdir(exist_ok=True)
    results = []
    with tempfile.TemporaryDirectory(prefix="drive-submission-", dir="tmp") as name:
        package = Path(name).resolve()
        unpack(archive, checksum, package)
        profile = json.loads((package / "agent_profile.json").read_text())
        engine = native.Engine(123456, profile["environment"])
        request = {
            "observations": [engine.observation(seat) for seat in (0, 1)],
            "environment": profile["environment"],
        }
        script = """
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd()))
import main
request = json.load(sys.stdin)
actions = [main.agent(obs, request['environment']) for obs in request['observations']]
info = main.runtime_info()
assert info['last_error'] is None, info
assert all(isinstance(action, dict) and action for action in actions)
print(json.dumps({'runtime': info, 'seats': len(actions)}))
"""
        for interpreter in interpreters:
            result = subprocess.run(
                [str(interpreter), "-c", script],
                input=json.dumps(request),
                text=True,
                capture_output=True,
                check=True,
                timeout=120,
                cwd=package,
                env={**os.environ, "PYTHONPATH": "", "PYTHONDONTWRITEBYTECODE": "1"},
            )
            results.append({"interpreter": str(interpreter), **json.loads(result.stdout)})
    return {
        "scope": "exact archive, CPU, both initial seats, every configured Python ABI",
        "results": results,
    }


def _run(job: Path) -> None:
    """Keep a completed export reusable across upload errors or service restarts."""
    specification = json.loads((job / "job.json").read_text())
    config = Publishing.model_validate(specification["configuration"])
    destination = job / "bundle"
    report_path = destination / "build-report.json"
    if report_path.is_file():
        report = json.loads(report_path.read_text())
    else:
        if destination.exists():
            shutil.rmtree(destination)  # Only an incomplete publisher-owned build attempt.
        state = json.loads((job / "input" / "state.json").read_text())
        report = build(
            Deployment(
                run=Path(specification["run"]),
                member=specification["member"],
                output_dir=destination,
                native=config.native,
                temperature=config.temperature,
            ),
            snapshot=job / "input",
            submission_info=describe(config, specification, state),
        )
    check = smoke(
        Path(report["archive"]["path"]), report["archive"]["sha256"], config.native.interpreters
    )
    write_json(job / "smoke.json", check)
    for name in ("submission-info.txt", "submission-info.json"):
        shutil.copyfile(destination / "package" / name, job / name)
    write_json(job / "ready.json", report["archive"])
    (job / "input" / "checkpoint.pt").unlink(missing_ok=True)


def run(job: Path) -> None:
    """Serialize retries even when a previous service died with a live export child."""
    with (job / "build.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        if not (job / "ready.json").is_file():
            _run(job)


if __name__ == "__main__":
    run(Path(sys.argv[1]))
