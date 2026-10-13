"""Validated replay tensors and causal contexts for unit-task BC."""

from __future__ import annotations

import math
import zipfile
from collections import Counter
from collections.abc import Mapping, Sequence
from contextlib import nullcontext
from dataclasses import dataclass
from typing import Any, cast

import numpy as np
import orjson
import torch
from numpy.typing import NDArray
from torch import Tensor

from kagg_revue.bc.actions import EncodedTurnAction, ReplayActionEncoder
from kagg_revue.bc.data_config import ReplayContract
from kagg_revue.bc.replay import (
    EpisodeLocator,
    ReplayRejected,
    _canonicalize_observable_sell_quantities,
    _validate_header,
)
from kagg_revue.native import _revue_native as native
from kagg_revue.policy.model import ActorArchitecture, TurnPolicyNet
from kagg_revue.policy.tasks.contract import ITEMS, TaskOperation
from kagg_revue.policy.tasks.grammar import TaskCatalog
from kagg_revue.policy.tasks.native import NativeTaskContract

Position = tuple[int, int]
UnitAction = tuple[object, ...]

_UNIT_MOVEMENT_DELTAS = {
    "UNIT:NORTH": (0, -1),
    "UNIT:SOUTH": (0, 1),
    "UNIT:EAST": (1, 0),
    "UNIT:WEST": (-1, 0),
}


@dataclass(frozen=True)
class ReplaySequence:
    """One validated complete episode in actor- and task-facing forms."""

    episode_id: str
    configuration: Mapping[str, Any]
    observations: tuple[tuple[dict[str, Any], ...], ...]
    positions: tuple[tuple[tuple[Position, ...], ...], ...]
    unit_actions: tuple[tuple[tuple[UnitAction, ...], ...], ...]
    encoded_actions: tuple[tuple[EncodedTurnAction, ...], ...]
    board: NDArray[np.float16]
    units: NDArray[np.float16]
    global_features: NDArray[np.float16]
    economic_state: NDArray[np.int32]
    action_tokens: NDArray[np.int64]
    action_quantities: NDArray[np.int64]
    decision_mask: NDArray[np.bool_]
    rewards: tuple[float, ...]
    agent_names: tuple[str, ...]
    repairs: tuple[Mapping[str, int], ...]
    minimum_remaining_overage: tuple[float | None, ...]

    @property
    def turns(self) -> int:
        """Return the number of actor decisions before terminal state."""
        return int(self.board.shape[1])


