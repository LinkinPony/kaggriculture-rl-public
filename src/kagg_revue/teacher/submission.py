"""Authenticated runtime for the exact Kaggle submission teacher."""

from __future__ import annotations

import gzip
import hashlib
import json
import re
import tarfile
from collections.abc import Mapping, Sequence
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

from kagg_revue.bc.dataset import sha256_file

_ROUTE_ID = re.compile(r"^[a-z][a-z0-9_-]*$")
_SHOP_ID = re.compile(r"^[A-Z][A-Z0-9_]*$")


@dataclass(frozen=True)
class ConditionalRouteBranch:
    """One exact route selected by the first occurrence of an observable event."""

    route_id: str
    first_event_day: int
    activation_step: int
    support: int
    actions: tuple[dict[str, Any], ...]


@dataclass(frozen=True)
class ConditionalRouteArtifact:
    """Authenticated default route and mutually exclusive event-day branches."""

    event_shop: str
    default_route_id: str
    default_support: int
    default_actions: tuple[dict[str, Any], ...]
    branches: tuple[ConditionalRouteBranch, ...]
    source: dict[str, Any]


@dataclass(frozen=True)
class SubmissionTeacherArtifact:
    """Verified deployment profile and route bytes extracted from one submission."""

    archive_path: Path
    archive_sha256: str
    source_commit: str
    route_sha256: str
    repair_weeds: bool
    weed_replay_steps: int
    route: ConditionalRouteArtifact

    def identity(self) -> dict[str, object]:
        """Return the immutable teacher identity recorded in generated datasets."""
        return {
            "kind": "kaggle_submission_archive",
            "archive_path": str(self.archive_path),
            "archive_sha256": self.archive_sha256,
            "source_commit": self.source_commit,
            "policy": "embedded_conditional_route",
            "route_sha256": self.route_sha256,
            "repair_weeds": self.repair_weeds,
            "weed_replay_steps": self.weed_replay_steps,
        }


@dataclass(frozen=True)
class _WeedTransaction:
    start_step: int
    intended: list[Any]


