"""Authenticated empirical route discovery and loading from Kaggle replays."""

from __future__ import annotations

import hashlib
from collections import defaultdict
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any, cast

import orjson

from kagg_revue.bc.actions import ReplayActionEncoder


@dataclass(frozen=True)
class ReplayRouteReference:
    """One target-agent seat selected without consulting terminal outcomes."""

    episode_id: int
    seat: int
    source_path: Path
    source_sha256: str
    prefix_sha256: str
    cluster_size: int = 1

    @property
    def route_id(self) -> str:
        """Return the stable episode-and-seat identity."""
        return f"{self.episode_id}:{self.seat}"


@dataclass(frozen=True)
class ReplayRoute:
    """A complete fixed action sequence used only as a proposal."""

    reference: ReplayRouteReference
    actions: tuple[Mapping[str, Any], ...]
    action_sha256: str
    hire_requests: int
    source_maximum_units: int

    @property
    def maximum_possible_units(self) -> int:
        """Bound live units by the number of requested hires."""
        return 1 + self.hire_requests


def _mapping(value: Any, field: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{field} must be a mapping")
    return cast(Mapping[str, Any], value)


def _list(value: Any, field: str) -> list[Any]:
    if not isinstance(value, list):
        raise ValueError(f"{field} must be a list")
    return value


def _integer(value: Any, field: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise ValueError(f"{field} must be an integer")
    return value


def _string(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{field} must be a nonempty string")
    return value


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _validated_replay(
    payload: bytes,
    reference_episode: int,
    episode_steps: int,
    maximum_market_orders: int,
) -> Mapping[str, Any]:
    replay = _mapping(orjson.loads(payload), "replay")
    if replay.get("name") != "kaggriculture":
        raise ValueError("replay environment is not kaggriculture")
    info = _mapping(replay.get("info"), "replay.info")
    if _integer(info.get("EpisodeId"), "replay.info.EpisodeId") != reference_episode:
        raise ValueError("replay EpisodeId differs from its manifest record")
    configuration = _mapping(replay.get("configuration"), "replay.configuration")
    if configuration.get("episodeSteps") != episode_steps:
        raise ValueError("replay episodeSteps differs from the evaluation environment")
    if configuration.get("maxMarketOrdersPerTurn") != maximum_market_orders:
        raise ValueError("replay market capacity differs from the evaluation environment")
    steps = _list(replay.get("steps"), "replay.steps")
    if len(steps) != episode_steps:
        raise ValueError("replay does not contain a complete episode")
    statuses = _list(replay.get("statuses"), "replay.statuses")
    if statuses != ["DONE", "DONE"]:
        raise ValueError("replay terminal statuses are not complete")
    return replay


def _agent_names(replay: Mapping[str, Any]) -> tuple[str, ...]:
    info = _mapping(replay.get("info"), "replay.info")
    agents = _list(info.get("Agents"), "replay.info.Agents")
    names = tuple(
        _string(_mapping(agent, f"replay.info.Agents[{index}]").get("Name"), "agent.Name")
        for index, agent in enumerate(agents)
    )
    if len(names) != 2:
        raise ValueError("replay must contain exactly two agents")
    return names


def _turn_action(replay: Mapping[str, Any], turn: int, seat: int) -> Mapping[str, Any]:
    steps = _list(replay.get("steps"), "replay.steps")
    target_step = _list(steps[turn + 1], f"replay.steps[{turn + 1}]")
    if len(target_step) != 2:
        raise ValueError("replay step must contain exactly two agent states")
    state = _mapping(target_step[seat], f"replay.steps[{turn + 1}][{seat}]")
    return _mapping(state.get("action"), f"replay.steps[{turn + 1}][{seat}].action")


def _source_unit_count(action: Mapping[str, Any]) -> int:
    hands = action.get("hands")
    if not isinstance(hands, list):
        raise ValueError("replay action hands must be a list")
    return 1 + len(hands)


def _prefix_identity(
    replay: Mapping[str, Any],
    seat: int,
    prefix_turns: int,
    maximum_market_orders: int,
    codec: ReplayActionEncoder,
) -> str:
    signature: list[tuple[tuple[int, ...], tuple[int, ...], int, int]] = []
    for turn in range(prefix_turns):
        action = _turn_action(replay, turn, seat)
        encoded = codec.encode(
            action,
            unit_count=_source_unit_count(action),
            max_market_orders=maximum_market_orders,
        )
        signature.append(
            (
                encoded.tokens,
                encoded.quantities,
                encoded.unit_decisions,
                encoded.market_orders,
            )
        )
    return _sha256(orjson.dumps(signature))


def _manifest_sources(
    repository_root: Path,
    manifest_path: Path,
) -> tuple[tuple[int, Path, str], ...]:
    manifest = _mapping(orjson.loads(manifest_path.read_bytes()), "manifest")
    episodes = _mapping(manifest.get("episodes"), "manifest.episodes")
    records = _list(episodes.get("records"), "manifest.episodes.records")
    external_root = (repository_root / "data" / "external").resolve()
    sources: list[tuple[int, Path, str]] = []
    for index, raw_record in enumerate(records):
        record = _mapping(raw_record, f"manifest.episodes.records[{index}]")
        source = _mapping(record.get("source"), f"manifest record {index} source")
        if source.get("kind") != "kaggle_cli":
            continue
        episode_id = _integer(record.get("id"), f"manifest record {index} id")
        relative_path = Path(_string(source.get("path"), f"manifest record {index} path"))
        if relative_path.is_absolute() or ".." in relative_path.parts:
            raise ValueError("manifest replay path must be repository-relative")
        source_path = (repository_root / relative_path).resolve()
        if not source_path.is_relative_to(external_root):
            raise ValueError("manifest replay path escapes data/external")
        source_sha256 = _string(source.get("sha256"), f"manifest record {index} sha256")
        sources.append((episode_id, source_path, source_sha256))
    if not sources:
        raise ValueError("manifest contains no direct Kaggle replay sources")
    if len({episode_id for episode_id, _path, _sha in sources}) != len(sources):
        raise ValueError("manifest direct replay EpisodeIds are not unique")
    return tuple(sources)


def discover_replay_routes(
    repository_root: Path,
    manifest_path: Path,
    source_agent_name: str,
    prefix_turns: int,
    route_ids: Sequence[str] | None,
    episode_steps: int,
    maximum_market_orders: int,
    codec: ReplayActionEncoder,
) -> tuple[tuple[ReplayRouteReference, ...], dict[str, object]]:
    """Select one deterministic representative per empirical prefix cluster."""
    discovered: list[ReplayRouteReference] = []
    sources = _manifest_sources(repository_root, manifest_path)
    for episode_id, source_path, source_sha256 in sources:
        payload = source_path.read_bytes()
        if _sha256(payload) != source_sha256:
            raise ValueError(f"manifest SHA differs for replay {episode_id}")
        replay = _validated_replay(
            payload,
            episode_id,
            episode_steps,
            maximum_market_orders,
        )
        for seat, agent_name in enumerate(_agent_names(replay)):
            if agent_name != source_agent_name:
                continue
            discovered.append(
                ReplayRouteReference(
                    episode_id=episode_id,
                    seat=seat,
                    source_path=source_path,
                    source_sha256=source_sha256,
                    prefix_sha256=_prefix_identity(
                        replay,
                        seat,
                        prefix_turns,
                        maximum_market_orders,
                        codec,
                    ),
                )
            )
    if not discovered:
        raise ValueError("source agent is absent from direct replay artifacts")

    by_id = {reference.route_id: reference for reference in discovered}
    if route_ids is not None:
        missing = set(route_ids) - set(by_id)
        if missing:
            raise ValueError(
                f"explicit replay routes are absent from the source: {sorted(missing)}"
            )
        selected = tuple(by_id[route_id] for route_id in route_ids)
        mode = "explicit_episode_seat_identities"
    else:
        clusters: defaultdict[str, list[ReplayRouteReference]] = defaultdict(list)
        for reference in discovered:
            clusters[reference.prefix_sha256].append(reference)
        representatives: list[ReplayRouteReference] = []
        for prefix_sha256, members in clusters.items():
            chosen = min(members, key=lambda value: (value.episode_id, value.seat))
            representatives.append(
                replace(chosen, prefix_sha256=prefix_sha256, cluster_size=len(members))
            )
        selected = tuple(
            sorted(
                representatives,
                key=lambda value: (-value.cluster_size, value.prefix_sha256),
            )
        )
        mode = "earliest_episode_seat_per_distinct_prefix"

    selection: dict[str, object] = {
        "schema_version": "empirical-replay-route-selection-v1",
        "semantics": (
            "representatives use only encoded action prefixes and episode/seat identity; "
            "terminal rewards and cash are excluded"
        ),
        "mode": mode,
        "source_agent_name": source_agent_name,
        "prefix_turns": prefix_turns,
        "direct_replay_files": len(sources),
        "source_agent_routes": len(discovered),
        "distinct_prefixes": len({reference.prefix_sha256 for reference in discovered}),
        "selected_routes": [
            {
                "route_id": reference.route_id,
                "episode_id": reference.episode_id,
                "seat": reference.seat,
                "prefix_sha256": reference.prefix_sha256,
                "cluster_size": reference.cluster_size,
                "source_path": str(reference.source_path.relative_to(repository_root)),
                "source_sha256": reference.source_sha256,
            }
            for reference in selected
        ],
    }
    selection["selection_sha256"] = _sha256(orjson.dumps(selection, option=orjson.OPT_SORT_KEYS))
    return selected, selection


def load_replay_route(
    reference: ReplayRouteReference,
    episode_steps: int,
    maximum_market_orders: int,
) -> ReplayRoute:
    """Load all target actions from one authenticated replay seat."""
    payload = reference.source_path.read_bytes()
    if _sha256(payload) != reference.source_sha256:
        raise ValueError(f"source replay changed for route {reference.route_id}")
    replay = _validated_replay(
        payload,
        reference.episode_id,
        episode_steps,
        maximum_market_orders,
    )
    actions = tuple(_turn_action(replay, turn, reference.seat) for turn in range(episode_steps - 1))
    hire_requests = 0
    source_maximum_units = 1
    for action in actions:
        source_maximum_units = max(source_maximum_units, _source_unit_count(action))
        market = action.get("market")
        if not isinstance(market, list):
            raise ValueError("replay action market must be a list")
        hire_requests += sum(
            isinstance(request, list) and bool(request) and request[0] == "HIRE"
            for request in market
        )
    return ReplayRoute(
        reference=reference,
        actions=actions,
        action_sha256=_sha256(orjson.dumps(actions, option=orjson.OPT_SORT_KEYS)),
        hire_requests=hire_requests,
        source_maximum_units=source_maximum_units,
    )


__all__ = [
    "ReplayRoute",
    "ReplayRouteReference",
    "discover_replay_routes",
    "load_replay_route",
]
