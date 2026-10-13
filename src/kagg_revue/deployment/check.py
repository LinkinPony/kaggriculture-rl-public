"""Qualify the exact portable archive using isolated CPU processes and official games."""

import hashlib
import json
import os
import select
import subprocess
import tempfile
from pathlib import Path
from typing import Any

import hydra
import numpy as np
from omegaconf import DictConfig, OmegaConf
from pydantic import Field, model_validator

from kagg_revue.artifacts.io import write_json
from kagg_revue.configuration import FrozenSettings
from kagg_revue.deployment.archive import unpack
from kagg_revue.deployment.liquidation import expected_action
from kagg_revue.native import _revue_core as native
from kagg_revue.native.comparison import MirrorReference


class Check(FrozenSettings):
    """An exact archive, target interpreter and reserved official complete-game seeds."""

    archive: Path
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    interpreter: Path
    output_dir: Path
    reference_directory: Path
    seed: int = Field(default=1220000000, ge=0)
    games: int = Field(default=2, gt=0)
    response_timeout: float = Field(default=60, gt=0, le=60)

    @model_validator(mode="after")
    def validate_paths(self) -> "Check":
        """Keep persistent artifacts and temporary executable extraction under the repo."""
        for path, prefix in (
            (self.archive, ("outputs", "deployment")),
            (self.output_dir, ("outputs", "analysis")),
            (self.reference_directory, ("data", "external")),
        ):
            if path.is_absolute() or ".." in path.parts or path.parts[:2] != prefix:
                raise ValueError("archive qualification path has the wrong artifact role")
        return self


def _request(process: subprocess.Popen[str], request: dict[str, Any], timeout: float) -> Any:
    assert process.stdin is not None and process.stdout is not None
    process.stdin.write(json.dumps(request) + "\n")
    process.stdin.flush()
    if not select.select([process.stdout], [], [], timeout)[0]:
        raise TimeoutError("deployment worker did not answer within the declared time")
    line = process.stdout.readline()
    if not line:
        raise RuntimeError("deployment worker exited; inspect its stderr log")
    return json.loads(line)


def check(config: Check) -> None:
    """Compare deployed features/actions and full official/native states every turn."""
    root = Path.cwd().resolve()
    config.output_dir.mkdir(parents=True, exist_ok=False)
    (root / "tmp").mkdir(exist_ok=True)
    records = []
    with tempfile.TemporaryDirectory(prefix="deployment-check-", dir=root / "tmp") as raw:
        package = Path(raw)
        manifest = unpack(config.archive, config.sha256, package)
        profile = json.loads((package / "agent_profile.json").read_text())
        for offset in range(config.games):
            seed = config.seed + offset
            reference = MirrorReference(config.reference_directory, profile["environment"], [seed])
            engine = native.Engine(seed, profile["environment"])
            sessions = [
                native.ContractSession(profile["environment"], profile["unit_limit"])
                for _ in (0, 1)
            ]
            features = np.empty((1, profile["observation_features"]), dtype=np.float16)
            processes, logs = [], []
            times: list[list[float]] = [[], []]
            trajectory = hashlib.sha256()
            try:
                for seat, mode in enumerate(("file", "raw")):
                    log = (config.output_dir / f"game-{offset}-seat-{seat}.log").open("w")
                    logs.append(log)
                    processes.append(
                        subprocess.Popen(
                            [
                                str(config.interpreter),
                                "-u",
                                str(Path(__file__).with_name("worker.py")),
                                str(package),
                                mode,
                            ],
                            cwd=package,
                            text=True,
                            env={**os.environ, "PYTHONPATH": "", "PYTHONDONTWRITEBYTECODE": "1"},
                            stdin=subprocess.PIPE,
                            stdout=subprocess.PIPE,
                            stderr=log,
                        )
                    )
                for turn in range(int(profile["environment"]["episodeSteps"]) - 1):
                    observations = reference.observations([engine])
                    actions = []
                    for seat, process in enumerate(processes):
                        result = _request(
                            process,
                            {
                                "observation": observations[seat],
                                "configuration": profile["environment"],
                            },
                            config.response_timeout,
                        )
                        times[seat].append(result["seconds"])
                        session = sessions[seat]
                        session.update(observations[seat])
                        session.observe_into(features)
                        if (
                            hashlib.sha256(features.tobytes()).hexdigest()
                            != result["features_sha256"]
                        ):
                            raise ValueError(f"portable features differ at {seed}:{turn}:{seat}")
                        session.set_program(
                            np.asarray(result["program"], dtype=np.int64), 1, profile["quantities"]
                        )
                        expected = expected_action(
                            profile,
                            observations[seat],
                            profile["environment"],
                            session.program_action(),
                        )
                        if expected != result["action"]:
                            raise ValueError(f"portable action differs at {seed}:{turn}:{seat}")
                        actions.append(result["action"])
                    trajectory.update(json.dumps(actions, sort_keys=True).encode())
                    engine.step(*actions)
                    reference.games[0].step(actions)
                reference.observations([engine])
                workers = [
                    _request(p, {"finish": True}, config.response_timeout) for p in processes
                ]
                for worker in workers:
                    if worker["runtime"]["actor_sha256"] != profile["actor_sha256"]:
                        raise ValueError("worker loaded a different actor")
                    if worker["runtime"]["last_error"] is not None or any(
                        name.startswith(
                            (
                                "kagg_revue.production",
                                "kagg_revue.learning",
                                "kagg_revue.teacher",
                                "kagg_revue.opponents",
                            )
                        )
                        for name in worker["modules"]
                    ):
                        raise ValueError("worker has an error or imports a training workflow")
                records.append(
                    {
                        "seed": seed,
                        "official_reference": reference.report(),
                        "cash": [engine.money(seat) for seat in (0, 1)],
                        "workers": workers,
                        "action_seconds": times,
                        "action_trajectory_sha256": trajectory.hexdigest(),
                    }
                )
            finally:
                for process in processes:
                    if process.poll() is None:
                        process.terminate()
                    process.wait()
                for log in logs:
                    log.close()
    write_json(
        config.output_dir / "report.json",
        {
            "configuration": config.model_dump(mode="json"),
            "archive_manifest": manifest,
            "results": records,
            "scope": "Exact archive, isolated target-Python CPU workers, both normal and raw entry "
            "execution. All feature arrays, decoded actions and official states checked. "
            "Local CPU timing is not a Kaggle-hosted runtime certification.",
        },
    )


@hydra.main(
    version_base=None,
    config_path=str(Path(__file__).resolve().parents[3] / "configs"),
    config_name="deployment_check",
)
def main(configuration: DictConfig) -> None:
    """Resolve the exact archive identity before executing any packaged code."""
    check(Check.model_validate(OmegaConf.to_container(configuration.check, resolve=True)))


if __name__ == "__main__":
    main()
