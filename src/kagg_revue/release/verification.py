"""Compare sanitized submissions with their immutable originals in isolated processes."""

import hashlib
import io
import json
import os
import select
import subprocess
import tempfile
import zipfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

import hydra
from omegaconf import DictConfig, OmegaConf

from kagg_revue.configuration import FrozenSettings
from kagg_revue.release.bundle import Artifact, json_bytes, read_archive
from kagg_revue.release.redaction import PRIVATE_PATH, redact_elf


class Verification(FrozenSettings):
    """Bind the original inputs, distribution directory and local interpreter matrix."""

    directory: Path
    originals: tuple[Artifact, ...]
    interpreters: tuple[Path, ...]
    output: Path
    seed: int = 101301000


def request(process: subprocess.Popen[str], value: dict[str, Any]) -> dict[str, Any]:
    """Send one observation and bound each worker response wait."""
    assert process.stdin is not None and process.stdout is not None
    process.stdin.write(json.dumps(value) + "\n")
    process.stdin.flush()
    if not select.select([process.stdout], [], [], 60)[0]:
        raise TimeoutError("package worker did not answer")
    line = process.stdout.readline()
    if not line:
        raise RuntimeError("package worker exited before answering")
    result: dict[str, Any] = json.loads(line)
    return result


def compare_contents(original: dict[str, bytes], released: dict[str, bytes]) -> dict[str, Any]:
    """Verify every executable Python/TorchScript member and all ELF changes."""
    unchanged = 0
    with (
        zipfile.ZipFile(io.BytesIO(original["actor.pt"])) as left,
        zipfile.ZipFile(io.BytesIO(released["actor.pt"])) as right,
    ):
        if left.namelist() != right.namelist():
            raise ValueError("TorchScript archive members changed")
        for name in left.namelist():
            content = right.read(name)
            if PRIVATE_PATH.search(content.decode(errors="replace")):
                raise ValueError("private path remains in actor archive")
            if not name.endswith(".debug_pkl"):
                if left.read(name) != content:
                    raise ValueError("executable TorchScript or tensor payload changed")
                unchanged += 1
    for name, content in released.items():
        if name.endswith(".so"):
            expected, _ = redact_elf(original[name])
            if content != expected:
                raise ValueError("native binary differs beyond unused path strings")
        elif name.endswith(".py") and original[name] != content:
            raise ValueError("deployed Python source changed")
        if name != "actor.pt" and PRIVATE_PATH.search(content.decode(errors="replace")):
            raise ValueError("private path remains in submission package")
    return {"unchanged_torchscript_payload_members": unchanged, "python_source_unchanged": True}


def game(
    original: dict[str, bytes], released: dict[str, bytes], interpreter: Path, seed: int
) -> dict[str, Any]:
    """Check both seats for a complete season, including recurrent cache eviction."""
    from kagg_revue.native import _revue_core as native

    profile = json.loads(released["agent_profile.json"])
    environment = profile["environment"]
    engine = native.Engine(seed, environment)
    worker = Path(__file__).resolve().parents[1] / "deployment" / "worker.py"
    temporary_root = Path("tmp")
    temporary_root.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="release-check-", dir=temporary_root) as temporary:
        processes = []
        logs = []
        trajectory = hashlib.sha256()
        try:
            for label, files in (("original", original), ("released", released)):
                package = Path(temporary).resolve() / label
                package.mkdir()
                for name, content in files.items():
                    path = package / name
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_bytes(content)
                log = (Path(temporary) / f"{label}.log").open("w+")
                logs.append(log)
                processes.append(
                    subprocess.Popen(
                        [str(interpreter), "-u", str(worker), str(package), "file"],
                        cwd=package,
                        env={
                            **os.environ,
                            "PYTHONPATH": "",
                            "PYTHONDONTWRITEBYTECODE": "1",
                            "CUDA_VISIBLE_DEVICES": "",
                            "OMP_NUM_THREADS": "1",
                        },
                        stdin=subprocess.PIPE,
                        stdout=subprocess.PIPE,
                        stderr=log,
                        text=True,
                    )
                )
            turns = int(environment["episodeSteps"]) - 1
            for turn in range(turns):
                actions = []
                for seat in (0, 1):
                    observation = engine.observation(seat)
                    value = {"observation": observation, "configuration": environment}
                    left, right = [request(process, value) for process in processes]
                    for key in ("action", "features_sha256", "program"):
                        if left[key] != right[key]:
                            raise ValueError(f"release diverges at turn {turn}, seat {seat}: {key}")
                    actions.append(left["action"])
                trajectory.update(json.dumps(actions, sort_keys=True).encode())
                engine.step(*actions)
                if (turn + 1) % 120 == 0:
                    print(
                        json.dumps({"verified_turns": turn + 1, "total_turns": turns}), flush=True
                    )
            runtime = [request(process, {"finish": True}) for process in processes]
            if not engine.done or any(r["runtime"]["last_error"] for r in runtime):
                raise ValueError("full game did not complete cleanly")
            for process in processes:
                if process.wait(timeout=30) != 0:
                    raise RuntimeError("package worker failed after verification")
            return {
                "seed": seed,
                "turns": turns,
                "matched_seat_actions": 2 * turns,
                "trajectory_sha256": trajectory.hexdigest(),
                "terminal_cash": [engine.money(seat) for seat in (0, 1)],
                "python": runtime[1]["python_version"].split()[0],
                "torch": runtime[1]["torch_version"],
                "passed": True,
                "scope": (
                    "Original-versus-sanitized full native-engine game; "
                    "not a new Kaggle score or timing certification."
                ),
            }
        finally:
            for process in processes:
                if process.poll() is None:
                    process.terminate()
                    try:
                        process.wait(timeout=10)
                    except subprocess.TimeoutExpired:
                        process.kill()
                        process.wait()
            for log in logs:
                log.close()


@hydra.main(version_base=None, config_path=None, config_name=None)
def main(configuration: DictConfig) -> None:
    """Write a path-free verification report for the exact distribution archives."""
    config = Verification.model_validate(
        OmegaConf.to_container(configuration.verification, resolve=True)
    )
    manifest = json.loads((config.directory / "manifest.json").read_text())
    rows = {row["name"]: row for row in manifest["artifacts"]}
    reports: list[dict[str, Any]] = []
    with ThreadPoolExecutor(max_workers=4) as executor:
        pending = {}
        for artifact in config.originals:
            print(json.dumps({"verifying": artifact.name}), flush=True)
            original = read_archive(artifact.source, artifact.sha256)
            row = rows[artifact.name]
            released = read_archive(config.directory / row["filename"], row["sha256"])
            report: dict[str, Any] = {
                "name": artifact.name,
                "archive_sha256": row["sha256"],
                "structure": compare_contents(original, released),
                "games": [],
            }
            reports.append(report)
            for interpreter in config.interpreters:
                future = executor.submit(game, original, released, interpreter, config.seed)
                pending[future] = report
        for future in as_completed(pending):
            pending[future]["games"].append(future.result())
            for report in reports:
                report["games"].sort(key=lambda row: row["python"])
            config.output.parent.mkdir(parents=True, exist_ok=True)
            config.output.write_bytes(json_bytes({"schema_version": 1, "artifacts": reports}))
    print(json.dumps({"verified_artifacts": len(reports), "passed": True}))


if __name__ == "__main__":
    main()
