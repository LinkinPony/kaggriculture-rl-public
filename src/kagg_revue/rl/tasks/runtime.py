"""Official-observation runtime for a frozen unit-task checkpoint."""

from __future__ import annotations

import time
from collections.abc import Mapping, Sequence
from contextlib import nullcontext
from dataclasses import replace
from pathlib import Path
from typing import Any, cast

import numpy as np
import torch
from torch import Tensor

from kagg_revue.core.backend import BackendApi
from kagg_revue.policy.facts import OpponentInventoryBounds
from kagg_revue.policy.tasks.grammar import (
    FactorizedTaskDecisionInputs,
    TaskDecisionInputs,
)
from kagg_revue.policy.tasks.native import (
    NativeTaskContract,
    decision_inputs,
    factorized_decision_inputs,
)
from kagg_revue.policy.tasks.runtime import (
    CompiledUnitActions,
    decode_market_actions,
    task_context,
)
from kagg_revue.policy.transformer import HistoryState
from kagg_revue.rl.tasks.checkpoint import load_task_checkpoint


def _autocast(device: torch.device) -> Any:
    if device.type == "cuda":
        return torch.autocast(device_type="cuda", dtype=torch.bfloat16)
    return nullcontext()


def _batched_task_observation(raw: Mapping[str, object]) -> dict[str, object]:
    arrays = [
        "mode_mask",
        "prefix_fields",
        "prefix_mask",
        "root_features",
        "target_conflicts",
        "resource_conflicts",
    ]
    if "candidate_mask" in raw:
        arrays.extend(
            ("candidate_mask", "candidate_arrivals", "candidate_features")
        )
    result: dict[str, object] = {
        name: np.asarray(raw[name])[None] for name in arrays
    }
    result.update(
        unit_indices=np.asarray([raw["unit_index"]], dtype=np.int64),
        current_x=np.asarray([raw["current_x"]], dtype=np.int64),
        current_y=np.asarray([raw["current_y"]], dtype=np.int64),
        available_at=np.asarray([raw["available_at"]], dtype=np.int64),
        day_end=np.asarray([raw["day_end"]], dtype=np.int64),
    )
    return result


def _integer(value: object, name: str) -> int:
    if not isinstance(value, (int, np.integer)) or isinstance(value, bool):
        raise ValueError(f"unit-task native {name} must be an integer")
    return int(value)


