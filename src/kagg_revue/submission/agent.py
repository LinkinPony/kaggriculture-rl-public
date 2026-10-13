"""Fail-closed Kaggle entrypoint for one frozen recurrent actor."""

from __future__ import annotations

import hashlib
import json
import math
import sysconfig
from collections.abc import Mapping, Sequence
from pathlib import Path, PurePosixPath
from typing import Any, cast

from kagg_revue.core.backend import BackendApi, load_backend
from kagg_revue.policy.runtime import TurnPolicyAgent

_ROOT = Path(__file__).resolve().parents[3]
_PROFILE_PATH = _ROOT / "agent_profile.json"
_AGENTS: dict[tuple[str, int], TurnPolicyAgent] = {}
_PROFILE: dict[str, Any] | None = None
_BACKEND: BackendApi | None = None
_LAST_ERROR: str | None = None


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(8 * 1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def _plain(value: Any) -> Any:
    if isinstance(value, float) and math.isfinite(value) and value.is_integer():
        return int(value)
    if isinstance(value, Mapping):
        return {str(key): _plain(item) for key, item in value.items()}
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return [_plain(item) for item in value]
    return value


def _profile() -> dict[str, Any]:
    global _PROFILE
    if _PROFILE is not None:
        return _PROFILE
    value = json.loads(_PROFILE_PATH.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise TypeError("agent profile must be a mapping")
    if value.get("schema_version") != "turn-policy-submission-profile-v1":
        raise ValueError("unsupported agent profile")
    actor_member = PurePosixPath(str(value.get("actor_path", "")))
    if actor_member.is_absolute() or ".." in actor_member.parts:
        raise ValueError("agent profile actor path is unsafe")
    actor_path = (_ROOT / actor_member).resolve()
    if not actor_path.is_relative_to(_ROOT) or not actor_path.is_file():
        raise FileNotFoundError("agent profile actor artifact is absent")
    if _sha256(actor_path) != str(value.get("actor_sha256", "")):
        raise ValueError("agent actor artifact SHA-256 mismatch")
    environment = value.get("resolved_environment")
    if not isinstance(environment, dict):
        raise TypeError("agent profile resolved environment must be a mapping")
    _PROFILE = cast(dict[str, Any], value)
    return _PROFILE


def _backend(profile: Mapping[str, Any]) -> BackendApi:
    global _BACKEND
    if _BACKEND is not None:
        return _BACKEND
    backend = load_backend(_ROOT)
    native = cast(Mapping[str, object], backend.identity["native_module"])
    records = profile.get("native_binaries")
    if not isinstance(records, list):
        raise TypeError("agent profile native binaries must be a list")
    abi = str(sysconfig.get_config_var("SOABI"))
    matches = [
        record
        for record in records
        if isinstance(record, dict) and record.get("python_abi") == abi
    ]
    if len(matches) != 1:
        raise ValueError(f"agent profile has no unique native binary for {abi}")
    expected = cast(dict[str, Any], matches[0])
    if (
        native.get("sha256") != expected.get("sha256")
        or native.get("size_bytes") != expected.get("size_bytes")
    ):
        raise ValueError("loaded native extension differs from the agent profile")
    _BACKEND = backend
    return backend


def _configuration(raw: Any, profile: Mapping[str, Any]) -> dict[str, Any]:
    defaults = profile["resolved_environment"]
    if not isinstance(defaults, Mapping):
        raise TypeError("agent profile environment must be a mapping")
    resolved = {str(key): _plain(value) for key, value in defaults.items()}
    if raw is not None:
        supplied = _plain(raw)
        if not isinstance(supplied, Mapping):
            raise TypeError("Kaggle configuration must be a mapping")
        resolved.update({str(key): value for key, value in supplied.items()})
    return resolved


def _agent(
    observation: Mapping[str, Any],
    configuration: dict[str, Any],
    profile: Mapping[str, Any],
) -> TurnPolicyAgent:
    player = int(observation["player"])
    configuration_key = json.dumps(configuration, sort_keys=True, separators=(",", ":"))
    key = configuration_key, player
    if key not in _AGENTS:
        actor_path = (_ROOT / str(profile["actor_path"])).resolve()
        _AGENTS[key] = TurnPolicyAgent(
            _backend(profile),
            configuration,
            actor_path,
            "cpu",
            int(profile["unit_limit"]),
            cpu_threads=int(profile["cpu_threads"]),
        )
    return _AGENTS[key]


def agent(observation: Any, configuration: Any = None) -> dict[str, Any]:
    """Return one legal official action from the authenticated actor."""
    global _LAST_ERROR
    try:
        plain_observation = _plain(observation)
        if not isinstance(plain_observation, Mapping):
            raise TypeError("Kaggle observation must be a mapping")
        profile = _profile()
        resolved = _configuration(configuration, profile)
        return _agent(plain_observation, resolved, profile).act(plain_observation)
    except Exception as error:
        _LAST_ERROR = f"{type(error).__name__}: {error}"
        raise


def runtime_info() -> dict[str, object]:
    """Expose bounded package identities to exact-archive smoke checks."""
    profile = _profile()
    backend = _backend(profile)
    return {
        "actor_sha256": profile["actor_sha256"],
        "native_module": backend.identity["native_module"],
        "last_error": _LAST_ERROR,
    }


__all__ = ["agent", "runtime_info"]
