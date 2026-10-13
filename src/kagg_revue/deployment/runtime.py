"""Packaged CPU agent using only official observations and a frozen sampled actor."""

import hashlib
import json
import math
import sysconfig
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

import numpy as np
import torch

from kagg_revue.native import _revue_observation as native

_ROOT = Path(__file__).resolve().parents[3]
_PROFILE: dict[str, Any] | None = None
_MODEL: Any = None
_SESSIONS: dict[int, "Session"] = {}
_ERROR: str | None = None


def _digest(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def _plain(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _plain(item) for key, item in value.items()}
    if isinstance(value, Sequence) and not isinstance(value, str | bytes):
        return [_plain(item) for item in value]
    if isinstance(value, float) and math.isfinite(value) and value.is_integer():
        return int(value)
    return value


def _load() -> dict[str, Any]:
    global _PROFILE, _MODEL
    if _PROFILE is None:
        profile = json.loads((_ROOT / "agent_profile.json").read_text())
        if profile["schema"] not in {
            "random-root-grounded-deployment-v1",
            "checkpoint-root-grounded-deployment-v1",
        }:
            raise ValueError("unsupported deployment profile")
        actor = _ROOT / "actor.pt"
        if _digest(actor) != profile["actor_sha256"]:
            raise ValueError("serialized actor identity differs")
        abi = sysconfig.get_config_var("SOABI")
        binaries = [item for item in profile["native_binaries"] if item["python_abi"] == abi]
        if len(binaries) != 1 or _digest(Path(native.__file__)) != binaries[0]["sha256"]:
            raise ValueError("observation extension identity differs")
        versions = getattr(native, "feature_versions", (native.feature_version,))
        if profile["feature_version"] not in versions:
            raise ValueError("observation feature ABI differs")
        torch.set_num_threads(profile["cpu_threads"])
        _MODEL = torch.jit.load(str(actor), map_location="cpu").eval()  # type: ignore[no-untyped-call]
        _PROFILE = profile
    return _PROFILE


class Session:
    """Keep observation history and sampling RNG private to one game and seat."""

    def __init__(
        self, configuration: dict[str, Any], profile: dict[str, Any], sample_seed: int
    ) -> None:
        """Allocate fixed batch-one buffers without consulting a training environment."""
        for key in ("boardSize", "episodeSteps", "maxMarketOrdersPerTurn"):
            if configuration[key] != profile["environment"][key]:
                raise ValueError(f"deployment geometry differs: {key}")
        self.native = native.ContractSession(configuration, profile["unit_limit"])
        self.features = np.empty((1, profile["observation_features"]), dtype=np.float16)
        self.inputs = torch.from_numpy(self.features)
        self.steps = torch.zeros(1, dtype=torch.long)
        self.quantities = profile["quantities"]
        self.sample_seed = sample_seed
        self.rng = torch.Generator(device="cpu").manual_seed(sample_seed).get_state()
        self.program = np.empty((1, 0), dtype=np.int64)
        self.last_step = -1
        self.memory: tuple[torch.Tensor, torch.Tensor, torch.Tensor] | None = None
        memory = profile.get("memory", {})
        if memory.get("turns", 0):
            capacity = memory["turns"] * memory["tokens"]
            shape = (
                memory["layers"],
                1,
                memory["heads"],
                capacity,
                memory["width"] // memory["heads"],
            )
            self.memory = (
                torch.zeros(shape),
                torch.zeros(shape),
                torch.full((capacity,), -1, dtype=torch.long),
            )

    def act(self, observation: dict[str, Any]) -> dict[str, Any]:
        """Encode the official observation and sample one causal action program."""
        step = int(observation["step"])
        if self.memory is not None and step != self.last_step + 1:
            raise ValueError("recurrent deployment requires contiguous observations from turn zero")
        self.native.update(observation)
        self.native.observe_into(self.features)
        self.steps.fill_(step)
        with torch.random.fork_rng(devices=[]), torch.inference_mode():
            torch.set_rng_state(self.rng)
            if self.memory is None:
                selected = _MODEL(self.inputs, self.steps)
            else:
                selected, keys, values, turns = _MODEL(self.inputs, self.steps, *self.memory)
                self.memory = (keys, values, turns)
            self.rng = torch.get_rng_state()
        self.program = selected.numpy()
        self.native.set_program(self.program, 1, self.quantities)
        self.last_step = step
        return self.native.program_action()


def agent(observation: Any, configuration: Any = None) -> dict[str, Any]:
    """Run the authenticated model with no script fallback or hidden state access."""
    global _ERROR
    try:
        profile = _load()
        observation = _plain(observation)
        player = int(observation["player"])
        if player not in _SESSIONS or int(observation["step"]) == 0:
            resolved = {**profile["environment"], **_plain(configuration or {})}
            _SESSIONS[player] = Session(resolved, profile, profile["sampling_seed"] + player)
        return _SESSIONS[player].act(observation)
    except Exception as error:
        _ERROR = f"{type(error).__name__}: {error}"
        raise


def runtime_info() -> dict[str, Any]:
    """Expose exact identities and sampling seeds to archive qualification tools."""
    profile = _load()
    return {
        "actor_sha256": profile["actor_sha256"],
        "native_module": {"sha256": _digest(Path(native.__file__))},
        "sampling_seeds": {seat: session.sample_seed for seat, session in _SESSIONS.items()},
        "last_error": _ERROR,
    }