def _mapping(value: Any, name: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise TypeError(f"{name} must be a mapping")
    return cast(Mapping[str, Any], value)


def _integer(value: Any, name: str, *, minimum: int = 0) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < minimum:
        raise ValueError(f"{name} must be an integer >= {minimum}")
    return value


def _route_id(value: Any) -> str:
    result = str(value)
    if not _ROUTE_ID.fullmatch(result):
        raise ValueError(f"invalid conditional route id: {result!r}")
    return result


def _shop_id(value: Any) -> str:
    result = str(value)
    if not _SHOP_ID.fullmatch(result):
        raise ValueError(f"invalid conditional route shop id: {result!r}")
    return result


def _route_actions(value: Any) -> tuple[dict[str, Any], ...]:
    if not isinstance(value, list):
        raise TypeError("route actions must be a list")
    required = {"farmer", "hands", "market"}
    actions: list[dict[str, Any]] = []
    for index, raw in enumerate(value):
        action = _mapping(raw, f"route action {index}")
        if set(action) != required:
            raise ValueError(f"route action {index} must contain exactly {sorted(required)}")
        copied = {str(key): deepcopy(item) for key, item in action.items()}
        if any(not isinstance(copied[field], list) for field in required):
            raise TypeError(f"route action {index} fields must be lists")
        actions.append(copied)
    if not actions:
        raise ValueError("route must contain at least one action")
    return tuple(actions)


def _decode_conditional_route(payload: bytes, expected_sha256: str) -> ConditionalRouteArtifact:
    actual_sha256 = hashlib.sha256(payload).hexdigest()
    if actual_sha256 != expected_sha256:
        raise ValueError(
            "conditional route artifact hash mismatch: "
            f"expected {expected_sha256}, got {actual_sha256}"
        )
    value = _mapping(json.loads(gzip.decompress(payload)), "conditional route artifact")
    if value.get("schema_version") != 1:
        raise ValueError("unsupported conditional route artifact schema")
    source = _mapping(value.get("source"), "conditional route source")
    event = _mapping(value.get("event"), "conditional route event")
    default = _mapping(value.get("default"), "conditional route default")
    raw_branches = value.get("branches")
    if not isinstance(raw_branches, list):
        raise TypeError("conditional route branches must be a list")
    default_actions = _route_actions(default.get("actions"))
    default_route_id = _route_id(default.get("route_id"))
    branches: list[ConditionalRouteBranch] = []
    for raw_branch in raw_branches:
        branch = _mapping(raw_branch, "conditional route branch")
        actions = _route_actions(branch.get("actions"))
        activation_step = _integer(branch.get("activation_step"), "activation_step")
        if len(actions) != len(default_actions):
            raise ValueError("conditional routes must have equal action counts")
        if activation_step >= len(default_actions):
            raise ValueError("conditional route activation step is outside the episode")
        if actions[:activation_step] != default_actions[:activation_step]:
            raise ValueError("conditional route differs before its observable event")
        branches.append(
            ConditionalRouteBranch(
                route_id=_route_id(branch.get("route_id")),
                first_event_day=_integer(branch.get("first_event_day"), "first_event_day"),
                activation_step=activation_step,
                support=_integer(branch.get("support"), "support", minimum=1),
                actions=actions,
            )
        )
    branch_ids = [branch.route_id for branch in branches]
    branch_days = [branch.first_event_day for branch in branches]
    if len(branch_ids) != len(set(branch_ids)) or default_route_id in branch_ids:
        raise ValueError("conditional route ids must be unique")
    if len(branch_days) != len(set(branch_days)) or branch_days != sorted(branch_days):
        raise ValueError("conditional route event days must be unique and ordered")
    return ConditionalRouteArtifact(
        event_shop=_shop_id(event.get("town_shop")),
        default_route_id=default_route_id,
        default_support=_integer(default.get("support"), "default support", minimum=1),
        default_actions=default_actions,
        branches=tuple(branches),
        source={str(key): deepcopy(item) for key, item in source.items()},
    )


def _tar_member(archive: tarfile.TarFile, name: str) -> bytes:
    try:
        member = archive.getmember(name)
    except KeyError as error:
        raise ValueError(f"submission archive lacks {name}") from error
    if not member.isfile():
        raise ValueError(f"submission archive member is not a regular file: {name}")
    stream = archive.extractfile(member)
    if stream is None:
        raise ValueError(f"submission archive member cannot be read: {name}")
    return stream.read()


def load_submission_teacher(
    archive_path: Path,
    expected_archive_sha256: str,
    expected_source_commit: str,
    expected_route_sha256: str,
) -> SubmissionTeacherArtifact:
    """Load only the authenticated policy profile and route from a submission tarball."""
    archive_path = archive_path.resolve()
    if not archive_path.is_file():
        raise FileNotFoundError(f"submission teacher archive does not exist: {archive_path}")
    archive_sha256 = sha256_file(archive_path)
    if archive_sha256 != expected_archive_sha256:
        raise ValueError(
            "submission archive hash mismatch: "
            f"expected {expected_archive_sha256}, got {archive_sha256}"
        )
    with tarfile.open(archive_path, "r:gz") as archive:
        manifest = _mapping(json.loads(_tar_member(archive, "manifest.json")), "manifest")
        profile = _mapping(
            json.loads(_tar_member(archive, "kagg/agent_profile.json")), "agent profile"
        )
        source_commit = str(manifest.get("source_commit"))
        if source_commit != expected_source_commit:
            raise ValueError("submission source commit differs from the expected teacher")
        if manifest.get("worktree_dirty") is not False:
            raise ValueError("submission teacher was not built from a clean source revision")
        if profile.get("policy") != "embedded_conditional_route":
            raise ValueError("submission teacher is not the expected conditional route policy")
        route_member = str(profile.get("artifact_path"))
        route_sha256 = str(profile.get("artifact_sha256"))
        if route_sha256 != expected_route_sha256:
            raise ValueError("submission route hash differs from the expected teacher")
        route_payload = _tar_member(archive, route_member)
    repair_weeds = profile.get("repair_weeds")
    if not isinstance(repair_weeds, bool):
        raise TypeError("submission teacher repair_weeds must be boolean")
    weed_replay_steps = _integer(profile.get("weed_replay_steps"), "weed_replay_steps")
    return SubmissionTeacherArtifact(
        archive_path=archive_path,
        archive_sha256=archive_sha256,
        source_commit=source_commit,
        route_sha256=route_sha256,
        repair_weeds=repair_weeds,
        weed_replay_steps=weed_replay_steps,
        route=_decode_conditional_route(route_payload, route_sha256),
    )


class SubmissionTeacher:
    """Exact conditional-route behavior of the authenticated Kaggle submission."""

    def __init__(
        self,
        configuration: Mapping[str, Any],
        artifact: SubmissionTeacherArtifact,
    ) -> None:
        """Create fresh episode-local route and repair state."""
        required_steps = max(1, int(configuration.get("episodeSteps", 720)) - 1)
        if len(artifact.route.default_actions) < required_steps:
            raise ValueError("submission route is shorter than the configured episode")
        self._artifact = artifact
        self._turns_per_day = max(1, int(configuration.get("turnsPerDay", 24)))
        self._routes_by_day = {branch.first_event_day: branch for branch in artifact.route.branches}
        self._actions = artifact.route.default_actions
        self._weed_transactions: dict[int, _WeedTransaction] = {}
        self._last_step = -1
        self._cached_step = -1
        self._cached_plan: dict[str, Any] | None = None
        self._reset_selector()

    def _reset_selector(self) -> None:
        self._active_route_id = self._artifact.route.default_route_id
        self._first_event_day: int | None = None
        self._switched_step: int | None = None
        self._selector_last_step = -1

    def _switch_actions(self, actions: tuple[dict[str, Any], ...], step: int) -> None:
        if len(actions) != len(self._actions) or actions[:step] != self._actions[:step]:
            raise ValueError("conditional route switch would rewrite the submitted prefix")
        self._actions = actions
        self._cached_step = -1
        self._cached_plan = None

    def _select_route(self, observation: Mapping[str, Any]) -> None:
        step = int(observation.get("step", 0))
        if step < self._selector_last_step:
            self.reset()
        self._selector_last_step = step
        if self._first_event_day is not None:
            return
        town = _mapping(observation.get("town"), "teacher observation town")
        shops = town.get("unlocked_shops")
        if not isinstance(shops, Sequence) or isinstance(shops, str | bytes):
            raise TypeError("teacher observation shops must be a sequence")
        if self._artifact.route.event_shop not in shops:
            return
        day = int(observation.get("day", 0))
        self._first_event_day = day
        branch = self._routes_by_day.get(day)
        if branch is None:
            return
        if step < branch.activation_step:
            raise ValueError("conditional route event appeared before its authenticated step")
        self._switch_actions(branch.actions, step)
        self._active_route_id = branch.route_id
        self._switched_step = step

    @staticmethod
    def _active_farm(observation: Mapping[str, Any]) -> Mapping[str, Any]:
        farms = observation.get("farms")
        if not isinstance(farms, Sequence):
            raise TypeError("teacher observation farms must be a sequence")
        farm = farms[int(observation.get("player", 0))]
        return _mapping(farm, "teacher active farm")

    @staticmethod
    def _tile_at(farm: Mapping[str, Any], position: Any) -> Any:
        try:
            x, y = int(position[0]), int(position[1])
            tiles = cast(Sequence[Sequence[Any]], farm["tiles"])
            return tiles[y][x]
        except (IndexError, KeyError, TypeError, ValueError):
            return "LOCKED"

    def _trace_actor_action(self, step: int, unit_index: int) -> list[Any]:
        action = self._actions[min(max(step, 0), len(self._actions) - 1)]
        if unit_index == 0:
            return deepcopy(cast(list[Any], action["farmer"]))
        hands = cast(list[Any], action["hands"])
        return (
            deepcopy(cast(list[Any], hands[unit_index - 1]))
            if unit_index - 1 < len(hands)
            else ["PASS"]
        )

    def _apply_weed_repair(
        self,
        observation: Mapping[str, Any],
        action: dict[str, Any],
        step: int,
    ) -> tuple[dict[str, Any], int]:
        if step == 0 or step < self._last_step:
            self._weed_transactions.clear()
        self._last_step = step
        farm = self._active_farm(observation)
        positions = [farm.get("farmer"), *cast(Sequence[Any], farm.get("hands", ()))]
        unit_actions = [
            cast(list[Any], action["farmer"]),
            *cast(list[list[Any]], action["hands"]),
        ]
        for unit_index, transaction in list(self._weed_transactions.items()):
            if unit_index >= len(unit_actions):
                self._weed_transactions.pop(unit_index)
                continue
            age = step - transaction.start_step
            if age == 1:
                unit_actions[unit_index] = deepcopy(transaction.intended)
            elif 2 <= age <= 1 + self._artifact.weed_replay_steps:
                unit_actions[unit_index] = self._trace_actor_action(step - 1, unit_index)
            else:
                self._weed_transactions.pop(unit_index)
        started = 0
        for unit_index, (position, intended) in enumerate(
            zip(positions, unit_actions, strict=True)
        ):
            if unit_index in self._weed_transactions or not intended:
                continue
            if intended[0] not in {"BUILD_PASTURE", "PLANT"}:
                continue
            tile = self._tile_at(farm, position)
            if not isinstance(tile, Mapping) or tile.get("kind") != "WEED":
                continue
            self._weed_transactions[unit_index] = _WeedTransaction(
                start_step=step,
                intended=deepcopy(intended),
            )
            unit_actions[unit_index] = ["DIG"]
            started += 1
        action["farmer"] = unit_actions[0]
        action["hands"] = unit_actions[1:]
        return action, started

    def plan(self, observation: Mapping[str, Any]) -> dict[str, Any]:
        """Return the exact route request and bounded behavior diagnostics."""
        self._select_route(observation)
        step = int(observation.get("step", 0))
        if step < 0 or step >= len(self._actions):
            raise IndexError(f"teacher route step is outside the artifact: {step}")
        if self._cached_step == step and self._cached_plan is not None:
            return deepcopy(self._cached_plan)
        action = deepcopy(self._actions[step])
        recorded_hands = cast(list[Any], action["hands"])
        farm = self._active_farm(observation)
        hands = farm.get("hands")
        if not isinstance(hands, Sequence):
            raise TypeError("teacher active farm hands must be a sequence")
        action["hands"] = [
            deepcopy(recorded_hands[index]) if index < len(recorded_hands) else ["PASS"]
            for index in range(len(hands))
        ]
        repairs_started = 0
        if self._artifact.repair_weeds:
            action, repairs_started = self._apply_weed_repair(observation, action, step)
        plan = {
            "action": action,
            "route_id": self._active_route_id,
            "first_event_day": self._first_event_day,
            "switched_step": self._switched_step,
            "weed_repairs_started": repairs_started,
        }
        self._cached_step = step
        self._cached_plan = deepcopy(plan)
        return plan

    def act(self, observation: Mapping[str, Any]) -> dict[str, Any]:
        """Return one official submitted request."""
        return cast(dict[str, Any], self.plan(observation)["action"])

    def causal_unit_programs(
        self,
        observation: Mapping[str, Any],
    ) -> tuple[tuple[tuple[object, ...], ...], ...]:
        """Return current-day unit programs known to the deployed actor.

        The suffix comes only from the authenticated route already embedded in
        the submission and from repair transactions started by observations at
        or before the current step. It never consumes a realized replay suffix
        or a future environment observation.
        """
        plan = self.plan(observation)
        step = int(observation.get("step", 0))
        farm = self._active_farm(observation)
        hands = farm.get("hands")
        if not isinstance(hands, Sequence):
            raise TypeError("teacher active farm hands must be a sequence")
        unit_count = 1 + len(hands)
        day_end = min(
            len(self._actions),
            (step // self._turns_per_day + 1) * self._turns_per_day,
        )
        current = cast(Mapping[str, Any], plan["action"])
        current_actions = [
            cast(Sequence[object], current["farmer"]),
            *cast(Sequence[Sequence[object]], current["hands"]),
        ]
        programs: list[list[tuple[object, ...]]] = [
            [tuple(current_actions[unit])] for unit in range(unit_count)
        ]
        for future_step in range(step + 1, day_end):
            for unit in range(unit_count):
                transaction = self._weed_transactions.get(unit)
                age = -1 if transaction is None else future_step - transaction.start_step
                if transaction is not None and age == 1:
                    action = transaction.intended
                elif transaction is not None and 2 <= age <= 1 + self._artifact.weed_replay_steps:
                    action = self._trace_actor_action(future_step - 1, unit)
                else:
                    action = self._trace_actor_action(future_step, unit)
                programs[unit].append(tuple(action))
        return tuple(tuple(program) for program in programs)

    def reset(self) -> None:
        """Restore the default route and clear all episode-local state."""
        self._actions = self._artifact.route.default_actions
        self._weed_transactions.clear()
        self._last_step = -1
        self._cached_step = -1
        self._cached_plan = None
        self._reset_selector()

    def metadata(self) -> dict[str, object]:
        """Return the actor-visible route choice made in this episode."""
        return {
            "route_sha256": self._artifact.route_sha256,
            "event_shop": self._artifact.route.event_shop,
            "first_event_day": self._first_event_day,
            "route_id": self._active_route_id,
            "switched_step": self._switched_step,
        }


__all__ = [
    "SubmissionTeacher",
    "SubmissionTeacherArtifact",
    "load_submission_teacher",
]
