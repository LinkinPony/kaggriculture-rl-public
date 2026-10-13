"""CPU Kaggle entrypoint with public observation history and persistent plans."""

import hashlib
import json
import math
import sysconfig
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

import numpy as np
import torch

from kagg_revue.native import _revue_native as native

_ROOT = Path(__file__).resolve().parents[4]
_PROFILE: dict[str, Any] | None = None
_MODEL: Any = None
_SESSIONS: dict[int, "Session"] = {}


def _digest(path: Path) -> str:
    result = hashlib.sha256()
    with path.open("rb") as stream:
        while block := stream.read(8 * 1024 * 1024):
            result.update(block)
    return result.hexdigest()


def _plain(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(k): _plain(v) for k, v in value.items()}
    if isinstance(value, Sequence) and not isinstance(value, str | bytes):
        return [_plain(v) for v in value]
    if isinstance(value, float) and math.isfinite(value) and value.is_integer():
        return int(value)
    return value


def _load() -> dict[str, Any]:
    global _PROFILE, _MODEL
    if _PROFILE is None:
        profile = json.loads((_ROOT / "agent_profile.json").read_text())
        actor = _ROOT / profile["actor_path"]
        if _digest(actor) != profile["actor_sha256"]:
            raise ValueError("frozen actor identity mismatch")
        abi = sysconfig.get_config_var("SOABI")
        binary = next(x for x in profile["native_binaries"] if x["python_abi"] == abi)
        if _digest(Path(native.__file__)) != binary["sha256"]:
            raise ValueError("native deployment identity mismatch")
        torch.set_num_threads(profile["cpu_threads"])
        _MODEL = torch.jit.load(str(actor), map_location="cpu").eval()  # type: ignore[no-untyped-call]
        _PROFILE = profile
    return _PROFILE


class Session:
    """Observe every official turn and replace the plan only at learned boundaries."""

    def __init__(self, configuration: dict[str, Any], profile: dict[str, Any]) -> None:
        """Allocate one public-state adapter and fixed inference buffers."""
        self.native = native.ContractSession(configuration, profile["unit_limit"])
        self.features = np.empty((1, profile["observation_features"]), dtype=np.float16)
        self.plan = np.zeros((1, profile["factors"]), dtype=np.int64)
        self.interval = int(profile["interval"])
        self.program_capacity = int(profile.get("program_capacity", 0))
        self.quantities = profile.get("quantities", [])
        turns = profile.get(
            "decision_turns",
            range(0, int(profile["resolved_environment"]["episodeSteps"]) - 1, self.interval),
        )
        self.boundaries = {turn: index for index, turn in enumerate(turns)}
        self.last_step = -1

    def act(self, observation: dict[str, Any]) -> dict[str, Any]:
        """Refresh public history and compile this turn's legal action."""
        step = int(observation["step"])
        self.native.update(observation)
        if step in self.boundaries:
            self.native.observe_into(self.features)
            with torch.inference_mode():
                selected = _MODEL(
                    torch.from_numpy(self.features), torch.tensor([self.boundaries[step]])
                )
            self.plan[:] = selected.numpy()
            if self.program_capacity:
                self.native.set_program(self.plan, self.program_capacity, self.quantities)
        self.last_step = step
        if self.program_capacity:
            return dict(self.native.program_action())
        return dict(self.native.action(self.plan))


def agent(observation: Any, configuration: Any = None) -> dict[str, Any]:
    """Compile the frozen policy using only the supplied official seat observation."""
    profile = _load()
    observation = _plain(observation)
    player = int(observation["player"])
    if player not in _SESSIONS or int(observation["step"]) == 0:
        resolved = {**profile["resolved_environment"], **_plain(configuration or {})}
        _SESSIONS[player] = Session(resolved, profile)
    return _SESSIONS[player].act(observation)


def runtime_info() -> dict[str, Any]:
    """Expose the exact deployed artifacts to the shared official-budget validator."""
    profile = _load()
    return {
        "actor_sha256": profile["actor_sha256"],
        "native_module": {"sha256": _digest(Path(native.__file__))},
        "last_error": None,
    }
