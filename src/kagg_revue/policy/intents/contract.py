"""Measured native ABI contract for canonical intent-ledger policies."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any


def _names(value: object, name: str) -> tuple[str, ...]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        raise TypeError(f"intent {name} must be a sequence")
    return tuple(str(item) for item in value)


@dataclass(frozen=True)
class NativeIntentContract:
    """Shape and enum identity reported by the compiled intent backend."""

    version: str
    spec_version: int
    board_size: int
    candidate_fields: tuple[str, ...]
    candidate_features: tuple[str, ...]
    ledger_fields: tuple[str, ...]
    status_fields: tuple[str, ...]
    work_fields: tuple[str, ...]
    position_fields: tuple[str, ...]
    market_fields: tuple[str, ...]
    choice_count: int
    asset_kind_count: int
    maintenance_count: int
    product_collection_count: int
    fertilizer_collection_count: int
    priority_count: int
    work_kind_count: int
    position_role_count: int
    directive_operation_count: int
    market_order_count: int
    phase_count: int
    status_count: int
    block_reason_count: int
    done_phase: int
    commit_choice: int

    @classmethod
    def from_spec(
        cls,
        raw: Mapping[str, Any],
        *,
        board_size: int,
    ) -> NativeIntentContract:
        """Validate a native spec without duplicating enum numeric values."""
        if board_size < 1:
            raise ValueError("intent board size must be positive")

        def enum(name: str) -> dict[str, int]:
            value = raw.get(name)
            if not isinstance(value, Mapping) or not value:
                raise TypeError(f"intent {name} enum is missing")
            result = {str(key): int(item) for key, item in value.items()}
            if set(result.values()) != set(range(len(result))):
                raise ValueError(f"intent {name} enum must be contiguous")
            return result

        choices = enum("choice_kinds")
        phases = enum("phases")
        asset_kinds = enum("asset_kinds")
        maintenance = enum("maintenance")
        product_collection = enum("product_collection")
        fertilizer_collection = enum("fertilizer_collection")
        priorities = enum("priorities")
        work_kinds = enum("work_kinds")
        position_roles = enum("position_roles")
        directive_operations = enum("directive_operations")
        market_order_kinds = enum("market_order_kinds")
        statuses = enum("statuses")
        block_reasons = enum("block_reasons")
        contract = cls(
            version=str(raw["abi_version"]),
            spec_version=int(raw["version"]),
            board_size=board_size,
            candidate_fields=_names(raw.get("candidate_fields"), "candidate fields"),
            candidate_features=_names(raw.get("candidate_features"), "candidate features"),
            ledger_fields=_names(raw.get("ledger_fields"), "ledger fields"),
            status_fields=_names(raw.get("status_fields"), "status fields"),
            work_fields=_names(raw.get("work_fields"), "work fields"),
            position_fields=_names(raw.get("position_fields"), "position fields"),
            market_fields=_names(raw.get("market_fields"), "market fields"),
            choice_count=len(choices),
            asset_kind_count=len(asset_kinds),
            maintenance_count=len(maintenance),
            product_collection_count=len(product_collection),
            fertilizer_collection_count=len(fertilizer_collection),
            priority_count=len(priorities),
            work_kind_count=len(work_kinds),
            position_role_count=len(position_roles),
            directive_operation_count=len(directive_operations),
            market_order_count=len(market_order_kinds),
            phase_count=len(phases),
            status_count=len(statuses),
            block_reason_count=len(block_reasons),
            done_phase=phases["DONE"],
            commit_choice=choices["COMMIT"],
        )
        contract._validate_widths(raw)
        return contract

    def _validate_widths(self, raw: Mapping[str, Any]) -> None:
        expected = (
            ("candidate_field_count", len(self.candidate_fields)),
            ("candidate_feature_count", len(self.candidate_features)),
            ("ledger_field_count", len(self.ledger_fields)),
            ("status_field_count", len(self.status_fields)),
            ("work_field_count", len(self.work_fields)),
        )
        for name, measured in expected:
            if int(raw[name]) != measured:
                raise ValueError(f"intent {name} differs from its field names")

    @property
    def tile_count(self) -> int:
        """Return the flattened own-farm surface."""
        return self.board_size**2


__all__ = ["NativeIntentContract"]
