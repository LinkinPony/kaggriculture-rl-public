"""Exact-archive local budget checks through the unmodified official runner."""

import hashlib
import json
import os
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Any

import hydra
import numpy as np
from omegaconf import DictConfig, OmegaConf

from kagg_revue.artifacts.io import write_json
from kagg_revue.datasets.observations import difference
from kagg_revue.deployment.archive import unpack
from kagg_revue.deployment.check import Check, _request
from kagg_revue.deployment.liquidation import expected_action
from kagg_revue.native import _revue_core as native
from kagg_revue.native.framework import load_framework, prepare_framework


def _observations(environment: Any, engine: Any) -> list[dict[str, Any]]:
    fields = ("player", "day", "hour", "farms", "private", "market", "town")
    observations = []
    for seat in (0, 1):
        observation = environment._Environment__get_shared_state(seat).observation
        native_observation = engine.observation(seat)
        if observation["step"] != engine.step_index:
            raise ValueError("framework and native clocks differ")
        mismatch = difference(
            {key: native_observation[key] for key in fields},
            {key: observation[key] for key in fields},
        )
        if mismatch:
            raise ValueError(f"framework state differs at {engine.step_index}:{seat}: {mismatch}")
        observations.append(dict(observation))
    return observations


def check(config: Check) -> None:
    """Run separate cold one-CPU seats and let the official core consume their logs."""
    root = Path.cwd().resolve()
    config.output_dir.mkdir(parents=True, exist_ok=False)
    (root / "tmp").mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="deployment-budget-", dir=root / "tmp") as raw:
        temporary = Path(raw)
        package, framework = temporary / "package", temporary / "framework"
        package.mkdir()
        manifest = unpack(config.archive, config.sha256, package)
        profile = json.loads((package / "agent_profile.json").read_text())
        identity = prepare_framework(config.reference_directory, framework)
        core = load_framework(framework, identity["version"])
        write_json(config.output_dir / "framework.json", identity)
        records = []
        for offset in range(config.games):
            seed = config.seed + offset
            environment = core.make(
                "kaggriculture", configuration={**profile["environment"], "seed": seed}, debug=False
            )
            engine = native.Engine(seed, dict(environment.configuration))
            sessions = [
                native.ContractSession(dict(environment.configuration), profile["unit_limit"])
                for _ in (0, 1)
            ]
            features = np.empty((1, profile["observation_features"]), dtype=np.float16)
            affinity = sorted(os.sched_getaffinity(0))
            processes, streams = [], []
            times: list[list[float]] = [[], []]
            remaining: list[list[float]] = [[], []]
            trajectory = hashlib.sha256()
            started = time.perf_counter()
            try:
                for seat in (0, 1):
                    stream = (config.output_dir / f"game-{offset}-seat-{seat}.log").open("w")
                    streams.append(stream)
                    processes.append(
                        subprocess.Popen(
                            [
                                str(config.interpreter),
                                "-u",
                                str(Path(__file__).with_name("budget_worker.py")),
                                str(package),
                                str(framework),
                                identity["version"],
                                str(affinity[seat % len(affinity)]),
                            ],
                            cwd=package,
                            text=True,
                            env={
                                **os.environ,
                                "PYTHONPATH": "",
                                "PYTHONDONTWRITEBYTECODE": "1",
                                "CUDA_VISIBLE_DEVICES": "",
                                "OMP_NUM_THREADS": "1",
                            },
                            stdin=subprocess.PIPE,
                            stdout=subprocess.PIPE,
                            stderr=stream,
                        )
                    )
                for turn in range(int(profile["environment"]["episodeSteps"]) - 1):
                    observations = _observations(environment, engine)
                    actions, logs = [], []
                    for seat, process in enumerate(processes):
                        result = _request(
                            process,
                            {
                                "observation": observations[seat],
                                "configuration": dict(environment.configuration),
                            },
                            config.response_timeout,
                        )
                        if "error" in result:
                            write_json(
                                config.output_dir / "failure.json",
                                {"seed": seed, "step": turn, "seat": seat, **result},
                            )
                            raise RuntimeError(f"official Agent failed: {result['error']}")
                        log = result["log"]
                        if log["stderr"]:
                            raise RuntimeError(f"official Agent stderr: {log['stderr']}")
                        times[seat].append(log["duration"])
                        remaining[seat].append(observations[seat]["remainingOverageTime"])
                        sessions[seat].update(observations[seat])
                        sessions[seat].observe_into(features)
                        if (
                            hashlib.sha256(features.tobytes()).hexdigest()
                            != result["features_sha256"]
                        ):
                            raise ValueError("official-runner deployed features differ")
                        sessions[seat].set_program(
                            np.asarray(result["program"], dtype=np.int64), 1, profile["quantities"]
                        )
                        expected = expected_action(
                            profile,
                            observations[seat],
                            dict(environment.configuration),
                            sessions[seat].program_action(),
                        )
                        if expected != result["action"]:
                            raise ValueError("official-runner deployed action differs")
                        actions.append(result["action"])
                        logs.append(log)
                    trajectory.update(json.dumps(actions, sort_keys=True).encode())
                    environment.step(actions, logs)
                    if any(
                        state.status in {"ERROR", "INVALID", "TIMEOUT"}
                        for state in environment.state
                    ):
                        raise RuntimeError("official framework rejected the deployed agent")
                    engine.step(*actions)
                final = _observations(environment, engine)
                elapsed = time.perf_counter() - started
                if (
                    not environment.done
                    or any(state.status != "DONE" for state in environment.state)
                    or elapsed > environment.configuration.runTimeout
                ):
                    raise RuntimeError("official full game or local episode deadline failed")
                workers = [
                    _request(process, {"finish": True}, config.response_timeout)
                    for process in processes
                ]
                for worker in workers:
                    if (
                        worker["runtime"]["actor_sha256"] != profile["actor_sha256"]
                        or worker["runtime"]["last_error"] is not None
                    ):
                        raise ValueError("official worker used a different actor or failed")
                record = {
                    "seed": seed,
                    "cash": [engine.money(seat) for seat in (0, 1)],
                    "statuses": [state.status for state in environment.state],
                    "configuration": dict(environment.configuration),
                    "wall_seconds": elapsed,
                    "action_seconds": times,
                    "remaining_overage_before_action": remaining,
                    "remaining_overage_final": [obs["remainingOverageTime"] for obs in final],
                    "workers": workers,
                    "checked_observations": len(final) * (engine.step_index + 1),
                    "action_trajectory_sha256": trajectory.hexdigest(),
                }
                records.append(record)
                write_json(config.output_dir / f"game-{offset}.json", record)
            finally:
                for process in processes:
                    if process.poll() is None:
                        process.terminate()
                    process.wait()
                for stream in streams:
                    stream.close()
        write_json(
            config.output_dir / "report.json",
            {
                "configuration": config.model_dump(mode="json"),
                "archive_manifest": manifest,
                "official_framework": identity,
                "results": records,
                "scope": "Exact archive with unmodified official Agent and Environment sources. "
                "Cold PyTorch import and first inference occur inside each seat's first "
                "action timer; one CPU per seat, no visible GPU. Official remaining-overage "
                "accounting and statuses "
                "are checked locally; this is not a Kaggle-hosted resource certification.",
            },
        )


@hydra.main(
    version_base=None,
    config_path=str(Path(__file__).resolve().parents[3] / "configs"),
    config_name="deployment_budget",
)
def main(configuration: DictConfig) -> None:
    """Resolve the exact archive and official runner before the local cold-start audit."""
    check(Check.model_validate(OmegaConf.to_container(configuration.check, resolve=True)))


if __name__ == "__main__":
    main()
