"""Fixed-address native staging and CUDA Graph replay for intent turns."""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any

import numpy as np
import torch
from numpy.typing import NDArray
from torch import Tensor

from kagg_revue.policy.cuda.capture import (
    capture_safe_graph_replay,
    serialized_graph_capture,
)
from kagg_revue.policy.cuda.history import CudaStaticHistory
from kagg_revue.policy.economics import EconomicStateLayout
from kagg_revue.policy.model import ActorArchitecture, TurnPolicyNet


@dataclass(frozen=True)
class IntentTurnInputs:
    """Stable device tensors consumed by one captured intent turn."""

    board: Tensor
    units: Tensor
    global_features: Tensor
    previous_actions: Tensor
    previous_quantities: Tensor
    previous_mask: Tensor
    economic_state: Tensor | None

    def tensors(self) -> tuple[Tensor, ...]:
        """Return every present input in pointer-validation order."""
        required = (
            self.board,
            self.units,
            self.global_features,
            self.previous_actions,
            self.previous_quantities,
            self.previous_mask,
        )
        return required + (() if self.economic_state is None else (self.economic_state,))


class PinnedIntentTurnStaging:
    """Let native code fill reusable pinned observations without Python copies."""

    def __init__(
        self,
        architecture: ActorArchitecture,
        batch: int,
        device: torch.device,
    ) -> None:
        """Allocate the fixed host/device ABI for one rollout batch."""
        if device.type != "cuda" or batch < 1:
            raise ValueError("pinned intent turn staging requires a positive CUDA batch")
        layout = EconomicStateLayout.create(
            architecture.board_shape[-1],
            architecture.unit_shape[1],
        )
        self._uses_economics = architecture.economic_feature_version is not None
        self._board = torch.empty(
            (batch, *architecture.board_shape),
            dtype=torch.float16,
            device="cpu",
            pin_memory=True,
        )
        self._units = torch.empty(
            (batch, *architecture.unit_shape),
            dtype=torch.float16,
            device="cpu",
            pin_memory=True,
        )
        self._global = torch.empty(
            (batch, architecture.global_features),
            dtype=torch.float32,
            device="cpu",
            pin_memory=True,
        )
        self._unit_counts = torch.empty((batch,), dtype=torch.int64, device="cpu", pin_memory=True)
        self._economic = torch.empty(
            (batch, layout.width),
            dtype=torch.int32,
            device="cpu",
            pin_memory=True,
        )
        previous_shape = (batch, architecture.max_decisions)
        self._previous_actions_host = torch.zeros(
            previous_shape, dtype=torch.int64, device="cpu", pin_memory=True
        )
        self._previous_quantities_host = torch.zeros_like(
            self._previous_actions_host, pin_memory=True
        )
        self._previous_mask_host = torch.zeros(
            previous_shape, dtype=torch.bool, device="cpu", pin_memory=True
        )
        self.inputs = IntentTurnInputs(
            board=torch.empty_like(self._board, device=device),
            units=torch.empty_like(self._units, device=device),
            global_features=torch.empty_like(self._global, device=device),
            previous_actions=torch.zeros(previous_shape, dtype=torch.long, device=device),
            previous_quantities=torch.zeros(previous_shape, dtype=torch.long, device=device),
            previous_mask=torch.zeros(previous_shape, dtype=torch.bool, device=device),
            economic_state=(
                torch.empty_like(self._economic, device=device) if self._uses_economics else None
            ),
        )

    @property
    def board(self) -> NDArray[np.float16]:
        """Return the current native-filled board view."""
        return self._board.numpy()

    @property
    def units(self) -> NDArray[np.float16]:
        """Return the current native-filled unit view."""
        return self._units.numpy()

    @property
    def global_features(self) -> NDArray[np.float32]:
        """Return the current native-filled global-feature view."""
        return self._global.numpy()

    @property
    def economic_state(self) -> NDArray[np.int32]:
        """Return the current native-filled compact economic-state view."""
        return self._economic.numpy()

    def install_native(
        self,
        backend: Any,
        engines: list[Any],
        players: list[int],
        unit_limit: int,
        workers: int,
    ) -> None:
        """Fill pinned observations in C++ and enqueue one ordered H2D upload."""
        backend.engine_policy_turn_inputs_compact_into(
            engines,
            players,
            unit_limit,
            workers,
            self.board,
            self.units,
            self.global_features,
            self._unit_counts.numpy(),
            self.economic_state,
        )
        self.inputs.board.copy_(self._board, non_blocking=True)
        self.inputs.units.copy_(self._units, non_blocking=True)
        self.inputs.global_features.copy_(self._global, non_blocking=True)
        if self.inputs.economic_state is not None:
            self.inputs.economic_state.copy_(self._economic, non_blocking=True)

    def install_previous(
        self,
        tokens: NDArray[np.int64],
        quantities: NDArray[np.int64],
        counts: NDArray[np.int64],
    ) -> None:
        """Stage the compiled prior action into persistent graph inputs."""
        width = tokens.shape[1]
        if (
            tokens.shape != quantities.shape
            or tokens.shape[0] != self.inputs.board.shape[0]
            or counts.shape != (tokens.shape[0],)
            or width > self.inputs.previous_actions.shape[1]
        ):
            raise ValueError("compiled intent action differs from turn staging")
        actions = self._previous_actions_host.numpy()
        staged_quantities = self._previous_quantities_host.numpy()
        mask = self._previous_mask_host.numpy()
        actions.fill(0)
        staged_quantities.fill(0)
        mask.fill(False)
        actions[:, :width] = tokens
        staged_quantities[:, :width] = quantities
        mask[:, :width] = np.arange(width)[None] < counts[:, None]
        self.inputs.previous_actions.copy_(self._previous_actions_host, non_blocking=True)
        self.inputs.previous_quantities.copy_(self._previous_quantities_host, non_blocking=True)
        self.inputs.previous_mask.copy_(self._previous_mask_host, non_blocking=True)

    def reset_episode(self) -> None:
        """Clear the recurrent prior-action inputs before a new episode batch."""
        self._previous_actions_host.zero_()
        self._previous_quantities_host.zero_()
        self._previous_mask_host.zero_()
        self.inputs.previous_actions.zero_()
        self.inputs.previous_quantities.zero_()
        self.inputs.previous_mask.zero_()