class TaskTapeAgent:
    """Episode-local no-search actor, native task compiler, and market decoder."""

    def __init__(
        self,
        backend: BackendApi,
        configuration: Mapping[str, object],
        checkpoint: Path,
        device: str,
        unit_limit: int,
        maximum_quantity: int,
        *,
        sample: bool = False,
        cpu_threads: int = 1,
        act_timeout_seconds: float = 1.0,
        remaining_overage_seconds: float = 60.0,
    ) -> None:
        """Authenticate a checkpoint against native visible-state contracts."""
        if cpu_threads < 1:
            raise ValueError("unit-task runtime CPU threads must be positive")
        if act_timeout_seconds <= 0.0 or remaining_overage_seconds < 0.0:
            raise ValueError("unit-task runtime time budgets are invalid")
        self._backend = backend
        self._configuration = dict(configuration)
        self._device = torch.device(device)
        if self._device.type == "cuda" and not torch.cuda.is_available():
            raise RuntimeError("CUDA unit-task runtime was requested but is unavailable")
        if self._device.type == "cpu":
            torch.set_num_threads(cpu_threads)
        self._contract = NativeTaskContract.from_spec(
            cast(
                Mapping[str, object],
                backend.unit_task_spec(
                    self._configuration,
                    unit_limit,
                    maximum_quantity,
                ),
            )
        )
        self._model, self._metadata = load_task_checkpoint(
            checkpoint,
            self._contract,
            self._device,
            include_optimizer=False,
        )
        self._model.eval()
        resolved_config = self._metadata.get("resolved_config")
        trained_environment = (
            resolved_config.get("environment")
            if isinstance(resolved_config, Mapping)
            else None
        )
        if not isinstance(trained_environment, Mapping) or dict(
            trained_environment
        ) != self._configuration:
            raise ValueError("unit-task checkpoint environment identity differs")
        artifacts = self._metadata.get("opponent_identities")
        current_native = cast(Mapping[str, object], backend.identity["native_module"])
        if not isinstance(artifacts, Mapping):
            raise ValueError("unit-task checkpoint lacks artifact identities")
        checkpoint_native = artifacts.get("native_module")
        if (
            not isinstance(checkpoint_native, Mapping)
            or checkpoint_native.get("sha256") != current_native.get("sha256")
        ):
            raise ValueError("unit-task checkpoint native extension identity differs")
        architecture = self._model.actor.architecture
        codec = cast(Mapping[str, object], backend.action_codec_spec())
        source_actor = self._metadata.get("source_actor_identity")
        if not isinstance(source_actor, Mapping):
            raise ValueError("unit-task checkpoint lacks source actor identity")
        native_keys = tuple(str(value) for value in cast(Sequence[object], codec["keys"]))
        checkpoint_keys = tuple(
            str(value)
            for value in cast(Sequence[object], source_actor.get("action_keys", ()))
        )
        if checkpoint_keys != native_keys:
            raise ValueError("unit-task checkpoint action vocabulary differs from native")
        encoder = cast(Mapping[str, object], backend.actor_encoder_spec())
        if source_actor.get("actor_encoder_version") != encoder.get("version"):
            raise ValueError("unit-task checkpoint observation encoder differs from native")
        facts = cast(Mapping[str, object], backend.derived_fact_spec())
        fact_widths = (
            _integer(facts["turn_features"], "turn fact width"),
            _integer(facts["prefix_features"], "prefix fact width"),
            _integer(facts["candidate_features"], "candidate fact width"),
        )
        actor_widths = (
            architecture.turn_fact_features,
            architecture.prefix_fact_features,
            architecture.candidate_fact_features,
        )
        self._uses_facts = any(actor_widths)
        if self._uses_facts and (
            actor_widths != fact_widths
            or architecture.derived_fact_version != str(facts["version"])
        ):
            raise ValueError("unit-task checkpoint derived facts differ from native")
        market_orders = self._configuration.get("maxMarketOrdersPerTurn")
        if not isinstance(market_orders, int) or isinstance(market_orders, bool):
            raise ValueError("unit-task runtime lacks market order capacity")
        if architecture.max_decisions < unit_limit + market_orders:
            raise ValueError("unit-task checkpoint cannot hold its official action")
        self._has_quantity = np.asarray(codec["has_quantity"], dtype=np.bool_)
        self._sample = sample
        self._task_session = backend.unit_task_session(
            self._configuration,
            unit_limit,
            maximum_quantity,
        )
        self._opponent_bounds = (
            OpponentInventoryBounds(_integer(facts["products"], "product count"))
            if self._uses_facts
            else None
        )
        self._history: HistoryState | None = None
        self._strategy: Tensor | None = None
        self._previous_tokens = torch.zeros(
            (1, architecture.max_decisions),
            dtype=torch.long,
            device=self._device,
        )
        self._previous_quantities = torch.zeros_like(self._previous_tokens)
        self._previous_mask = torch.zeros_like(self._previous_tokens, dtype=torch.bool)
        self._last_step: int | None = None
        self._act_timeout = act_timeout_seconds
        self._initial_overage = remaining_overage_seconds
        self._remaining_overage = remaining_overage_seconds
        self._maximum_actor_seconds = 0.0
        self._turns = 0
        self._task_decisions = 0

    def reset(self) -> None:
        """Drop every episode-local recurrent and compiler state."""
        self._history = None
        self._strategy = None
        self._previous_tokens.zero_()
        self._previous_quantities.zero_()
        self._previous_mask.zero_()
        self._last_step = None
        self._remaining_overage = self._initial_overage
        self._task_session.reset()
        if self._opponent_bounds is not None:
            self._opponent_bounds.reset()
        self._maximum_actor_seconds = 0.0
        self._turns = 0
        self._task_decisions = 0

    def _tensor(self, value: object) -> Tensor:
        return torch.as_tensor(np.asarray(value), device=self._device)

    def act(self, observation: Mapping[str, Any]) -> dict[str, Any]:
        """Return one official action through the native visible-state compiler."""
        started = time.perf_counter()
        step = int(observation["step"])
        if step == 0 or self._last_step is None or step != self._last_step + 1:
            self.reset()
        policy_session = self._backend.policy_session(
            dict(observation),
            self._configuration,
            self._contract.unit_limit,
        )
        visible = self._task_session.visible_state(dict(observation))
        board_raw, units_raw, global_raw = policy_session.encode()
        board = self._tensor(board_raw)[None]
        units = self._tensor(units_raw)[None]
        global_features = self._tensor(global_raw)[None]
        economic_state = (
            self._tensor(policy_session.gpu_state())[None]
            if self._model.actor.economics is not None
            or self._model.tasks.factorized is not None
            else None
        )
        turn_facts: Tensor | None = None
        turn_fact_mask: Tensor | None = None
        if self._uses_facts:
            if self._opponent_bounds is None:
                raise RuntimeError("unit-task runtime lost opponent bounds")
            lower, upper = self._opponent_bounds.update(
                cast(Mapping[str, Any], policy_session.flow_snapshot())
            )
            turn_facts = self._tensor(policy_session.turn_facts(lower, upper))[None]
            turn_fact_mask = torch.ones(
                turn_facts.shape[:2],
                dtype=torch.bool,
                device=self._device,
            )

        with torch.inference_mode(), _autocast(self._device):
            context, self._history, self._strategy, _skill = (
                self._model.actor.start_turn(
                    board,
                    units,
                    global_features,
                    self._previous_tokens,
                    self._previous_quantities,
                    self._previous_mask,
                    self._history,
                    turn_facts,
                    turn_fact_mask,
                    economic_state,
                    self._strategy,
                    sample_skill=False,
                )
            )
            maximum = self._contract.prefix_capacity + self._contract.unit_limit
            for _ in range(maximum):
                if not bool(self._task_session.decision_required_visible(visible)):
                    break
                raw = cast(
                    Mapping[str, object],
                    self._task_session.compact_observation_visible(visible)
                    if self._model.tasks.factorized is not None
                    else self._task_session.observation_visible(visible),
                )
                batched = _batched_task_observation(raw)
                inputs: TaskDecisionInputs | FactorizedTaskDecisionInputs
                if self._model.tasks.factorized is not None:
                    if economic_state is None:
                        raise RuntimeError(
                            "factorized task runtime lacks economic state"
                        )
                    inputs = factorized_decision_inputs(
                        batched,
                        task_context(context),
                        economic_state,
                        self._contract,
                        device=self._device,
                        history_window=self._model.tasks.architecture.history_window,
                    )
                else:
                    legacy_inputs = decision_inputs(
                        batched,
                        task_context(context),
                        self._contract,
                        device=self._device,
                    )
                    inputs = replace(
                        legacy_inputs,
                        candidate_features=legacy_inputs.candidate_features.to(
                            torch.float16
                        ).float(),
                    )
                output = self._model.tasks.rollout(
                    inputs,
                    sample=self._sample,
                    validate_inputs=False,
                    compute_entropy=False,
                )
                selection = torch.stack(
                    (
                        output.actions.mode,
                        output.actions.candidate,
                        output.actions.quantity,
                        output.actions.earliest,
                        output.actions.deadline,
                    ),
                    dim=1,
                )[0].to(device="cpu", dtype=torch.int64)
                self._task_session.select_visible(
                    visible,
                    *(int(value) for value in selection),
                )
                self._task_decisions += 1
            else:
                raise RuntimeError("unit-task runtime exceeded daily planning capacity")
            raw_compiled = cast(
                Mapping[str, object],
                self._task_session.action_numeric_visible(visible),
            )
            unit_count = _integer(raw_compiled["unit_count"], "unit count")
            tokens = np.zeros((1, self._contract.unit_limit), dtype=np.int64)
            quantities = np.zeros_like(tokens)
            results = np.full_like(tokens, -1)
            tokens[0, :unit_count] = np.asarray(raw_compiled["tokens"], dtype=np.int64)
            quantities[0, :unit_count] = np.asarray(
                raw_compiled["quantities"], dtype=np.int64
            )
            results[0, :unit_count] = np.asarray(
                raw_compiled["task_results"], dtype=np.int64
            )
            compiled = CompiledUnitActions(
                tokens=tokens,
                quantities=quantities,
                task_results=results,
                unit_counts=np.asarray([unit_count], dtype=np.int64),
            )
            policy_batch = self._backend.policy_session_batch([policy_session], 1)
            market = decode_market_actions(
                self._model.actor,
                context,
                [policy_session],
                policy_batch,
                compiled,
                self._has_quantity,
                sample=self._sample,
            )
        if self._opponent_bounds is not None:
            self._opponent_bounds.record_own_flow(
                policy_session.own_market_flow_bounds()
            )
        self._previous_tokens = torch.as_tensor(
            market.tokens,
            dtype=torch.long,
            device=self._device,
        )
        self._previous_quantities = torch.as_tensor(
            market.quantities,
            dtype=torch.long,
            device=self._device,
        )
        self._previous_mask = torch.as_tensor(
            market.decision_mask,
            dtype=torch.bool,
            device=self._device,
        )
        self._last_step = step
        self._turns += 1
        action = cast(dict[str, Any], policy_session.action())
        elapsed = time.perf_counter() - started
        self._maximum_actor_seconds = max(self._maximum_actor_seconds, elapsed)
        self._remaining_overage -= max(0.0, elapsed - self._act_timeout)
        if self._remaining_overage < 0.0:
            raise TimeoutError("unit-task runtime exhausted official overage time")
        return action

    def diagnostics(self) -> dict[str, object]:
        """Return bounded official-time and compiler runtime facts."""
        return {
            "turns": self._turns,
            "task_decisions": self._task_decisions,
            "maximum_actor_seconds": self._maximum_actor_seconds,
            "remaining_overage_seconds": self._remaining_overage,
            "native_task_abi": self._contract.version,
            "catalog_fingerprint": self._contract.catalog_fingerprint,
            "online_search": False,
        }

    def act_native(self, engine: Any, player: int) -> dict[str, Any]:
        """Use the same official-visible path against an in-memory engine."""
        return self.act(cast(Mapping[str, Any], engine.observation(player)))


__all__ = ["TaskTapeAgent"]
