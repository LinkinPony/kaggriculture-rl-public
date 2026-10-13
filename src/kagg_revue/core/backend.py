"""Native engine and external-artifact boundary shared across workflows."""

from __future__ import annotations

import hashlib
import importlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from kagg_revue.opponents.portfolios.catalog import ACTIVE_IDS
from kagg_revue.opponents.public import (
    PublicAgentRuntime,
    load_public_agent_manifest,
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(8 * 1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


@dataclass(frozen=True)
class BackendApi:
    """Loaded native engine, planner, encoder, and notebook boundaries."""

    repository_root: Path
    engine: Any
    engine_batch: Any
    native_planner: Any
    official_action_builder: Any
    official_action_control_spec: Any
    game_rules: Any
    conditional_program_session: Any
    conditional_program_spec: Any
    conditional_program_observations_batch: Any
    conditional_program_active_observations_batch: Any
    conditional_program_select_batch: Any
    conditional_program_actions_batch: Any
    conditional_program_compile_teacher_batch: Any
    actor_encoder_spec: Any
    encode_actor_observation: Any
    encode_official_observation_numeric: Any
    decode_action_tokens: Any
    action_codec_spec: Any
    derived_fact_spec: Any
    gpu_policy_state_spec: Any
    policy_session: Any
    policy_session_batch: Any
    engine_policy_session_batch: Any
    engine_policy_turn_inputs: Any
    engine_policy_turn_inputs_into: Any
    engine_policy_turn_inputs_compact_into: Any
    engine_step_numeric_batch: Any
    deterministic_incumbent_session: Any
    engine_step_deterministic_incumbent_batch: Any
    engine_step_kaito_v48_batch: Any
    capability_session: Any
    capability_spec: Any
    capability_candidates_batch: Any
    capability_select_batch: Any
    capability_actions_batch: Any
    capability_decision_required_batch: Any
    intent_ledger_session: Any
    intent_ledger_batch: Any
    intent_ledger_spec: Any
    intent_ledger_observations_batch: Any
    intent_ledger_select_batch: Any
    intent_ledger_actions_batch: Any
    effect_policy_session: Any
    effect_policy_batch: Any
    effect_policy_spec: Any
    effect_policy_observations_batch: Any
    effect_policy_select_batch: Any
    effect_policy_actions_batch: Any
    unit_task_session: Any
    unit_task_spec: Any
    unit_task_snapshots_batch: Any
    unit_task_apply_sequences_batch: Any
    unit_task_observations_batch: Any
    unit_task_select_batch: Any
    unit_task_actions_batch: Any
    unit_task_decision_required_batch: Any
    structured_plan_session: Any
    structured_plan_spec: Any
    structured_plan_observations_batch: Any
    structured_plan_ready_observations_batch: Any
    structured_plan_apply_batch: Any
    structured_plan_actions_batch: Any
    structured_plan_decision_required_batch: Any
    structured_plan_step_self_play_batch: Any
    structured_plan_advance_self_play_batch: Any
    structured_plan_opponent_batch_steps: dict[str, Any]
    kaito_v48_action_numeric_batch: Any
    kaito_v48_route_action_numeric_batch: Any
    kaito_v48_proposed_route: Any
    native_opponent_batch_steps: dict[str, Any]
    load_public_agent_manifest: Any
    public_agent_runtime: Any
    identity: dict[str, object]


def load_backend(repository_root: Path) -> BackendApi:
    """Load the in-repository extension and record its binary identity."""
    try:
        engine_module = importlib.import_module("kagg_revue.native.engine")
        native_module = importlib.import_module("kagg_revue.native._revue_native")
    except ModuleNotFoundError as error:
        raise RuntimeError(
            "native extension is missing; run python -m kagg_revue.native.build build.target=legacy"
        ) from error
    native_file = native_module.__file__
    if native_file is None:
        raise ImportError("native module does not expose a filesystem path")
    native_path = Path(native_file).resolve()
    native_root = (repository_root / "src" / "kagg_revue" / "native").resolve()
    if not native_path.is_relative_to(native_root):
        raise ImportError(f"native module resolved outside this repository: {native_path}")
    return BackendApi(
        repository_root=repository_root.resolve(),
        engine=engine_module.Engine,
        engine_batch=native_module.EngineBatch,
        native_planner=native_module.NativePlanner,
        official_action_builder=native_module.NativeOfficialActionBuilder,
        official_action_control_spec=native_module.official_action_control_spec,
        game_rules=native_module.game_rules,
        conditional_program_session=native_module.ConditionalProgramSession,
        conditional_program_spec=native_module.conditional_program_spec,
        conditional_program_observations_batch=(
            native_module.conditional_program_observations_batch
        ),
        conditional_program_active_observations_batch=(
            native_module.conditional_program_active_observations_batch
        ),
        conditional_program_select_batch=(native_module.conditional_program_select_batch),
        conditional_program_actions_batch=(native_module.conditional_program_actions_batch),
        conditional_program_compile_teacher_batch=(
            native_module.conditional_program_compile_teacher_batch
        ),
        actor_encoder_spec=native_module.actor_encoder_spec,
        encode_actor_observation=native_module.encode_actor_observation,
        encode_official_observation_numeric=(native_module.encode_official_observation_numeric),
        decode_action_tokens=native_module.decode_action_tokens,
        action_codec_spec=native_module.action_codec_spec,
        derived_fact_spec=native_module.derived_fact_spec,
        gpu_policy_state_spec=native_module.gpu_policy_state_spec,
        policy_session=native_module.PolicySession,
        policy_session_batch=native_module.PolicySessionBatch,
        engine_policy_session_batch=native_module.engine_policy_session_batch,
        engine_policy_turn_inputs=native_module.engine_policy_turn_inputs,
        engine_policy_turn_inputs_into=native_module.engine_policy_turn_inputs_into,
        engine_policy_turn_inputs_compact_into=(
            native_module.engine_policy_turn_inputs_compact_into
        ),
        engine_step_numeric_batch=native_module.engine_step_numeric_batch,
        deterministic_incumbent_session=native_module.DeterministicIncumbentSession,
        engine_step_deterministic_incumbent_batch=(
            native_module.engine_step_deterministic_incumbent_batch
        ),
        engine_step_kaito_v48_batch=native_module.engine_step_kaito_v48_batch,
        capability_session=native_module.CapabilitySession,
        capability_spec=native_module.capability_spec,
        capability_candidates_batch=native_module.capability_candidates_batch,
        capability_select_batch=native_module.capability_select_batch,
        capability_actions_batch=native_module.capability_actions_batch,
        capability_decision_required_batch=(native_module.capability_decision_required_batch),
        intent_ledger_session=native_module.IntentLedgerSession,
        intent_ledger_batch=native_module.IntentLedgerBatch,
        intent_ledger_spec=native_module.intent_ledger_spec,
        intent_ledger_observations_batch=(native_module.intent_ledger_observations_batch),
        intent_ledger_select_batch=native_module.intent_ledger_select_batch,
        intent_ledger_actions_batch=native_module.intent_ledger_actions_batch,
        effect_policy_session=native_module.AtomicEffectSession,
        effect_policy_batch=native_module.AtomicEffectBatch,
        effect_policy_spec=native_module.effect_policy_spec,
        effect_policy_observations_batch=(
            native_module.effect_policy_observations_batch
        ),
        effect_policy_select_batch=native_module.effect_policy_select_batch,
        effect_policy_actions_batch=native_module.effect_policy_actions_batch,
        unit_task_session=native_module.UnitTaskSession,
        unit_task_spec=native_module.unit_task_spec,
        unit_task_snapshots_batch=native_module.unit_task_snapshots_batch,
        unit_task_apply_sequences_batch=(native_module.unit_task_apply_sequences_batch),
        unit_task_observations_batch=native_module.unit_task_observations_batch,
        unit_task_select_batch=native_module.unit_task_select_batch,
        unit_task_actions_batch=native_module.unit_task_actions_batch,
        unit_task_decision_required_batch=(native_module.unit_task_decision_required_batch),
        structured_plan_session=native_module.StructuredPlanSession,
        structured_plan_spec=native_module.structured_plan_spec,
        structured_plan_observations_batch=(native_module.structured_plan_observations_batch),
        structured_plan_ready_observations_batch=(
            native_module.structured_plan_ready_observations_batch
        ),
        structured_plan_apply_batch=native_module.structured_plan_apply_batch,
        structured_plan_actions_batch=native_module.structured_plan_actions_batch,
        structured_plan_decision_required_batch=(
            native_module.structured_plan_decision_required_batch
        ),
        structured_plan_step_self_play_batch=(native_module.structured_plan_step_self_play_batch),
        structured_plan_advance_self_play_batch=(
            native_module.structured_plan_advance_self_play_batch
        ),
        structured_plan_opponent_batch_steps={
            "boatlee_v21": native_module.structured_plan_step_boatlee_v21_batch,
            "kaito_v39": native_module.structured_plan_step_kaito_v39_batch,
            "kaito_v48": native_module.structured_plan_step_kaito_v48_batch,
            "mugundh_v21": native_module.structured_plan_step_mugundh_v21_batch,
        },
        kaito_v48_action_numeric_batch=native_module.kaito_v48_action_numeric_batch,
        kaito_v48_route_action_numeric_batch=(native_module.kaito_v48_route_action_numeric_batch),
        kaito_v48_proposed_route=native_module.kaito_v48_proposed_route,
        native_opponent_batch_steps={
            **{
                name: native_module.engine_step_native_opponent_batch
                for name in ACTIVE_IDS
            },
            # Retained only for archived research and legacy direct callers.
            "boatlee_v21": native_module.engine_step_boatlee_v21_batch,
            "deterministic_incumbent": (native_module.engine_step_deterministic_incumbent_batch),
            "kaito_v39": native_module.engine_step_kaito_v39_batch,
            "kaito_v48": native_module.engine_step_kaito_v48_batch,
            "mugundh_v21": native_module.engine_step_mugundh_v21_batch,
        },
        load_public_agent_manifest=load_public_agent_manifest,
        public_agent_runtime=PublicAgentRuntime,
        identity={
            "implementation": "repository_local",
            "native_module": {
                "path": str(native_path.relative_to(repository_root)),
                "sha256": _sha256(native_path),
                "size_bytes": native_path.stat().st_size,
            },
        },
    )


__all__ = ["BackendApi", "load_backend"]
