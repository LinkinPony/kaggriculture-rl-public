"""Hash-bound native and model compatibility evidence for a full PPO migration."""

import json
from pathlib import Path
from typing import Any

from kagg_revue.artifacts.io import digest
from kagg_revue.learning.adapter import runtime_settings
from kagg_revue.learning.config import Experiment
from kagg_revue.learning.matchmaking.archives import NativeQualification
from kagg_revue.learning.matchmaking.observations import verify_native_identity
from kagg_revue.opponents import artifacts as scripts
from kagg_revue.policy.contracts import ContractLayout


def read(pointer: NativeQualification) -> dict[str, Any]:
    """Require unchanged successful evidence before using any reported comparison."""
    if digest(pointer.path) != pointer.sha256:
        raise ValueError("feature migration evidence changed")
    report: dict[str, Any] = json.loads(pointer.path.read_text())
    if report.get("passed") is not True:
        raise ValueError("feature migration requires successful evidence")
    return report


def verify(
    state: dict[str, Any],
    config: Experiment,
    native_sha256: str,
    native: NativeQualification,
    model: NativeQualification,
    script: NativeQualification,
) -> None:
    """Bind old pool engines, exact model outputs and all C++ script encoders."""
    qualified = {
        **state,
        "native": native_sha256,
        "protocol": config.model_dump(mode="json"),
        "opponent_native_qualification": native.model_dump(mode="json"),
    }
    engines = {
        state["native"],
        *(m["source_native_sha256"] for m in state.get("external_opponents", {}).values()),
    }
    for engine in engines:
        verify_native_identity(qualified, engine)
    layout = ContractLayout.resolve(runtime_settings(config))
    report = read(model)
    if (
        report.get("inputs", {}).get("checkpoint_sha256") != state["members"][state["latest"]]
        or report.get("target_native_sha256") != native_sha256
        or report.get("target_observation_features") != layout.observation.features
    ):
        raise ValueError("model evidence does not bind this checkpoint and native feature layout")
    for mode in ("cpu_fp32", "cuda_bf16"):
        rows = report.get("checks", {}).get(mode, [])
        if not rows or any(not all(row["equal"].values()) for row in rows):
            raise ValueError("migration must preserve actor, critic, actions and memory")
        if mode == "cuda_bf16" and (
            sum(row["length"] for row in rows) != layout.observation.turns
            or rows[-1]["retained_history_turns"] != layout.network.memory_turns
        ):
            raise ValueError("migration must qualify a complete recurrent season")
    assert config.script_population is not None
    current = scripts.identity(config.script_population)
    previous = state["script_runtime"]
    if current["files"].keys() != previous["files"].keys() or any(
        value != current["files"][name]
        for name, value in previous["files"].items()
        if not Path(name).name.startswith("_revue_native.")
    ):
        raise ValueError("feature migration must preserve the frozen script implementations")
    report = read(script)
    if (
        report.get("script_runtime") != current
        or report.get("target_native_sha256") != native_sha256
        or report.get("matched_core_legacy_v5b") is not True
        or report.get("features") != layout.observation.features
        or report.get("checked_feature_rows", 0)
        < 2 * len(config.script_population.agents) * layout.observation.turns
    ):
        raise ValueError("native script evidence does not bind the complete v5b integration")
