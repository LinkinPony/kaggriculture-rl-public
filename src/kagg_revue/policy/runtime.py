"""Incremental policy runtime over the native numeric action boundary."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

import numpy as np
import torch
from numpy.typing import NDArray
from torch import Tensor

from kagg_revue.core.backend import BackendApi
from kagg_revue.policy.economics import EconomicStateLayout
from kagg_revue.policy.economics.transition import apply_selection
from kagg_revue.policy.facts import OpponentInventoryBounds
from kagg_revue.policy.model import ActorArchitecture, TurnPolicyNet
from kagg_revue.policy.state import load_causal_actor_state
from kagg_revue.policy.transformer import HistoryState
from kagg_revue.policy.vocabulary import CURRENT_ACTIONS

NumericFeatureArray = NDArray[np.float32] | NDArray[np.float16]
NumericObservation = tuple[NumericFeatureArray, NumericFeatureArray, NDArray[np.float32]]


@dataclass(frozen=True)
class NumericAction:
    """One fixed-width action sequence consumable by the native engine."""

    tokens: NDArray[np.int64]
    quantities: NDArray[np.int64]
    decision_count: int
    unit_count: int


def load_actor(
    path: Path, device: torch.device
) -> tuple[TurnPolicyNet, tuple[str, ...], str, str | None]:
    """Load and authenticate the model-local fields of an actor artifact."""
    raw = torch.load(path, map_location="cpu", weights_only=True)
    if not isinstance(raw, Mapping):
        raise ValueError("turn-policy actor artifact must be a mapping")
    artifact_version = raw.get("artifact_version")
    if artifact_version not in {
        "turn-policy-actor-v2",
        "turn-policy-actor-v3",
        "turn-policy-actor-v4",
        "turn-policy-actor-v5",
        "turn-policy-actor-v6",
    }:
        if artifact_version == "turn-policy-actor-v1":
            raise ValueError(
                "legacy mixture-quantity actor is unsafe for deterministic BC; retrain it"
            )
        raise ValueError("unsupported turn-policy actor artifact")
    architecture_payload = dict(cast(Mapping[str, Any], raw["architecture"]))
    if "advisor_features" in architecture_payload:
        if int(architecture_payload.pop("advisor_features")) != 0:
            raise ValueError("legacy actors with heuristic adviser inputs are unsupported")
        architecture_payload["fact_dropout"] = architecture_payload.pop("advisor_dropout", 0.0)
        architecture_payload.update(
            {
                "derived_fact_version": None,
                "turn_fact_features": 0,
                "prefix_fact_features": 0,
                "candidate_fact_features": 0,
            }
        )
    architecture = ActorArchitecture.model_validate(architecture_payload)
    model = TurnPolicyNet(architecture)
    model_state = raw.get("model_state")
    if not isinstance(model_state, Mapping):
        raise ValueError("turn-policy actor artifact lacks model state")
    load_causal_actor_state(model, model_state)
    model.to(device).eval()
    keys = tuple(str(key) for key in cast(Sequence[object], raw["action_keys"]))
    if len(keys) != architecture.action_tokens:
        raise ValueError("actor artifact vocabulary differs from its architecture")
    fact_version = raw.get("derived_fact_version")
    if fact_version is not None and not isinstance(fact_version, str):
        raise ValueError("actor artifact derived-fact version is invalid")
    if fact_version != architecture.derived_fact_version:
        raise ValueError("actor artifact derived-fact identity differs from its architecture")
    economic_version = raw.get("economic_feature_version")
    if economic_version is not None and not isinstance(economic_version, str):
        raise ValueError("actor artifact economic-feature version is invalid")
    if economic_version != architecture.economic_feature_version:
        raise ValueError("actor artifact economic-feature identity differs from its architecture")
    if artifact_version == "turn-policy-actor-v6" and raw.get(
        "action_codec_version"
    ) != CURRENT_ACTIONS.version:
        raise ValueError("actor artifact action-codec identity is invalid")
    return model, keys, str(raw["actor_encoder_version"]), fact_version


class BaselineAgent:
    """Unchanged deterministic planner retained only as a named incumbent."""

    def __init__(self, backend: BackendApi, configuration: Mapping[str, Any]) -> None:
        """Bind a fresh native planner."""
        self._planner = backend.native_planner(dict(configuration), {"scheduler": "route_aware"})

    def act(self, observation: Mapping[str, Any]) -> dict[str, Any]:
        """Return one official action."""
        return cast(dict[str, Any], self._planner.act(dict(observation)))


class TurnPolicyAgent:
    """Episode-local recurrent actor with one parse and one format boundary per turn."""

    def __init__(
        self,
        backend: BackendApi,
        configuration: Mapping[str, Any],
        artifact: Path,
        device: str,
        unit_limit: int,
        *,
        sample: bool = False,
        cpu_threads: int = 1,
    ) -> None:
        """Load a frozen actor and validate it against the native numeric ABI."""
        self._backend = backend
        self._configuration = dict(configuration)
        self._device = torch.device(device)
        if cpu_threads < 1:
            raise ValueError("cpu_threads must be positive")
        if self._device.type == "cpu":
            torch.set_num_threads(cpu_threads)
        self._model, self._keys, encoder_version, fact_version = load_actor(artifact, self._device)
        self._unit_limit = unit_limit
        self._sample = sample
        codec = cast(Mapping[str, Any], backend.action_codec_spec())
        native_keys = tuple(str(key) for key in cast(Sequence[object], codec["keys"]))
        if self._keys != native_keys:
            raise ValueError("actor artifact and native action codec vocabularies differ")
        encoder = cast(Mapping[str, Any], backend.actor_encoder_spec())
        architecture = self._model.architecture
        if encoder_version != str(encoder["version"]):
            raise ValueError("actor artifact and native observation encoders differ")
        if (
            architecture.board_shape[1] != int(encoder["board_channels"])
            or architecture.unit_shape[2] != int(encoder["unit_feat"])
            or architecture.global_features != int(encoder["global_feat"])
            or architecture.unit_shape[1] != unit_limit
        ):
            raise ValueError("actor architecture differs from the native tensor ABI")
        fact_spec = cast(Mapping[str, Any], backend.derived_fact_spec())
        fact_widths = (
            int(fact_spec["turn_features"]),
            int(fact_spec["prefix_features"]),
            int(fact_spec["candidate_features"]),
        )
        architecture_fact_widths = (
            architecture.turn_fact_features,
            architecture.prefix_fact_features,
            architecture.candidate_fact_features,
        )
        self._uses_facts = any(architecture_fact_widths)
        if self._uses_facts and (
            architecture_fact_widths != fact_widths
            or architecture.derived_fact_version != str(fact_spec["version"])
            or fact_version != str(fact_spec["version"])
        ):
            raise ValueError("actor artifact and native derived-fact contracts differ")
        self._opponent_bounds = (
            OpponentInventoryBounds(int(fact_spec["products"])) if self._uses_facts else None
        )
        self._economic_layout: EconomicStateLayout | None = None
        if architecture.economic_feature_version is not None:
            state_spec = cast(
                Mapping[str, int],
                backend.gpu_policy_state_spec(
                    architecture.board_shape[-1],
                    unit_limit,
                ),
            )
            self._economic_layout = EconomicStateLayout.from_spec(
                state_spec,
                board_size=architecture.board_shape[-1],
                unit_limit=unit_limit,
            )
        board_size = self._configuration.get("boardSize")
        if board_size is not None and architecture.board_shape[2:] != (
            int(board_size),
            int(board_size),
        ):
            raise ValueError("actor board shape differs from the resolved environment")
        self._unit_tokens = int(codec["unit_tokens"])
        self._market_stop = int(codec["market_stop_token"])
        self._has_quantity = np.asarray(codec["has_quantity"], dtype=np.bool_)
        self._max_market_orders = int(self._configuration["maxMarketOrdersPerTurn"])
        self._unit_mask = (
            torch.arange(self._model.architecture.action_tokens, device=self._device)
            < self._unit_tokens
        )
        self._market_mask = ~self._unit_mask
        self._history: HistoryState | None = None
        self._strategy: Tensor | None = None
        self._previous_tokens = torch.zeros(
            (1, self._model.architecture.max_decisions),
            dtype=torch.long,
            device=self._device,
        )
        self._previous_quantities = torch.zeros_like(self._previous_tokens)
        self._previous_mask = torch.zeros_like(self._previous_tokens, dtype=torch.bool)
        self._last_step: int | None = None
        self._turns = 0
        self._decisions = 0

    def reset(self) -> None:
        """Drop all episode-local history and previous-action tokens."""
        self._history = None
        self._strategy = None
        self._previous_tokens.zero_()
        self._previous_quantities.zero_()
        self._previous_mask.zero_()
        self._last_step = None
        if self._opponent_bounds is not None:
            self._opponent_bounds.reset()

    def _as_tensor(self, value: NumericFeatureArray) -> Tensor:
        tensor = torch.from_numpy(value)
        return tensor.to(self._device, non_blocking=self._device.type == "cuda")

    def act_numeric(
        self, observation: NumericObservation, step: int, session: Any | None = None
    ) -> NumericAction:
        """Choose one action sequence from already encoded contiguous arrays."""
        if step == 0 or self._last_step is None or step != self._last_step + 1:
            self.reset()
        board_array, unit_array, global_array = observation
        board = self._as_tensor(board_array)[None]
        units = self._as_tensor(unit_array)[None]
        globals_ = self._as_tensor(global_array)[None]
        observed_units = int(np.count_nonzero(unit_array[0, :, 0] > 0.5))
        unit_count = (
            int(session.unit_count)
            if session is not None
            else max(1, min(observed_units, self._unit_limit))
        )
        turn_facts: Tensor | None = None
        turn_fact_mask: Tensor | None = None
        economic_state: Tensor | None = None
        if self._economic_layout is not None:
            if session is None:
                raise ValueError("economic features require a native policy session")
            state_array = np.asarray(session.gpu_state(), dtype=np.int64)
            if state_array.shape != (self._economic_layout.width,):
                raise ValueError("native economic state differs from the actor")
            economic_state = torch.as_tensor(
                state_array,
                dtype=torch.int64,
                device=self._device,
            )[None]
        if self._uses_facts:
            if session is None or self._opponent_bounds is None:
                raise ValueError("exact derived facts require a native policy session")
            lower, upper = self._opponent_bounds.update(
                cast(Mapping[str, Any], session.flow_snapshot())
            )
            fact_array = np.asarray(session.turn_facts(lower, upper), dtype=np.float32)
            expected = self._model.architecture.turn_fact_features
            if fact_array.ndim != 2 or fact_array.shape[1] != expected:
                raise ValueError("native turn facts differ from the actor architecture")
            turn_facts = self._as_tensor(fact_array)[None]
            turn_fact_mask = torch.ones(turn_facts.shape[:2], dtype=torch.bool, device=self._device)
        with torch.inference_mode():
            context, self._history, self._strategy, _ = self._model.start_turn(
                board,
                units,
                globals_,
                self._previous_tokens,
                self._previous_quantities,
                self._previous_mask,
                self._history,
                turn_facts,
                turn_fact_mask,
                economic_state,
                self._strategy,
                sample_skill=self._sample,
            )
            action_state = self._model.action.initial_state(context)
            turn_tokens = torch.zeros(
                (self._model.architecture.max_decisions,),
                dtype=torch.long,
                device=self._device,
            )
            turn_quantities = torch.zeros_like(turn_tokens)
            previous_token: Tensor | None = None
            previous_quantity: Tensor | None = None
            decision_count = 0
            for decision in range(self._model.architecture.max_decisions):
                if session is not None:
                    if int(session.phase) == 2:
                        break
                    phase = int(session.phase)
                else:
                    phase = 0 if decision < unit_count else 1
                    if phase == 1 and decision - unit_count >= self._max_market_orders:
                        break
                next_phase = torch.tensor([phase], dtype=torch.long, device=self._device)
                prefix_facts: Tensor | None = None
                candidate_facts: Tensor | None = None
                if self._uses_facts:
                    if session is None:
                        raise ValueError("derived facts require a native policy session")
                    prefix_array = np.asarray(session.prefix_facts(), dtype=np.float32)
                    candidate_array = np.asarray(session.candidate_facts(), dtype=np.float32)
                    if prefix_array.shape != (
                        self._model.architecture.prefix_fact_features,
                    ) or candidate_array.shape != (
                        self._model.architecture.action_tokens,
                        self._model.architecture.candidate_fact_features,
                    ):
                        raise ValueError("native decision facts differ from the actor architecture")
                    prefix_facts = self._as_tensor(prefix_array)[None]
                    candidate_facts = self._as_tensor(candidate_array)[None]
                economic_prefix: Tensor | None = None
                economic_candidates: Tensor | None = None
                if self._model.economics is not None:
                    if economic_state is None:
                        raise RuntimeError("economic actor lost its turn state")
                    economic_prefix = self._model.economics.prefix_features(
                        economic_state,
                        next_phase,
                    )
                    economic_candidates = self._model.economics.candidate_features(
                        economic_state,
                        next_phase,
                    )
                logits, decision_hidden, action_state = self._model.action.next_cached(
                    previous_token,
                    previous_quantity,
                    next_phase,
                    context,
                    action_state,
                    prefix_facts,
                    candidate_facts,
                    economic_prefix,
                    economic_candidates,
                )
                allowed = (
                    torch.as_tensor(
                        np.asarray(session.legal_mask(), dtype=np.bool_),
                        device=self._device,
                    )
                    if session is not None
                    else (self._unit_mask if phase == 0 else self._market_mask)
                )
                logits = logits.float().masked_fill(~allowed[None], -torch.inf)
                token = (
                    torch.multinomial(torch.softmax(logits, dim=-1), 1).squeeze(-1)
                    if self._sample
                    else logits.argmax(dim=-1)
                )
                token_value = int(token.item())
                selected_candidate_facts = (
                    candidate_facts[torch.arange(token.shape[0], device=token.device), token]
                    if candidate_facts is not None
                    else None
                )
                economic_quantities = (
                    None
                    if self._model.economics is None or economic_state is None
                    else self._model.economics.quantity_features(economic_state, token)
                )
                quantity_logits = self._model.action.quantity_logits(
                    decision_hidden,
                    token,
                    selected_candidate_facts,
                    economic_quantities,
                )
                quantity = (
                    self._model.choose_quantity(quantity_logits, sample=self._sample)
                    if self._has_quantity[token_value]
                    else torch.zeros_like(token)
                )
                turn_tokens[decision] = token[0]
                turn_quantities[decision] = quantity[0]
                previous_token = token
                previous_quantity = quantity
                decision_count = decision + 1
                if session is not None:
                    session.select(token_value, int(quantity.item()))
                    if economic_state is not None and self._model.economics is not None:
                        apply_selection(
                            economic_state,
                            token,
                            quantity,
                            torch.ones_like(token, dtype=torch.bool),
                            self._model.economics.layout,
                        )
                elif token_value == self._market_stop:
                    break
        if self._opponent_bounds is not None and session is not None:
            self._opponent_bounds.record_own_flow(session.own_market_flow_bounds())
        prefix_tokens = turn_tokens[:decision_count][None]
        prefix_quantities = turn_quantities[:decision_count][None]
        self._previous_tokens.zero_()
        self._previous_quantities.zero_()
        self._previous_mask.zero_()
        self._previous_tokens[:, :decision_count] = prefix_tokens
        self._previous_quantities[:, :decision_count] = prefix_quantities
        self._previous_mask[:, :decision_count] = True
        self._last_step = step
        self._turns += 1
        self._decisions += decision_count
        return NumericAction(
            tokens=prefix_tokens[0].cpu().numpy().astype(np.int64, copy=False),
            quantities=prefix_quantities[0].cpu().numpy().astype(np.int64, copy=False),
            decision_count=decision_count,
            unit_count=unit_count,
        )

    def act(self, observation: Mapping[str, Any]) -> dict[str, Any]:
        """Parse once at the Kaggle boundary and return one official action dict."""
        session = self._backend.policy_session(
            dict(observation), self._configuration, self._unit_limit
        )
        encoded = session.encode()
        arrays = cast(NumericObservation, tuple(np.asarray(value) for value in encoded))
        self.act_numeric(arrays, int(observation["step"]), session)
        return cast(dict[str, Any], session.action())

    def act_native(self, engine: Any, player: int) -> NumericAction:
        """Act directly on a native engine without constructing an observation dict."""
        session = engine.policy_session(player, self._unit_limit)
        encoded = session.encode()
        arrays = cast(NumericObservation, tuple(np.asarray(value) for value in encoded))
        return self.act_numeric(arrays, int(engine.step_index), session)

    def diagnostics(self) -> dict[str, object]:
        """Return bounded runtime facts for closed-loop reports."""
        return {
            "turns": self._turns,
            "decisions": self._decisions,
            "history_position": 0 if self._history is None else self._history.position,
            "numeric_boundary": True,
            "derived_fact_version": self._model.architecture.derived_fact_version,
        }


__all__ = ["BaselineAgent", "NumericAction", "TurnPolicyAgent", "load_actor"]