class IntentTurnGraph:
    """Capture scene and causal history encoding for one intent rollout batch."""

    def __init__(
        self,
        actor: TurnPolicyNet,
        inputs: IntentTurnInputs,
        tile_count: int,
    ) -> None:
        """Warm and capture the fixed-address visible-turn encoder."""
        tensors = inputs.tensors()
        device = inputs.board.device
        batch = inputs.board.shape[0]
        if device.type != "cuda" or any(tensor.device != device for tensor in tensors):
            raise ValueError("intent turn graph inputs must share one CUDA device")
        if any(tensor.shape[0] != batch for tensor in tensors):
            raise ValueError("intent turn graph inputs have different batches")
        if actor.architecture.turn_fact_features or actor.architecture.skill_tokens:
            raise ValueError("intent turn graph requires deterministic actor context")
        if (inputs.economic_state is None) != (actor.economics is None):
            raise ValueError("intent turn graph economic state differs from actor")
        tile_start = 1 + actor.architecture.latent_tokens
        maximum_tiles = 2 * actor.architecture.board_shape[-2] * actor.architecture.board_shape[-1]
        if tile_count < 1 or tile_count > maximum_tiles:
            raise ValueError("intent tile context exceeds actor scene memory")
        self._actor = actor
        self._inputs = inputs
        self._input_pointers = tuple(tensor.data_ptr() for tensor in tensors)
        self._device = device
        self._tile_start = tile_start
        self._tile_stop = tile_start + tile_count
        self._maximum_replays = actor.architecture.max_history
        self._replays = 0
        self._history = CudaStaticHistory(actor, batch, torch.bfloat16)
        started = time.perf_counter()
        with torch.inference_mode(), torch.autocast("cuda", dtype=torch.bfloat16):
            self._context, self._tiles = self._run()
        torch.cuda.current_stream(device).synchronize()
        self._history.reset()
        graph = torch.cuda.CUDAGraph()
        with (
            torch.inference_mode(),
            torch.autocast("cuda", dtype=torch.bfloat16),
            serialized_graph_capture(graph),
        ):
            self._context, self._tiles = self._run()
        torch.cuda.current_stream(device).synchronize()
        self._history.reset()
        torch.cuda.current_stream(device).synchronize()
        self._graph = graph
        self.capture_seconds = time.perf_counter() - started

    def _run(self) -> tuple[Tensor, Tensor]:
        economic_features: Tensor | None = None
        if self._actor.economics is not None:
            economic_state = self._inputs.economic_state
            if economic_state is None:
                raise RuntimeError("intent turn graph lost its economic state")
            economic_features = self._actor.economics.turn_features(
                economic_state,
                self._inputs.global_features,
            )
        scene = self._actor.scene(
            self._inputs.board,
            self._inputs.units,
            self._inputs.global_features,
            self._inputs.previous_actions,
            self._inputs.previous_quantities,
            self._inputs.previous_mask,
            economic_features=economic_features,
        )
        context, _skill = self._history.start_turn(scene)
        return (
            context.memory[:, 0],
            context.memory[:, self._tile_start : self._tile_stop],
        )

    def replay(self, inputs: IntentTurnInputs) -> tuple[Tensor, Tensor]:
        """Replay one encoded turn after native staging, without host dispatch."""
        if tuple(tensor.data_ptr() for tensor in inputs.tensors()) != self._input_pointers:
            raise ValueError("intent turn graph input address changed")
        if self._replays >= self._maximum_replays:
            raise RuntimeError("intent turn graph exceeded actor history capacity")
        capture_safe_graph_replay(self._graph)
        self._replays += 1
        return self._context, self._tiles

    def reset_episode(self) -> None:
        """Reset causal history while retaining all captured allocations."""
        with torch.inference_mode():
            self._history.reset()
        self._replays = 0

    def close(self) -> None:
        """Release graph-private allocations."""
        self._graph.reset()
        del self._graph
        del self._context
        del self._tiles
        del self._history
        del self._inputs
        del self._actor


__all__ = [
    "IntentTurnGraph",
    "IntentTurnInputs",
    "PinnedIntentTurnStaging",
]
