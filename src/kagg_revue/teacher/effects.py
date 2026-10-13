"""Causal Rank8 proposals on the native atomic-effect candidate surface."""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any, cast

import numpy as np
from numpy.typing import NDArray

from kagg_revue.teacher.submission import SubmissionTeacher, SubmissionTeacherArtifact

_DIRECTIONS = {
    "NORTH": (0, -1),
    "SOUTH": (0, 1),
    "EAST": (1, 0),
    "WEST": (-1, 0),
}
_TARGET_EFFECTS = {
    "PLANT",
    "WATER",
    "HARVEST",
    "FERTILIZE",
    "DIG",
    "BUILD_COOP",
    "BUILD_PASTURE",
    "FEED",
    "CARE",
    "COLLECT_FERTILIZER",
}
_MARKET_EFFECTS = {
    "BUY_SEED",
    "BUY_PRODUCT",
    "BUY_ANIMAL",
    "SELL",
    "HIRE",
    "BUY_LAND",
}
_ANIMALS = {"GOOSE", "COW", "SHEEP"}


def _mapping(value: object, name: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise TypeError(f"effect teacher {name} must be a mapping")
    return cast(Mapping[str, Any], value)


def _sequence(value: object, name: str) -> Sequence[Any]:
    if not isinstance(value, Sequence) or isinstance(value, str | bytes):
        raise TypeError(f"effect teacher {name} must be a sequence")
    return value


def _integer(value: object, name: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise TypeError(f"effect teacher {name} must be an integer")
    return value


@dataclass(frozen=True, slots=True)
class EffectProposal:
    """One complete native work request derived from the current raw action."""

    operation: str
    request_kind: int
    unit: int
    target: int = -1
    item: int = -1
    quantity: int = 0


@dataclass(frozen=True, slots=True)
class EffectTeacherPlan:
    """Immutable Rank8 intent for one actor-visible official-turn state."""

    work: tuple[EffectProposal, ...]
    market: tuple[tuple[str, int, int], ...]
    route_id: object
    first_event_day: object


class Rank8EffectTeacher:
    """Translate only actor-visible Rank8 requests into native effect choices."""

    def __init__(
        self,
        configuration: Mapping[str, object],
        artifact: SubmissionTeacherArtifact,
        effect_spec: Mapping[str, object],
        item_names: Sequence[object],
    ) -> None:
        """Bind one submission runtime and the measured effect ABI."""
        self._teacher = SubmissionTeacher(configuration, artifact)
        self._board_size = _integer(configuration.get("boardSize"), "boardSize")
        self._shed_capacity = _integer(
            configuration.get("shedCapacity", 100), "shedCapacity"
        )
        raw_kinds = _mapping(effect_spec.get("request_kinds"), "request kinds")
        self._kinds = {str(name): _integer(value, str(name)) for name, value in raw_kinds.items()}
        required = {
            "STOP",
            "STAGE",
            "BANK",
            "LOAD",
            "UNLOAD",
            "PLACE_ANIMAL",
            "SKIP_MARKET_SLOT",
            *_TARGET_EFFECTS,
            *_MARKET_EFFECTS,
        }
        if missing := required - set(self._kinds):
            raise ValueError(f"effect teacher ABI lacks requests: {sorted(missing)}")
        self._items = {str(name): index for index, name in enumerate(item_names)}
        if not _ANIMALS.issubset(self._items):
            raise ValueError("effect teacher actor item vocabulary lacks animals")
        self._work: list[EffectProposal] = []
        self._market: list[tuple[str, int, int]] = []
        self._market_offset = 0
        self._metadata: dict[str, object] = {}
        self._diagnostics: Counter[str] = Counter()

    @staticmethod
    def _at_shed(position: tuple[int, int], board_size: int) -> bool:
        half = board_size // 2
        return position in {
            (half - 1, half - 1),
            (half, half - 1),
            (half - 1, half),
            (half, half),
        }

    def _proposal(
        self,
        action: Sequence[Any],
        position: tuple[int, int],
        unit: int,
        quantity: int,
    ) -> EffectProposal | None:
        operation = str(action[0])
        target = position[1] * self._board_size + position[0]
        item = -1
        if operation in _DIRECTIONS:
            dx, dy = _DIRECTIONS[operation]
            target_x = position[0] + dx
            target_y = position[1] + dy
            if not (0 <= target_x < self._board_size and 0 <= target_y < self._board_size):
                return None
            return EffectProposal(
                operation,
                self._kinds["STAGE"],
                unit,
                target_y * self._board_size + target_x,
            )
        if operation in _TARGET_EFFECTS:
            if operation == "PLANT":
                item = self._items[str(action[1])]
            return EffectProposal(operation, self._kinds[operation], unit, target, item)
        if operation == "PICKUP":
            if quantity <= 0:
                return None
            return EffectProposal(
                operation,
                self._kinds["LOAD"],
                unit,
                item=self._items[str(action[1])],
                quantity=quantity,
            )
        if operation == "DROP":
            return EffectProposal(operation, self._kinds["BANK"], unit)
        if operation == "PLACE":
            item_name = str(action[1])
            if item_name in _ANIMALS:
                return EffectProposal(
                    operation,
                    self._kinds["PLACE_ANIMAL"],
                    unit,
                    target,
                    self._items[item_name],
                )
            if quantity <= 0:
                return None
            return EffectProposal(
                operation,
                self._kinds["UNLOAD"],
                unit,
                item=self._items[item_name],
                quantity=quantity,
            )
        if operation == "PASS":
            return None
        raise ValueError(f"unsupported Rank8 unit operation {operation!r}")

    def prepare(self, observation: Mapping[str, object]) -> Mapping[str, object]:
        """Build current-turn work and market proposals without future state."""
        plan = self._teacher.plan(observation)
        action = _mapping(plan.get("action"), "teacher action")
        player = _integer(observation.get("player"), "observation player")
        farms = _sequence(observation.get("farms"), "farms")
        farm = _mapping(farms[player], "active farm")
        positions = [
            tuple(_sequence(farm.get("farmer"), "farmer position")),
            *(
                tuple(_sequence(value, "hand position"))
                for value in _sequence(farm.get("hands", ()), "hands")
            ),
        ]
        if any(
            len(position) != 2 or not all(isinstance(value, int) for value in position)
            for position in positions
        ):
            raise TypeError("effect teacher unit positions are malformed")
        private = _mapping(observation.get("private"), "private state")
        raw_shed = _mapping(private.get("shed"), "shed")
        raw_seeds = _mapping(private.get("seeds"), "seeds")
        raw_inventories = _sequence(private.get("inventories"), "inventories")
        inventories = [_mapping(value, "unit inventory") for value in raw_inventories]
        if len(inventories) != len(positions):
            raise ValueError("effect teacher units and inventories do not align")
        farmer = _sequence(action.get("farmer"), "farmer action")
        hands = _sequence(action.get("hands", ()), "hand actions")
        actions = [farmer, *(_sequence(value, "hand action") for value in hands)]
        if len(actions) != len(positions):
            raise ValueError("effect teacher action and live unit counts differ")

        plant_demand = Counter(
            str(unit_action[1])
            for unit_action in actions
            if unit_action and str(unit_action[0]) == "PLANT"
        )
        invalid_plants = {
            crop
            for crop, demand in plant_demand.items()
            if demand > _integer(raw_seeds.get(crop, 0), f"{crop} seed count")
        }
        shed = Counter(
            {str(name): _integer(value, f"{name} shed count") for name, value in raw_shed.items()}
        )
        room = max(0, self._shed_capacity - sum(shed.values()))
        proposals: list[EffectProposal] = []
        for unit, (raw_action, raw_position, carried) in enumerate(
            zip(actions, positions, inventories, strict=True)
        ):
            if not raw_action:
                raise ValueError("effect teacher unit action cannot be empty")
            operation = str(raw_action[0])
            position = cast(tuple[int, int], raw_position)
            if operation == "PLANT" and str(raw_action[1]) in invalid_plants:
                self._diagnostics["omitted_atomic_plant_conflict"] += 1
                continue
            if operation == "FEED" and _integer(carried.get("WHEAT", 0), "carried wheat") <= 0:
                self._diagnostics["omitted_unavailable_feed"] += 1
                continue
            if operation == "FERTILIZE" and _integer(
                carried.get("FERTILIZER", 0), "carried fertilizer"
            ) <= 0:
                self._diagnostics["omitted_unavailable_fertilize"] += 1
                continue
            if operation == "PLACE" and len(raw_action) == 2:
                item_name = str(raw_action[1])
                if item_name in _ANIMALS and _integer(
                    carried.get(item_name, 0), f"carried {item_name}"
                ) <= 0:
                    self._diagnostics["omitted_unavailable_animal"] += 1
                    continue

            quantity = 0
            if operation == "PICKUP":
                item_name = str(raw_action[1])
                if not self._at_shed(position, self._board_size):
                    self._diagnostics["omitted_remote_pickup"] += 1
                    continue
                quantity = min(
                    _integer(raw_action[2], "pickup quantity"),
                    shed[item_name],
                )
                shed[item_name] -= quantity
                room += quantity
            elif operation == "PLACE" and len(raw_action) > 2:
                item_name = str(raw_action[1])
                if not self._at_shed(position, self._board_size):
                    self._diagnostics["omitted_remote_unload"] += 1
                    continue
                quantity = min(
                    _integer(raw_action[2], "place quantity"),
                    _integer(carried.get(item_name, 0), f"carried {item_name}"),
                    room,
                )
                shed[item_name] += quantity
                room -= quantity
            elif operation == "DROP" and self._at_shed(position, self._board_size):
                for item_name, raw_count in carried.items():
                    deposited = min(_integer(raw_count, f"carried {item_name}"), room)
                    shed[str(item_name)] += deposited
                    room -= deposited
            proposal = self._proposal(raw_action, position, unit, quantity)
            if proposal is not None:
                proposals.append(proposal)
        self._work = proposals

        market: list[tuple[str, int, int]] = []
        for raw_order in _sequence(action.get("market", ()), "market orders"):
            order = _sequence(raw_order, "market order")
            if not order:
                raise ValueError("effect teacher market order cannot be empty")
            operation = str(order[0])
            if operation not in _MARKET_EFFECTS:
                raise ValueError(f"unsupported Rank8 market operation {operation!r}")
            item = -1 if operation in {"HIRE", "BUY_LAND"} else self._items[str(order[1])]
            quantity = 0 if operation in {"HIRE", "BUY_LAND"} else _integer(
                order[2], "market quantity"
            )
            market.append((operation, item, quantity))
        self._market = market
        self._market_offset = 0
        self._metadata = {
            "route_id": plan.get("route_id"),
            "first_event_day": plan.get("first_event_day"),
        }
        return plan

    @staticmethod
    def _candidate_rows(
        candidate_fields: NDArray[np.int64],
        candidate_mask: NDArray[np.bool_],
        proposal: EffectProposal,
    ) -> NDArray[np.int64]:
        matches = candidate_mask.copy()
        matches &= candidate_fields[:, 0] == proposal.request_kind
        matches &= candidate_fields[:, 1] == proposal.target
        matches &= candidate_fields[:, 2] == proposal.item + 1
        matches &= candidate_fields[:, 3] == proposal.quantity
        matches &= candidate_fields[:, 5] == proposal.unit + 1
        return np.flatnonzero(matches)

    def select_work(
        self,
        candidate_fields: NDArray[np.int64],
        candidate_mask: NDArray[np.bool_],
    ) -> int:
        """Select the earliest currently legal unit proposal, or finish work."""
        for offset, proposal in enumerate(self._work):
            matches = self._candidate_rows(candidate_fields, candidate_mask, proposal)
            if len(matches) > 1:
                raise RuntimeError("effect teacher work proposal is not canonical")
            if len(matches) == 1:
                self._work.pop(offset)
                self._diagnostics[f"selected_{proposal.operation.lower()}"] += 1
                return int(matches[0])
        for proposal in self._work:
            self._diagnostics[f"omitted_{proposal.operation.lower()}"] += 1
        self._work.clear()
        stop = np.flatnonzero(candidate_mask & (candidate_fields[:, 0] == self._kinds["STOP"]))
        if len(stop) != 1:
            raise RuntimeError("effect teacher work STOP is unavailable")
        return int(stop[0])

    def select_market(
        self,
        candidate_fields: NDArray[np.int64],
        candidate_mask: NDArray[np.bool_],
    ) -> int:
        """Select one raw market slot, preserving rejected slots explicitly."""
        if self._market_offset >= len(self._market):
            stop = np.flatnonzero(
                candidate_mask & (candidate_fields[:, 0] == self._kinds["STOP"])
            )
            if len(stop) != 1:
                raise RuntimeError("effect teacher market STOP is unavailable")
            return int(stop[0])
        operation, item, quantity = self._market[self._market_offset]
        self._market_offset += 1
        matches = candidate_mask & (candidate_fields[:, 0] == self._kinds[operation])
        if item >= 0:
            matches &= candidate_fields[:, 2] == item + 1
        indices = np.flatnonzero(matches)
        if quantity > 0 and len(indices):
            exact = indices[candidate_fields[indices, 3] == quantity]
            if len(exact) == 1:
                self._diagnostics[f"selected_{operation.lower()}"] += 1
                return int(exact[0])
            partial = indices[candidate_fields[indices, 3] <= quantity]
            if len(partial):
                quantities = candidate_fields[partial, 3]
                selected = int(partial[int(np.argmax(quantities))])
                self._diagnostics[f"partial_{operation.lower()}"] += 1
                return selected
        elif quantity == 0 and len(indices) == 1:
            self._diagnostics[f"selected_{operation.lower()}"] += 1
            return int(indices[0])
        skip = np.flatnonzero(
            candidate_mask
            & (candidate_fields[:, 0] == self._kinds["SKIP_MARKET_SLOT"])
        )
        if len(skip) != 1:
            raise RuntimeError("effect teacher market-slot skip is unavailable")
        self._diagnostics[f"skipped_{operation.lower()}"] += 1
        return int(skip[0])

    def snapshot(self) -> EffectTeacherPlan:
        """Freeze the current proposal list for labeling student-visited states."""
        return EffectTeacherPlan(
            work=tuple(self._work),
            market=tuple(self._market),
            route_id=self._metadata.get("route_id"),
            first_event_day=self._metadata.get("first_event_day"),
        )

    def label_work(
        self,
        plan: EffectTeacherPlan,
        candidate_fields: NDArray[np.int64],
        candidate_mask: NDArray[np.bool_],
    ) -> int:
        """Label a student work prefix without consuming the teacher plan."""
        for proposal in plan.work:
            matches = self._candidate_rows(candidate_fields, candidate_mask, proposal)
            if len(matches) > 1:
                raise RuntimeError("effect teacher work proposal is not canonical")
            if len(matches) == 1:
                return int(matches[0])
        stop = np.flatnonzero(
            candidate_mask & (candidate_fields[:, 0] == self._kinds["STOP"])
        )
        if len(stop) != 1:
            raise RuntimeError("effect teacher work STOP is unavailable")
        return int(stop[0])

    def label_market(
        self,
        plan: EffectTeacherPlan,
        slot: int,
        candidate_fields: NDArray[np.int64],
        candidate_mask: NDArray[np.bool_],
    ) -> int:
        """Label one student market prefix at its actual slot position."""
        if slot < 0:
            raise ValueError("effect teacher market slot cannot be negative")
        if slot >= len(plan.market):
            stop = np.flatnonzero(
                candidate_mask & (candidate_fields[:, 0] == self._kinds["STOP"])
            )
            if len(stop) != 1:
                raise RuntimeError("effect teacher market STOP is unavailable")
            return int(stop[0])
        operation, item, quantity = plan.market[slot]
        matches = candidate_mask & (
            candidate_fields[:, 0] == self._kinds[operation]
        )
        if item >= 0:
            matches &= candidate_fields[:, 2] == item + 1
        indices = np.flatnonzero(matches)
        if quantity > 0 and len(indices):
            exact = indices[candidate_fields[indices, 3] == quantity]
            if len(exact) == 1:
                return int(exact[0])
            partial = indices[candidate_fields[indices, 3] <= quantity]
            if len(partial):
                quantities = candidate_fields[partial, 3]
                return int(partial[int(np.argmax(quantities))])
        elif quantity == 0 and len(indices) == 1:
            return int(indices[0])
        skip = np.flatnonzero(
            candidate_mask
            & (candidate_fields[:, 0] == self._kinds["SKIP_MARKET_SLOT"])
        )
        if len(skip) != 1:
            raise RuntimeError("effect teacher market-slot skip is unavailable")
        return int(skip[0])

    def metadata(self) -> dict[str, object]:
        """Return the active authenticated route identity."""
        return dict(self._metadata)

    def diagnostics(self) -> dict[str, int]:
        """Return cumulative translation counts for this episode."""
        return dict(self._diagnostics)

    def reset(self) -> None:
        """Reset the embedded teacher and all turn-local state."""
        self._teacher.reset()
        self._work.clear()
        self._market.clear()
        self._market_offset = 0
        self._metadata.clear()
        self._diagnostics.clear()


__all__ = ["EffectProposal", "EffectTeacherPlan", "Rank8EffectTeacher"]
