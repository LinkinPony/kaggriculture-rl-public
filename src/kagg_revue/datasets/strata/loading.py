"""Bounded resident-shard staging for masked distributed BC batches."""

from collections.abc import Iterator

import numpy as np
import torch

from kagg_revue.datasets.demonstrations.loading import Dataset


class ResidentDataset(Dataset):
    """Transfer each selected shard once and gather shuffled minibatches on-device."""

    def batches(
        self,
        shard: int,
        batch_rows: int,
        device: torch.device,
        seed: tuple[int, ...] | None,
        *,
        rank: int = 0,
        world: int = 1,
    ) -> Iterator[tuple[torch.Tensor, torch.Tensor, torch.Tensor, int]]:
        """Preserve exact row weighting and padded last-batch semantics across ranks."""
        if batch_rows % world or not 0 <= rank < world:
            raise ValueError("resident BC batches must divide across ranks")
        record = self.shards[shard]
        arrays = {
            key: np.load(self.path(record[key]), mmap_mode="r")
            for key in ("observations", "actions", "origins", "quantity_coverage")
        }
        mask = np.asarray(arrays["quantity_coverage"]).copy()
        if "row_selection" in record:
            selection = np.load(self.path(record["row_selection"]), mmap_mode="r")
            if selection.shape != mask.shape or selection.dtype != np.bool_:
                raise ValueError("invalid resident row-selection mask")
            mask &= selection
        indices = np.flatnonzero(mask)
        if not len(indices):
            return
        expected = {
            "observations": (record["rows"], self.layout.observation.features),
            "actions": (record["rows"], self.layout.factors),
            "origins": (record["rows"], 2),
        }
        if any(arrays[key].shape != shape for key, shape in expected.items()):
            raise ValueError("resident shard shape differs from manifest")
        observations = torch.from_numpy(arrays["observations"][indices]).to(device)
        actions = torch.from_numpy(arrays["actions"][indices]).to(device)
        turns = torch.from_numpy(arrays["origins"][indices, 0].astype(np.int64)).to(device)
        ordering = np.arange(len(indices))
        if seed is not None:
            np.random.default_rng(seed).shuffle(ordering)
        for start in range(0, len(ordering), batch_rows):
            selected = ordering[start : start + batch_rows]
            count = len(selected)
            if count < batch_rows:
                selected = np.resize(selected, batch_rows)
            local = batch_rows // world
            positions = torch.from_numpy(selected[rank * local : (rank + 1) * local].copy()).to(
                device
            )
            yield observations[positions], actions[positions].long(), turns[positions], count