def _mapping(value: Any, field: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ReplayRejected("invalid_schema", f"{field} must be a mapping")
    return cast(Mapping[str, Any], value)


def _list(value: Any, field: str) -> list[Any]:
    if not isinstance(value, list):
        raise ReplayRejected("invalid_schema", f"{field} must be a list")
    return value


def _integer(value: Any, field: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise ReplayRejected("invalid_schema", f"{field} must be an integer")
    return value


def _unit_action(
    codec: ReplayActionEncoder,
    token: int,
    quantity: int,
) -> UnitAction:
    key = codec.keys[token]
    fields = key.split(":")
    if len(fields) < 2 or fields[0] != "UNIT":
        raise ReplayRejected("invalid_action", "unit prefix contains a market token")
    result: list[object] = [fields[1]]
    if len(fields) == 3:
        result.append(fields[2])
    if quantity:
        result.append(quantity)
    return tuple(result)


def canonicalize_boundary_movements(
    encoded: EncodedTurnAction,
    positions: Sequence[Position],
    board_size: int,
    codec: ReplayActionEncoder,
) -> EncodedTurnAction:
    """Map observable out-of-board movement no-ops to canonical PASS requests."""
    if len(positions) != encoded.unit_decisions:
        raise ValueError("unit positions do not match the encoded action prefix")
    if board_size < 1:
        raise ValueError("board size must be positive")
    try:
        pass_token = codec.keys.index("UNIT:PASS")
    except ValueError as error:
        raise ValueError("action vocabulary lacks canonical unit PASS") from error
    tokens = list(encoded.tokens)
    quantities = list(encoded.quantities)
    repairs = dict(encoded.repairs)
    repaired = 0
    for index, position in enumerate(positions):
        x, y = position
        if not (0 <= x < board_size and 0 <= y < board_size):
            raise ValueError("observed unit position lies outside the board")
        token = tokens[index]
        if not 0 <= token < len(codec.keys):
            raise ValueError("encoded unit token lies outside the action vocabulary")
        delta = _UNIT_MOVEMENT_DELTAS.get(codec.keys[token])
        if delta is None:
            continue
        target_x = x + delta[0]
        target_y = y + delta[1]
        if 0 <= target_x < board_size and 0 <= target_y < board_size:
            continue
        tokens[index] = pass_token
        quantities[index] = 0
        repaired += 1
    if repaired == 0:
        return encoded
    repairs["out_of_board_movements_to_pass"] = (
        repairs.get("out_of_board_movements_to_pass", 0) + repaired
    )
    return EncodedTurnAction(
        tokens=tuple(tokens),
        quantities=tuple(quantities),
        unit_decisions=encoded.unit_decisions,
        market_orders=encoded.market_orders,
        repairs=repairs,
    )


def canonicalize_static_unit_noops(
    encoded: EncodedTurnAction,
    positions: Sequence[Position],
    codec: ReplayActionEncoder,
    catalog: TaskCatalog,
) -> EncodedTurnAction:
    """Map statically impossible official operations to canonical PASS requests."""
    if len(positions) != encoded.unit_decisions:
        raise ValueError("unit positions do not match the encoded action prefix")
    try:
        pass_token = codec.keys.index("UNIT:PASS")
    except ValueError as error:
        raise ValueError("action vocabulary lacks canonical unit PASS") from error
    allowed = {
        (int(operation), int(argument), int(target[0]), int(target[1]))
        for operation, argument, target in zip(
            catalog.operations.tolist(),
            catalog.arguments.tolist(),
            catalog.targets.tolist(),
            strict=True,
        )
    }
    tokens = list(encoded.tokens)
    quantities = list(encoded.quantities)
    repairs = dict(encoded.repairs)
    repaired = 0
    for index, position in enumerate(positions):
        token = tokens[index]
        if not 0 <= token < len(codec.keys):
            raise ValueError("encoded unit token lies outside the action vocabulary")
        key = codec.keys[token]
        if key == "UNIT:PASS" or key in _UNIT_MOVEMENT_DELTAS:
            continue
        fields = key.split(":")
        try:
            operation = TaskOperation[fields[1]]
            argument = -1 if len(fields) == 2 else ITEMS.index(fields[2])
        except (IndexError, KeyError, ValueError):
            continue
        candidate = (int(operation), argument, position[0], position[1])
        if candidate in allowed:
            continue
        tokens[index] = pass_token
        quantities[index] = 0
        repaired += 1
    if repaired == 0:
        return encoded
    repairs["statically_impossible_unit_operations_to_pass"] = (
        repairs.get("statically_impossible_unit_operations_to_pass", 0) + repaired
    )
    return EncodedTurnAction(
        tokens=tuple(tokens),
        quantities=tuple(quantities),
        unit_decisions=encoded.unit_decisions,
        market_orders=encoded.market_orders,
        repairs=repairs,
    )


def _observation_units(
    observation: Mapping[str, Any],
    seat: int,
) -> tuple[Position, ...]:
    farms = _list(observation.get("farms"), "observation.farms")
    if len(farms) != 2:
        raise ReplayRejected("invalid_schema", "observation farm count differs")
    farm = _mapping(farms[seat], "observation own farm")
    raw_farmer = _list(farm.get("farmer"), "observation own farmer")
    raw_hands = _list(farm.get("hands"), "observation own hands")
    raw_positions = [raw_farmer, *raw_hands]
    positions: list[Position] = []
    for index, raw in enumerate(raw_positions):
        if (
            not isinstance(raw, list)
            or len(raw) != 2
            or any(not isinstance(value, int) or isinstance(value, bool) for value in raw)
        ):
            raise ReplayRejected(
                "invalid_observation",
                f"observation unit position {index} is malformed",
            )
        positions.append((int(raw[0]), int(raw[1])))
    return tuple(positions)


def load_replay_sequence(
    locator: EpisodeLocator,
    contract: ReplayContract,
    task_contract: NativeTaskContract,
    actor_architecture: ActorArchitecture,
) -> ReplaySequence:
    """Decode one complete replay with the same causal inputs as the actor."""
    try:
        with zipfile.ZipFile(locator.archive) as archive:
            replay = _mapping(orjson.loads(archive.read(locator.entry)), "replay")
    except (KeyError, orjson.JSONDecodeError, zipfile.BadZipFile) as error:
        raise ReplayRejected(
            "invalid_json", f"cannot decode replay member: {type(error).__name__}: {error}"
        ) from error
    episode_id, configuration, steps, rewards, agent_names = _validate_header(
        replay, locator, contract
    )
    configuration_dict = dict(configuration)
    turns = contract.episode_steps - 1
    architecture = actor_architecture
    if architecture.board_shape[-1] != contract.board_size:
        raise ValueError("task BC actor and replay use different board sizes")
    if architecture.unit_shape[1] != contract.unit_limit:
        raise ValueError("task BC actor and replay use different unit limits")
    codec = ReplayActionEncoder(cast(Mapping[str, Any], native.action_codec_spec()))
    if (
        codec.unit_tokens != architecture.unit_action_tokens
        or len(codec.keys) != architecture.action_tokens
    ):
        raise ValueError("task BC architecture and native action vocabularies differ")

    board_rows: list[list[NDArray[np.float16]]] = [[], []]
    unit_rows: list[list[NDArray[np.float16]]] = [[], []]
    global_rows: list[list[NDArray[np.float16]]] = [[], []]
    economic_rows: list[list[NDArray[np.int32]]] = [[], []]
    observations: list[list[dict[str, Any]]] = [[], []]
    positions: list[list[tuple[Position, ...]]] = [[], []]
    unit_actions: list[list[tuple[UnitAction, ...]]] = [[], []]
    encoded_actions: list[list[EncodedTurnAction]] = [[], []]
    action_tokens = np.zeros(
        (contract.agents, turns, architecture.max_decisions), dtype=np.int64
    )
    action_quantities = np.zeros_like(action_tokens)
    decision_mask = np.zeros_like(action_tokens, dtype=np.bool_)
    repairs: list[Counter[str]] = [Counter() for _ in range(contract.agents)]
    minimum_overage = [math.inf] * contract.agents

    for turn in range(turns):
        source_step = _list(steps[turn], f"steps[{turn}]")
        target_step = _list(steps[turn + 1], f"steps[{turn + 1}]")
        if len(source_step) != contract.agents or len(target_step) != contract.agents:
            raise ReplayRejected("invalid_schema", "step agent count differs")
        for seat in range(contract.agents):
            source_state = _mapping(source_step[seat], f"steps[{turn}][{seat}]")
            if source_state.get("status") != "ACTIVE":
                raise ReplayRejected(
                    "inactive_source_turn", "source decision status is not ACTIVE"
                )
            raw_observation = _mapping(
                source_state.get("observation"),
                f"steps[{turn}][{seat}].observation",
            )
            observation = dict(raw_observation)
            if _integer(observation.get("player"), "observation.player") != seat:
                raise ReplayRejected("seat_mismatch", "observation player differs")
            observed_step = observation.get("step")
            if observed_step is None:
                observation["step"] = turn
            elif observed_step != turn:
                raise ReplayRejected("turn_mismatch", "observation step differs")
            current_positions = _observation_units(observation, seat)
            if len(current_positions) > contract.unit_limit:
                raise ReplayRejected(
                    "unit_limit_exceeded", "visible units exceed actor capacity"
                )
            target_state = _mapping(target_step[seat], f"steps[{turn + 1}][{seat}]")
            encoded = codec.encode(
                target_state.get("action"),
                len(current_positions),
                contract.max_market_orders,
            )
            encoded = _canonicalize_observable_sell_quantities(
                encoded,
                observation,
                configuration,
                codec,
            )
            encoded = canonicalize_boundary_movements(
                encoded,
                current_positions,
                contract.board_size,
                codec,
            )
            encoded = canonicalize_static_unit_noops(
                encoded,
                current_positions,
                codec,
                task_contract.catalog,
            )
            if len(encoded.tokens) > architecture.max_decisions:
                raise ReplayRejected(
                    "decision_limit_exceeded", "official action exceeds actor capacity"
                )
            action_tokens[seat, turn, : len(encoded.tokens)] = encoded.tokens
            action_quantities[seat, turn, : len(encoded.quantities)] = encoded.quantities
            decision_mask[seat, turn, : len(encoded.tokens)] = True
            repairs[seat].update(encoded.repairs)

            try:
                raw_board, raw_units, raw_global = native.encode_official_observation_numeric(
                    observation,
                    configuration_dict,
                    contract.unit_limit,
                )
                policy_session = native.PolicySession(
                    observation,
                    configuration_dict,
                    contract.unit_limit,
                )
                raw_economic = np.asarray(policy_session.gpu_state(), dtype=np.int64)
            except (KeyError, TypeError, ValueError, RuntimeError) as error:
                raise ReplayRejected(
                    "observation_encoding_failed",
                    f"native actor input failed: {type(error).__name__}: {error}",
                ) from error
            if np.any(raw_economic < np.iinfo(np.int32).min) or np.any(
                raw_economic > np.iinfo(np.int32).max
            ):
                raise ReplayRejected(
                    "observation_encoding_failed", "economic state exceeds int32 storage"
                )
            board_rows[seat].append(np.asarray(raw_board, dtype=np.float16))
            unit_rows[seat].append(np.asarray(raw_units, dtype=np.float16))
            global_rows[seat].append(np.asarray(raw_global, dtype=np.float16))
            economic_rows[seat].append(raw_economic.astype(np.int32))
            observations[seat].append(observation)
            positions[seat].append(current_positions)
            unit_actions[seat].append(
                tuple(
                    _unit_action(codec, token, quantity)
                    for token, quantity in zip(
                        encoded.tokens[: len(current_positions)],
                        encoded.quantities[: len(current_positions)],
                        strict=True,
                    )
                )
            )
            encoded_actions[seat].append(encoded)
            raw_overage = observation.get("remainingOverageTime")
            if isinstance(raw_overage, int | float) and not isinstance(raw_overage, bool):
                minimum_overage[seat] = min(minimum_overage[seat], float(raw_overage))

    board = np.stack([np.stack(rows) for rows in board_rows]).astype(np.float16)
    units = np.stack([np.stack(rows) for rows in unit_rows]).astype(np.float16)
    global_features = np.stack([np.stack(rows) for rows in global_rows]).astype(np.float16)
    economic_state = np.stack([np.stack(rows) for rows in economic_rows]).astype(np.int32)
    if not all(
        np.isfinite(value).all() for value in (board, units, global_features)
    ):
        raise ReplayRejected("nonfinite_observation", "actor input contains NaN or Inf")
    return ReplaySequence(
        episode_id=episode_id,
        configuration=configuration_dict,
        observations=tuple(tuple(rows) for rows in observations),
        positions=tuple(tuple(rows) for rows in positions),
        unit_actions=tuple(tuple(rows) for rows in unit_actions),
        encoded_actions=tuple(tuple(rows) for rows in encoded_actions),
        board=board,
        units=units,
        global_features=global_features,
        economic_state=economic_state,
        action_tokens=action_tokens,
        action_quantities=action_quantities,
        decision_mask=decision_mask,
        rewards=rewards,
        agent_names=agent_names,
        repairs=tuple(dict(values) for values in repairs),
        minimum_remaining_overage=tuple(
            value if math.isfinite(value) else None for value in minimum_overage
        ),
    )


def actor_contexts(
    actor: TurnPolicyNet,
    sequence: ReplaySequence,
    device: torch.device,
) -> NDArray[np.float16]:
    """Cache the frozen actor's exact causal history token for every turn."""
    actor.eval()

    def tensor(value: NDArray[np.generic]) -> Tensor:
        return torch.as_tensor(value, device=device)

    turn_mask = torch.ones(
        sequence.board.shape[:2], dtype=torch.bool, device=device
    )
    autocast = (
        torch.autocast(device_type="cuda", dtype=torch.bfloat16)
        if device.type == "cuda"
        else nullcontext()
    )
    with torch.inference_mode(), autocast:
        encoding = actor.encode_sequence(
            tensor(sequence.board),
            tensor(sequence.units),
            tensor(sequence.global_features),
            tensor(sequence.action_tokens).long(),
            tensor(sequence.action_quantities),
            turn_mask,
            tensor(sequence.decision_mask).bool(),
            economic_state=(
                tensor(sequence.economic_state)
                if actor.architecture.economic_feature_version
                else None
            ),
        )
        contexts = encoding.history.to(device="cpu", dtype=torch.float16).numpy()
    result = np.ascontiguousarray(contexts, dtype=np.float16)
    if result.shape != (
        sequence.board.shape[0],
        sequence.turns,
        actor.architecture.model_width,
    ) or not np.isfinite(result).all():
        raise ValueError("task BC actor contexts differ from their expected shape")
    return result


__all__ = [
    "ReplaySequence",
    "actor_contexts",
    "canonicalize_boundary_movements",
    "canonicalize_static_unit_noops",
    "load_replay_sequence",
]
