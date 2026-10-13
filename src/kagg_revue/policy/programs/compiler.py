"""High-level Python owner for the native persistent program compiler."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, cast

import numpy as np

from kagg_revue.policy.programs.contract import (
    MarketDecision,
    ProgramPhase,
    UnitDecision,
)
from kagg_revue.policy.programs.legality import MarketMasks, UnitMasks
from kagg_revue.policy.programs.native import NativeProgramContract
from kagg_revue.policy.programs.schema import CompiledProgram, ProgramDecisionTrace


def _scalar_int(value: object, name: str) -> int:
    if not isinstance(value, (int, np.integer)) or isinstance(value, bool):
        raise ValueError(f"native conditional-program {name} must be an integer")
    return int(value)


class ProgramSession:
    """Retain options and an exact trace around one native actor session."""

    def __init__(
        self,
        configuration: Mapping[str, object] | None = None,
        unit_limit: int = 65,
        *,
        backend: Any | None = None,
    ) -> None:
        """Create one compiler session against the validated native ABI."""
        if backend is None:
            from kagg_revue.native import _revue_native as backend_module

            backend = backend_module
        resolved = None if configuration is None else dict(configuration)
        self._backend = backend
        self._handle = backend.ConditionalProgramSession(resolved, unit_limit)
        self.contract = NativeProgramContract.from_spec(
            cast(
                Mapping[str, object],
                backend.conditional_program_spec(resolved, unit_limit),
            )
        )
        self._unit_decisions: list[UnitDecision] = []
        self._unit_masks: list[UnitMasks] = []
        self._market_decisions: list[MarketDecision] = []
        self._market_masks: list[MarketMasks] = []

    @property
    def handle(self) -> Any:
        """Underlying native owner used by fused rollout calls."""
        return self._handle

    @property
    def phase(self) -> ProgramPhase:
        """Current branch in the turn-level autoregressive program."""
        return ProgramPhase(int(self._handle.phase))

    def reset(self) -> None:
        """Clear persistent options and the current program trace."""
        self._handle.reset()
        self._clear_trace()

    def decision_required(self, engine: Any, player: int) -> bool:
        """Refresh from one native engine and report whether sampling remains."""
        previous = self.phase
        required = bool(self._handle.decision_required(engine, player))
        if required and previous is ProgramPhase.DONE:
            self._clear_trace()
        return required

    def observation(self, engine: Any, player: int) -> Mapping[str, object]:
        """Return the exact native masks for the current decision."""
        previous = self.phase
        raw = cast(Mapping[str, object], self._handle.observation(engine, player))
        if previous is ProgramPhase.DONE:
            self._clear_trace()
        return raw

    def observation_visible(self, observation: Mapping[str, object]) -> Mapping[str, object]:
        """Return masks using only the official deployment observation."""
        previous = self.phase
        raw = cast(
            Mapping[str, object],
            self._handle.observation_visible(dict(observation)),
        )
        if previous is ProgramPhase.DONE:
            self._clear_trace()
        return raw

    def select_unit(self, engine: Any, player: int, decision: UnitDecision) -> None:
        """Apply one unit choice to the compiler's sequential shadow state."""
        raw = self.observation(engine, player)
        self._select_unit(raw, decision, engine, player)

    def select_unit_visible(
        self, observation: Mapping[str, object], decision: UnitDecision
    ) -> None:
        """Apply one unit choice through the deployment-only boundary."""
        raw = self.observation_visible(observation)
        self._select_unit(raw, decision, dict(observation))

    def select_market(self, engine: Any, player: int, decision: MarketDecision) -> None:
        """Apply one ordered market choice and update projected resources."""
        raw = self.observation(engine, player)
        self._select_market(raw, decision, engine, player)

    def select_market_visible(
        self, observation: Mapping[str, object], decision: MarketDecision
    ) -> None:
        """Apply one market choice through the deployment-only boundary."""
        raw = self.observation_visible(observation)
        self._select_market(raw, decision, dict(observation))

    def compile(self, engine: Any, player: int) -> CompiledProgram:
        """Compile a completed program into the numeric official action ABI."""
        raw = cast(Mapping[str, object], self._handle.action_numeric(engine, player))
        return self._compiled(raw)

    def compile_visible(self, observation: Mapping[str, object]) -> CompiledProgram:
        """Compile a completed program using the deployment observation."""
        raw = cast(
            Mapping[str, object],
            self._handle.action_numeric_visible(dict(observation)),
        )
        return self._compiled(raw)

    def _select_unit(
        self,
        raw: Mapping[str, object],
        decision: UnitDecision,
        *native_args: object,
    ) -> None:
        if ProgramPhase(_scalar_int(raw["phase"], "phase")) is not ProgramPhase.UNIT:
            raise ValueError("conditional program is not awaiting a unit decision")
        masks = UnitMasks.from_raw(raw, self.contract)
        values = (
            int(decision.control),
            int(decision.task),
            decision.target,
            decision.argument,
            int(decision.direction),
            int(decision.raw_operation),
            int(decision.quantity_mode),
            decision.exact_quantity,
        )
        if len(native_args) == 2:
            self._handle.select(*native_args, *values)
        else:
            self._handle.select_visible(*native_args, *values)
        self._unit_masks.append(masks)
        self._unit_decisions.append(decision)

    def _select_market(
        self,
        raw: Mapping[str, object],
        decision: MarketDecision,
        *native_args: object,
    ) -> None:
        if ProgramPhase(_scalar_int(raw["phase"], "phase")) is not ProgramPhase.MARKET:
            raise ValueError("conditional program is not awaiting a market decision")
        masks = MarketMasks.from_raw(raw, self.contract)
        values = (
            0,
            int(decision.order_type),
            -1,
            decision.item,
            0,
            0,
            int(decision.quantity_mode),
            decision.exact_quantity,
        )
        if len(native_args) == 2:
            self._handle.select(*native_args, *values)
        else:
            self._handle.select_visible(*native_args, *values)
        self._market_masks.append(masks)
        self._market_decisions.append(decision)

    def _compiled(self, raw: Mapping[str, object]) -> CompiledProgram:
        if bool(raw["requires_decision"]):
            raise ValueError("conditional program still requires a decision")
        result = CompiledProgram(
            tokens=np.ascontiguousarray(raw["tokens"], dtype=np.int64),
            quantities=np.ascontiguousarray(raw["quantities"], dtype=np.int64),
            decision_count=_scalar_int(raw["decision_count"], "decision count"),
            unit_count=_scalar_int(raw["unit_count"], "unit count"),
            action=dict(cast(Mapping[str, object], raw["action"])),
            trace=ProgramDecisionTrace(
                unit_decisions=tuple(self._unit_decisions),
                unit_masks=tuple(self._unit_masks),
                market_decisions=tuple(self._market_decisions),
                market_masks=tuple(self._market_masks),
            ),
        )
        result.validate(self.contract.maximum_decisions)
        return result

    def _clear_trace(self) -> None:
        self._unit_decisions.clear()
        self._unit_masks.clear()
        self._market_decisions.clear()
        self._market_masks.clear()


__all__ = ["ProgramSession"]
