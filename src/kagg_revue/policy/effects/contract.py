"""Measured native ABI contract for atomic-effect policies."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any


def _names(value: object, name: str) -> tuple[str, ...]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        raise TypeError(f"effect {name} must be a sequence")
    return tuple(str(item) for item in value)


@dataclass(frozen=True)
class NativeEffectContract:
    """Shape and enum identity reported by the compiled effect backend."""

    version: str
    spec_version: int
    board_size: int
    candidate_fields: tuple[str, ...]
    candidate_features: tuple[str, ...]
    job_fields: tuple[str, ...]
    action_fields: tuple[str, ...]
    request_count: int
    resource_count: int
    phase_count: int
    work_phase: int
    market_phase: int
    done_phase: int
    stop_request: int

    @classmethod
    def from_spec(
        cls,
        raw: Mapping[str, Any],
        *,
        board_size: int,
    ) -> NativeEffectContract:
        """Validate enum continuity and measured native field widths."""
        if board_size < 1:
            raise ValueError("effect board size must be positive")

        def enum(name: str) -> dict[str, int]:
            value = raw.get(name)
            if not isinstance(value, Mapping) or not value:
                raise TypeError(f"effect {name} enum is missing")
            result = {str(key): int(item) for key, item in value.items()}
            if set(result.values()) != set(range(len(result))):
                raise ValueError(f"effect {name} enum must be contiguous")
            return result

        requests = enum("request_kinds")
        resources = enum("resource_kinds")
        phases = enum("phases")
        contract = cls(
            version=str(raw["abi_version"]),
            spec_version=int(raw["version"]),
            board_size=board_size,
            candidate_fields=_names(raw.get("candidate_fields"), "candidate fields"),
            candidate_features=_names(raw.get("candidate_features"), "candidate features"),
            job_fields=_names(raw.get("job_fields"), "job fields"),
            action_fields=_names(raw.get("action_fields"), "action fields"),
            request_count=len(requests),
            resource_count=len(resources),
            phase_count=len(phases),
            work_phase=phases["WORK"],
            market_phase=phases["MARKET"],
            done_phase=phases["DONE"],
            stop_request=requests["STOP"],
        )
        measured = (
            ("candidate_field_count", len(contract.candidate_fields)),
            ("candidate_feature_count", len(contract.candidate_features)),
            ("job_field_count", len(contract.job_fields)),
            ("action_field_count", len(contract.action_fields)),
        )
        for name, width in measured:
            if int(raw[name]) != width:
                raise ValueError(f"effect {name} differs from its field names")
        return contract

    @property
    def tile_count(self) -> int:
        """Return the flattened own-farm surface."""
        return self.board_size**2


__all__ = ["NativeEffectContract"]
