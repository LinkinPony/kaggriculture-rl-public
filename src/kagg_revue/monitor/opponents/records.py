"""Compact opponent identities and physical-game panels from committed updates."""

from __future__ import annotations

import math
from array import array
from dataclasses import dataclass, field
from typing import Any

COUNTS = ("games", "wins", "ties", "losses")
VALUES = ("mean_terminal_cash", "mean_cash_difference", "score", "probability")


def finite(value: object) -> float | None:
    """Accept finite JSON numbers, excluding booleans and numeric strings."""
    if isinstance(value, int | float) and not isinstance(value, bool) and math.isfinite(value):
        return float(value)
    return None


def identity(entry: dict[str, Any]) -> dict[str, Any] | None:
    """Keep authenticated keys; never identify a model by its update number alone."""
    kind = entry.get("kind", "history")
    key = entry.get("key")
    sha = entry.get("sha256")
    if not isinstance(key, str) or not key:
        if kind != "history" or not isinstance(sha, str) or not sha:
            return None
        key = f"history:{sha}"
    if kind not in {"history", "script"} or not key.startswith(f"{kind}:"):
        return None
    result: dict[str, Any] = {
        name: entry[name]
        for name in ("name", "path", "source_run", "update", "sha256")
        if name in entry
    }
    result.update(key=key, kind=kind)
    if kind == "history":
        result.setdefault("sha256", key.removeprefix("history:"))
        result.setdefault("name", entry.get("path", key))
    return result


@dataclass
class OpponentRecord:
    """One identity with packed columns, avoiding a Python object per training round."""

    metadata: dict[str, Any]
    steps: array[int] = field(default_factory=lambda: array("q"))
    counts: dict[str, array[int]] = field(
        default_factory=lambda: {name: array("q") for name in COUNTS}
    )
    values: dict[str, array[float]] = field(
        default_factory=lambda: {name: array("d") for name in VALUES}
    )

    def append(self, update: int, panel: dict[str, Any], sampling: dict[str, Any]) -> None:
        """Store exactly one globally reduced physical-game panel."""
        self.steps.append(update)
        for name in COUNTS:
            self.counts[name].append(panel[name])
        for name in VALUES:
            source = sampling if name in {"score", "probability"} else panel
            value = finite(source.get(name))
            self.values[name].append(value if value is not None else math.nan)


@dataclass
class OpponentIndex:
    """Accumulate identifiable outcomes without guessing missing legacy identities."""

    records: dict[str, OpponentRecord] = field(default_factory=dict)
    unassigned_games: int = 0
    invalid_panels: int = 0

    def append(self, row: dict[str, Any], update: int) -> None:
        """Index only global panels, excluding self-play and per-worker duplicates."""
        panels = row.get("populations")
        if not isinstance(panels, dict):
            return
        pfsp = row.get("pfsp")
        pfsp = pfsp if isinstance(pfsp, dict) else {}
        selected = pfsp.get("selected")
        selected = selected if isinstance(selected, dict) else {}
        for name, panel in panels.items():
            if name == "self_play" or not isinstance(panel, dict):
                continue
            games = finite(panel.get("games"))
            if games == 0:
                continue
            if not all(
                isinstance(panel.get(field), int)
                and not isinstance(panel[field], bool)
                and 0 <= panel[field] < 2**63
                for field in COUNTS
            ) or games != sum(panel[field] for field in COUNTS[1:]):
                self.invalid_panels += 1
                continue
            candidate: dict[str, Any] = {}
            sampling: dict[str, Any] = {}
            if name == "historical_self_play":
                if selected.get("kind", "history") == "history":
                    candidate = selected or row.get("opponent") or {}
                    sampling = selected
            elif selected.get("kind") == "script" and selected.get("name") == name:
                candidate = sampling = selected
            metadata = identity(candidate) if isinstance(candidate, dict) else None
            fallback = row.get("opponent")
            if metadata is None and name == "historical_self_play" and isinstance(fallback, dict):
                metadata = identity(fallback)
            if metadata is None:
                self.unassigned_games += panel["games"]
                continue
            record = self.records.setdefault(metadata["key"], OpponentRecord(metadata))
            record.metadata.update(metadata)
            record.append(update, panel, sampling)
