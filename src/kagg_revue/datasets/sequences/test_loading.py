"""Check that distributed packing preserves every teacher trajectory exactly once."""

from pathlib import Path
from types import SimpleNamespace
from typing import cast

import numpy as np
import pytest
import torch

from kagg_revue.datasets.sequences.loading import SequenceDataset
from kagg_revue.policy.contracts import ContractLayout


@pytest.mark.parametrize("validation_name", ["selection", "val"])
def test_grouped_complete_trajectories(tmp_path: Path, validation_name: str) -> None:
    """Seats can share batches across games; clocks, masks and split isolation remain exact."""
    dataset = SequenceDataset.__new__(SequenceDataset)
    dataset.directory = tmp_path
    dataset.layout = cast(
        ContractLayout,
        SimpleNamespace(observation=SimpleNamespace(turns=4, features=2), factors=1),
    )
    dataset.manifest = {"sequence_format": "complete-turn-seat-v1"}
    dataset.shards = []
    for episode, seats in enumerate((2, 1, 2, 2)):
        observations = np.zeros((4, seats, 2), dtype=np.float16)
        observations[:, :, 0] = episode * 10 + np.arange(seats)
        observations[:, :, 1] = np.arange(4)[:, None]
        actions = np.zeros((4, seats, 1), dtype=np.int64)
        eligible = np.ones((4, seats), dtype=np.bool_)
        if episode == 0:
            eligible[2, 0] = False
        record = {
            "split": validation_name if episode == 3 else "train",
            "task": {"seats": list(range(seats))},
        }
        for name, values in (
            ("observations", observations),
            ("actions", actions),
            ("eligible", eligible),
        ):
            path = tmp_path / f"{episode}-{name}.npy"
            np.save(path, values)
            record[name] = path.name
        dataset.shards.append(record)
    dataset.configure(batch_rows=16, world=2, seed=19)
    identifiers, rows = [], 0
    retained = []
    for index in dataset.partition("train"):
        for rank in range(2):
            inputs, targets, mask = dataset.episode(index, torch.device("cpu"), rank, 2)
            references = dataset.groups[index]
            columns = [
                dataset._trajectory(*references[min(i, len(references) - 1)])
                for i in range(rank * 2, (rank + 1) * 2)
            ]
            expected = [
                torch.from_numpy(np.stack(items, axis=1)) for items in zip(*columns, strict=True)
            ]
            expected[2] &= torch.arange(2) + rank * 2 < len(references)
            for actual, reference in zip((inputs, targets, mask), expected, strict=True):
                torch.testing.assert_close(actual, reference, rtol=0, atol=0)
                assert actual.is_contiguous()
                retained.append((actual, actual.clone()))
            assert inputs.shape == (4, 2, 2) and targets.shape == (4, 2, 1)
            assert torch.equal(inputs[:, :, 1], torch.arange(4)[:, None].expand(-1, 2))
            identifiers.extend(inputs[0, mask.any(0), 0].tolist())
            rows += int(mask.sum())
    assert sorted(identifiers) == [0, 1, 10, 20, 21]
    assert rows == 19
    assert len(dataset.partition("selection")) == 1
    if validation_name == "val":
        assert dataset.partition("val") == dataset.partition("selection")
        assert dataset.partition("confirmation") == []
    for actual, reference in retained:
        torch.testing.assert_close(actual, reference, rtol=0, atol=0)
