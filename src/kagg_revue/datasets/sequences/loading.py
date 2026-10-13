"""Authenticated complete trajectories with loss masks separate from context validity."""

from typing import Literal

import numpy as np
import torch
from torch import Tensor

from kagg_revue.datasets.demonstrations.loading import Dataset


class SequenceDataset(Dataset):
    """Reuse source authentication and split checks while preserving every time step."""

    def configure(self, batch_rows: int, world: int, seed: int) -> None:
        """Pack whole teacher trajectories into balanced fixed-size device batches."""
        turns = self.layout.observation.turns
        if batch_rows % (turns * world):
            raise ValueError("recurrent BC batches must contain whole trajectories per rank")
        self.trajectories = batch_rows // turns
        self._host_buffers: list[Tensor] = []
        self.groups: list[list[tuple[int, int]]] = []
        self.group_splits: list[str] = []
        generator = np.random.default_rng([seed, 71])
        splits = (
            ("train", "val")
            if any(s["split"] == "val" for s in self.shards)
            else ("train", "selection", "confirmation")
        )
        for split in splits:
            references = [
                (index, seat)
                for index, record in enumerate(self.shards)
                if record["split"] == split
                for seat in range(len(record["task"]["seats"]))
            ]
            order = generator.permutation(len(references))
            references = [references[int(index)] for index in order]
            for start in range(0, len(references), self.trajectories):
                self.groups.append(references[start : start + self.trajectories])
                self.group_splits.append(split)

    def partition(self, split: Literal["train", "val", "selection", "confirmation"]) -> list[int]:
        """Expose deterministic complete-trajectory groups as checkpointable work units."""
        if not hasattr(self, "groups"):
            return super().partition(split)
        name = self.resolve_split(split)
        return [index for index, value in enumerate(self.group_splits) if value == name]

    def episode(
        self, index: int, device: torch.device, rank: int, world: int
    ) -> tuple[Tensor, Tensor, Tensor]:
        """Load complete local trajectories and mask padding only in the final batch."""
        if self.manifest.get("sequence_format") != "complete-turn-seat-v1":
            raise ValueError("recurrent BC requires complete context trajectories")
        if hasattr(self, "groups"):
            references = self.groups[index]
            local = self.trajectories // world
            positions = range(rank * local, (rank + 1) * local)
            columns = [
                self._trajectory(*references[min(i, len(references) - 1)]) for i in positions
            ]
            values = self._pack(columns, device)
            mask = values[2] & (torch.arange(local, device=device) + rank * local < len(references))
            return values[0], values[1], mask
        record = self.shards[index]
        arrays = {
            key: np.load(self.path(record[key]), mmap_mode="r")
            for key in ("observations", "actions", "eligible")
        }
        turns, seats = arrays["eligible"].shape
        if turns != self.layout.observation.turns or not 1 <= seats <= 2:
            raise ValueError("sequence dimensions differ from complete teacher trajectories")
        if arrays["observations"].shape != (turns, seats, self.layout.observation.features):
            raise ValueError("sequence observation ABI mismatch")
        if arrays["actions"].shape != (turns, seats, self.layout.factors):
            raise ValueError("sequence action ABI mismatch")
        local = (seats + world - 1) // world
        chosen = np.arange(rank * local, (rank + 1) * local)
        present = chosen < seats
        chosen = np.minimum(chosen, seats - 1)
        observations = torch.from_numpy(np.array(arrays["observations"][:, chosen])).to(device)
        actions = torch.from_numpy(np.array(arrays["actions"][:, chosen], dtype=np.int64)).to(
            device
        )
        mask = torch.from_numpy(np.array(arrays["eligible"][:, chosen]) & present[None]).to(device)
        return observations, actions, mask

    def _pack(
        self, columns: list[tuple[np.ndarray, np.ndarray, np.ndarray]], device: torch.device
    ) -> list[Tensor]:
        """Copy into Torch-owned buffers without allocating large NumPy stack outputs.

        NumPy's large allocations can trigger expensive synchronous huge-page
        compaction. Reuse pinned host storage for CUDA transfers; CPU results
        retain independent ownership across calls. Blocking transfers ensure a
        host buffer is no longer in flight when the next episode overwrites it.
        """
        values = []
        for field, items in enumerate(zip(*columns, strict=True)):
            shape = (items[0].shape[0], len(items), *items[0].shape[1:])
            dtype = torch.from_numpy(np.empty(0, dtype=items[0].dtype)).dtype
            if device.type == "cuda" and field < len(self._host_buffers):
                host = self._host_buffers[field]
                if host.shape != shape or host.dtype != dtype:
                    raise ValueError("packed trajectory geometry changed without reconfiguration")
            else:
                host = torch.empty(shape, dtype=dtype, pin_memory=device.type == "cuda")
                if device.type == "cuda":
                    self._host_buffers.append(host)
            array = host.numpy()
            for index, item in enumerate(items):
                array[:, index] = item
            values.append(host.to(device))
        return values

    def _trajectory(self, index: int, seat: int) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        record = self.shards[index]
        arrays = {
            key: np.load(self.path(record[key]), mmap_mode="r")
            for key in ("observations", "actions", "eligible")
        }
        turns, seats = arrays["eligible"].shape
        if (
            turns != self.layout.observation.turns
            or not 1 <= seats <= 2
            or arrays["observations"].shape != (turns, seats, self.layout.observation.features)
            or arrays["actions"].shape != (turns, seats, self.layout.factors)
        ):
            raise ValueError("sequence dimensions differ from complete teacher trajectories")
        return (
            np.asarray(arrays["observations"][:, seat]),
            np.asarray(arrays["actions"][:, seat], dtype=np.int64),
            np.asarray(arrays["eligible"][:, seat]),
        )
