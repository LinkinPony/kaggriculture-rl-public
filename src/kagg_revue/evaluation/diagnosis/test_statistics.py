"""Ensure strategic metrics distinguish rare decisions from forced legal choices."""

import numpy as np
import pytest
import torch

from kagg_revue.evaluation.diagnosis.actions import present
from kagg_revue.evaluation.diagnosis.statistics import aggregate, totals


def test_rare_operation_counts_and_forced_support() -> None:
    """Keep STOP, animal quantities and forced unit actions in the intended groups."""
    logits = torch.zeros(2, 12, 44)
    actions = torch.zeros(2, 12, dtype=torch.long)
    fields = torch.zeros(2, 12)
    actions[0, 1] = 35
    logits[0, 1] = -1e9
    logits[0, 1, 35] = 0
    fields[0, 1] = 1
    actions[0, 8:10] = torch.tensor([18, 1])
    fields[0, 8:11] = 1
    fields[1, 8] = 1
    result = aggregate([{"totals": totals(logits, actions, fields, 1)}])
    assert result["unit_operation"]["accuracy"] == 1
    assert "unit_operation/multiple_choices" not in result
    assert result["market/BUY_ANIMAL:GOOSE"]["count"] == 1
    assert result["market/STOP"]["count"] == 2
    assert result["quantity/BUY_ANIMAL:GOOSE"]["count"] == 1
    assert "quantity/STOP" not in result
    assert result["market/BUY_ANIMAL:GOOSE"]["teacher_probability"] == pytest.approx(1 / 44)


def test_order_insensitive_membership_respects_stop() -> None:
    """Ignore operation positions but exclude any stale slots beyond STOP."""
    actions = np.zeros((3, 14), dtype=np.int16)
    actions[:, 8::2] = [[18, 2, 0], [2, 18, 0], [0, 18, 2]]
    mask = present(actions, 8)
    assert np.array_equal(mask[0], mask[1])
    assert mask[:, 18].tolist() == [True, True, False]
