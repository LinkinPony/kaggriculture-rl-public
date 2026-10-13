"""Exact-archive smoke validation runnable locally and as a Kaggle script."""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import shutil
import subprocess
import sys
import sysconfig
import tarfile
import time
import traceback
from collections.abc import Callable, Mapping, Sequence
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath
from types import ModuleType
from typing import Any, cast

_REPORT_PROTOCOL = "TURN-POLICY-KAGGLE-VALIDATION-v1"
_ENVIRONMENT_VERSION = "1.32.7"
_SUBMISSION_LIMIT_BYTES = 100_000_000


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(8 * 1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise TypeError(f"expected a JSON object: {path}")
    return cast(dict[str, Any], value)


def _archive_from_inputs() -> Path:
    matches = sorted(
        {
            *Path("/kaggle/input").rglob("submission.tar.gz"),
            *Path("/kaggle/input").rglob("submission.tar.gz.bin"),
        }
    )
    if len(matches) != 1:
        raise RuntimeError(f"expected one exact submission archive input, found {matches}")
    return matches[0]


def _inspect_archive(archive_path: Path) -> tuple[dict[str, Any], list[dict[str, object]]]:
    if archive_path.stat().st_size >= _SUBMISSION_LIMIT_BYTES:
        raise ValueError("submission archive exceeds the competition byte limit")
    with tarfile.open(archive_path, "r:gz") as archive:
        members = archive.getmembers()
        names = [member.name for member in members]
        if len(names) != len(set(names)):
            raise ValueError("submission archive contains duplicate members")
        contents: dict[str, bytes] = {}
        for member in members:
            relative = PurePosixPath(member.name)
            if relative.is_absolute() or ".." in relative.parts:
                raise ValueError(f"unsafe submission archive member: {member.name}")
            if not member.isfile() and not member.isdir():
                raise ValueError(f"unsupported submission archive member: {member.name}")
            if member.isfile():
                stream = archive.extractfile(member)
                if stream is None:
                    raise RuntimeError(f"cannot read submission member: {member.name}")
                contents[member.name] = stream.read()
    manifest_bytes = contents.pop("manifest.json", None)
    if manifest_bytes is None:
        raise ValueError("submission archive has no manifest.json")
    manifest_value = json.loads(manifest_bytes)
    if not isinstance(manifest_value, dict):
        raise TypeError("submission manifest must be a mapping")
    manifest = cast(dict[str, Any], manifest_value)
    if manifest.get("schema_version") not in {
        "turn-policy-kaggle-submission-v1",
        "entity-policy-kaggle-submission-v1",
    }:
        raise ValueError("unsupported submission manifest")
    if manifest.get("worktree_dirty") is not False or manifest.get("probe_scaffold") is not False:
        raise ValueError("submission was not built from clean production source")
    actual_files = sorted(
        (
            {
                "path": name,
                "sha256": hashlib.sha256(content).hexdigest(),
                "size_bytes": len(content),
            }
            for name, content in contents.items()
        ),
        key=lambda row: str(row["path"]),
    )
    declared = manifest.get("files")
    if (
        not isinstance(declared, list)
        or sorted(declared, key=lambda row: str(row.get("path", ""))) != actual_files
    ):
        raise ValueError("submission members differ from the embedded file manifest")
    actor = manifest.get("actor_artifact")
    if not isinstance(actor, dict):
        raise TypeError("submission manifest lacks its actor artifact")
    actor_content = contents.get(str(actor.get("archive_path", "")))
    if actor_content is None or hashlib.sha256(actor_content).hexdigest() != actor.get("sha256"):
        raise ValueError("submission actor artifact identity is invalid")
    abi = str(sysconfig.get_config_var("SOABI"))
    native_records = manifest.get("native_binaries")
    if not isinstance(native_records, list):
        raise TypeError("submission manifest lacks native binary identities")
    matching = [
        record
        for record in native_records
        if isinstance(record, dict) and record.get("python_abi") == abi
    ]
    if len(matching) != 1:
        raise ValueError(f"submission has no unique native binary for {abi}")
    native = cast(dict[str, Any], matching[0])
    native_content = contents.get(str(native.get("archive_path", "")))
    if (
        native_content is None
        or len(native_content) != int(native.get("size_bytes", -1))
        or hashlib.sha256(native_content).hexdigest() != native.get("sha256")
    ):
        raise ValueError("submission native binary identity is invalid")
    return manifest, actual_files


def _extract(archive_path: Path, destination: Path) -> None:
    destination.mkdir(parents=True, exist_ok=False)
    with tarfile.open(archive_path, "r:gz") as archive:
        archive.extractall(destination, filter="data")


def _load_entrypoint(root: Path) -> ModuleType:
    path = root / "main.py"
    code = compile(path.read_text(encoding="utf-8"), str(path), "exec")
    environment: dict[str, Any] = {}
    original_sys_path = sys.path.copy()
    try:
        sys.path.append(str(root))
        exec(code, environment)  # noqa: S102
    finally:
        sys.path[:] = original_sys_path
    agent = environment.get("agent")
    if not callable(agent):
        raise AttributeError("submission main.py has no callable agent")
    callables = [value for value in environment.values() if callable(value)]
    if not callables or callables[-1] is not agent:
        raise RuntimeError("submission agent is not the final callable in main.py")
    module = ModuleType("_exact_turn_policy_submission")
    module.__dict__.update(environment)
    return module


def _state_value(state: Any, name: str) -> Any:
    if isinstance(state, Mapping):
        return state.get(name)
    return getattr(state, name)


def _observation_value(state: Any, name: str) -> Any:
    observation = _state_value(state, "observation")
    return _state_value(observation, name)


def _as_int(value: object, name: str) -> int:
    if not isinstance(value, int | float) or isinstance(value, bool):
        raise TypeError(f"{name} must be numeric")
    return int(value)


def _as_float(value: object, name: str) -> float:
    if not isinstance(value, int | float) or isinstance(value, bool):
        raise TypeError(f"{name} must be numeric")
    return float(value)


def _non_pass(action: Mapping[str, Any]) -> bool:
    farmer = action.get("farmer", ["PASS"])
    hands = action.get("hands", [])
    market = action.get("market", [])
    farmer_active = isinstance(farmer, Sequence) and bool(farmer) and farmer[0] != "PASS"
    hands_active = (
        any(isinstance(item, Sequence) and bool(item) and item[0] != "PASS" for item in hands)
        if isinstance(hands, Sequence)
        else False
    )
    return farmer_active or hands_active or bool(market)


def _smoke_seat(
    module: ModuleType,
    configuration: dict[str, Any],
    candidate_seat: int,
) -> dict[str, object]:
    make = importlib.import_module("kaggle_environments").make

    raw_agent = cast(Callable[[Any, Any], Mapping[str, Any]], module.agent)
    action_digest = hashlib.sha256()
    action_calls = 0
    non_pass_turns = 0
    total_seconds = 0.0
    maximum_seconds = 0.0

    def candidate(observation: Any, runtime_configuration: Any) -> dict[str, Any]:
        nonlocal action_calls, non_pass_turns, total_seconds, maximum_seconds
        started = time.perf_counter()
        raw_action = raw_agent(observation, runtime_configuration)
        elapsed = time.perf_counter() - started
        if not isinstance(raw_action, Mapping):
            raise TypeError("submission agent returned a non-mapping action")
        action = {str(key): value for key, value in raw_action.items()}
        encoded = json.dumps(action, sort_keys=True, separators=(",", ":")).encode()
        action_digest.update(len(encoded).to_bytes(4, "little"))
        action_digest.update(encoded)
        action_calls += 1
        non_pass_turns += int(_non_pass(action))
        total_seconds += elapsed
        maximum_seconds = max(maximum_seconds, elapsed)
        return action

    agents: list[Any] = ["pass", "pass"]
    agents[candidate_seat] = candidate
    environment = make("kaggriculture", configuration=configuration, debug=True)
    environment.run(agents)
    initial = environment.steps[0]
    final = environment.steps[-1]
    runtime_info = module.runtime_info()
    if not isinstance(runtime_info, Mapping):
        raise TypeError("submission runtime info must be a mapping")
    resolved = dict(environment.configuration)
    return {
        "candidate_seat": candidate_seat,
        "statuses": [str(_state_value(state, "status")) for state in final],
        "rewards": [float(_state_value(state, "reward")) for state in final],
        "action_calls": action_calls,
        "non_pass_turns": non_pass_turns,
        "action_sha256": action_digest.hexdigest(),
        "total_action_seconds": total_seconds,
        "max_action_seconds": maximum_seconds,
        "initial_overage_seconds": float(
            _observation_value(initial[candidate_seat], "remainingOverageTime")
        ),
        "ending_overage_seconds": float(
            _observation_value(final[candidate_seat], "remainingOverageTime")
        ),
        "resolved_environment": resolved,
        "runtime": dict(runtime_info),
    }


def _install_environment(dependency_root: Path) -> str:
    dependency_root.mkdir(parents=True, exist_ok=True)
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "pip",
            "install",
            "--disable-pip-version-check",
            "--no-deps",
            "--target",
            str(dependency_root),
            f"kaggle-environments=={_ENVIRONMENT_VERSION}",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    sys.path.insert(0, str(dependency_root))
    return completed.stdout + completed.stderr


def validate_archive(
    archive_path: Path,
    output_dir: Path,
    work_root: Path,
    *,
    seed: int,
    act_timeout_seconds: float,
    remaining_overage_seconds: float,
    run_timeout_seconds: float,
    install_environment: bool,
) -> dict[str, object]:
    """Validate identities and run both seats for a complete official season."""
    archive_path = archive_path.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    if work_root.exists():
        raise FileExistsError(f"validation work directory already exists: {work_root}")
    report: dict[str, object] = {
        "protocol": _REPORT_PROTOCOL,
        "status": "failed",
        "generated_at": datetime.now(UTC).isoformat(),
        "archive": {
            "path": str(archive_path),
            "sha256": _sha256(archive_path),
            "size_bytes": archive_path.stat().st_size,
        },
        "runtime": {
            "python": sys.version,
            "python_abi": str(sysconfig.get_config_var("SOABI")),
        },
    }
    try:
        manifest, files = _inspect_archive(archive_path)
        dependency_output = ""
        if install_environment:
            dependency_output = _install_environment(work_root / "dependencies")
        environment_version = importlib.metadata.version("kaggle-environments")
        if environment_version != _ENVIRONMENT_VERSION:
            raise RuntimeError(
                "validation kaggle-environments version mismatch: "
                f"expected {_ENVIRONMENT_VERSION}, got {environment_version}"
            )
        report["runtime"] = {
            **cast(dict[str, object], report["runtime"]),
            "kaggle_environments": environment_version,
            "torch": importlib.metadata.version("torch"),
            "numpy": importlib.metadata.version("numpy"),
            "pydantic": importlib.metadata.version("pydantic"),
        }
        extracted = work_root / "submission"
        _extract(archive_path, extracted)
        profile = cast(dict[str, Any], manifest["agent_profile"])
        configuration = dict(profile["resolved_environment"])
        configuration.update(
            {
                "episodeSteps": 720,
                "actTimeout": act_timeout_seconds,
                "runTimeout": run_timeout_seconds,
                "seed": seed,
            }
        )
        module = _load_entrypoint(extracted)
        runs = [_smoke_seat(module, configuration, seat) for seat in (0, 1)]
        expected_calls = int(configuration["episodeSteps"]) - 1
        expected_native = next(
            record
            for record in cast(list[dict[str, Any]], manifest["native_binaries"])
            if record["python_abi"] == str(sysconfig.get_config_var("SOABI"))
        )
        report.update(
            {
                "manifest": {
                    "source_commit": manifest["source_commit"],
                    "checkpoint": manifest["checkpoint"],
                    "actor_artifact": manifest["actor_artifact"],
                    "file_count": len(files) + 1,
                },
                "smoke": {"configuration": configuration, "runs": runs},
            }
        )
        for run in runs:
            runtime = cast(dict[str, Any], run["runtime"])
            native = cast(dict[str, Any], runtime["native_module"])
            if run["statuses"] != ["DONE", "DONE"]:
                raise RuntimeError(f"full-season smoke did not finish: {run['statuses']}")
            if (
                _as_int(run["action_calls"], "action calls") != expected_calls
                or _as_int(run["non_pass_turns"], "non-pass turns") < 1
            ):
                raise RuntimeError("submission did not produce a complete nontrivial action trace")
            if runtime["last_error"] is not None:
                raise RuntimeError(
                    f"submission recorded an execution error: {runtime['last_error']}"
                )
            if (
                _as_float(run["initial_overage_seconds"], "initial overage")
                != (remaining_overage_seconds)
                or _as_float(run["ending_overage_seconds"], "ending overage") < 0.0
            ):
                raise RuntimeError("submission exhausted official overage time")
            if native["sha256"] != expected_native["sha256"]:
                raise RuntimeError("submission loaded an unexpected native extension")
        validated_archive = output_dir / "validated-submission.tar.gz"
        shutil.copy2(archive_path, validated_archive)
        if _sha256(validated_archive) != _sha256(archive_path):
            raise RuntimeError("validated archive copy differs from its input")
        report.update(
            {
                "status": "passed",
                "dependency_install_output_tail": dependency_output[-12000:],
                "validated_archive": {
                    "path": str(validated_archive),
                    "sha256": _sha256(validated_archive),
                    "size_bytes": validated_archive.stat().st_size,
                },
            }
        )
    except BaseException as error:
        report["error"] = {
            "type": type(error).__name__,
            "message": str(error),
            "traceback": traceback.format_exc(),
        }
    report_path = output_dir / "submission-validation-report.json"
    report_path.write_text(
        json.dumps(report, indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )
    print("TURN_POLICY_SUBMISSION_VALIDATION=" + json.dumps(report, sort_keys=True, default=str))
    if report["status"] != "passed":
        raise RuntimeError(f"exact submission validation failed; see {report_path}")
    return report


def main() -> None:
    """Run validation with local arguments or Kaggle filesystem defaults."""
    on_kaggle = Path("/kaggle/input").is_dir()
    parser = argparse.ArgumentParser()
    parser.add_argument("--archive", type=Path, default=None)
    parser.add_argument(
        "--output-dir", type=Path, default=Path("/kaggle/working") if on_kaggle else None
    )
    parser.add_argument(
        "--work-dir",
        type=Path,
        default=Path("/kaggle/temp/turn_policy_validation") if on_kaggle else None,
    )
    parser.add_argument("--seed", type=int, default=20260825)
    parser.add_argument("--act-timeout", type=float, default=1.0)
    parser.add_argument("--remaining-overage", type=float, default=60.0)
    parser.add_argument("--run-timeout", type=float, default=1200.0)
    parser.add_argument("--install-environment", action="store_true", default=on_kaggle)
    arguments = parser.parse_args()
    archive = arguments.archive or (_archive_from_inputs() if on_kaggle else None)
    if archive is None or arguments.output_dir is None or arguments.work_dir is None:
        parser.error("local validation requires --archive, --output-dir and --work-dir")
    validate_archive(
        archive,
        arguments.output_dir,
        arguments.work_dir,
        seed=arguments.seed,
        act_timeout_seconds=arguments.act_timeout,
        remaining_overage_seconds=arguments.remaining_overage,
        run_timeout_seconds=arguments.run_timeout,
        install_environment=arguments.install_environment,
    )


if __name__ == "__main__":
    main()
