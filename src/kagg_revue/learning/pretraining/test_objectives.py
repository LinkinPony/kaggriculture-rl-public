"""Check domain weighting, rank imbalance, masking and partition-level selection."""

from datetime import timedelta
from pathlib import Path

import pytest
import torch
import torch.distributed as dist
import torch.multiprocessing as mp
from pydantic import ValidationError
from torch import Tensor

from kagg_revue.learning.optimization.learner import average_gradients
from kagg_revue.learning.pretraining.config import GroupedLoss, LossWeights
from kagg_revue.learning.pretraining.objectives import SupervisedLoss
from kagg_revue.learning.pretraining.telemetry import partition_nll


def _fields() -> Tensor:
    fields = torch.zeros(4, 20)
    fields[0, [0, 1, 2, 8, 9, 16, 17, 18]] = 1
    fields[1, [0, 8, 16]] = 1
    fields[2, :] = 1  # Context-only row must contribute no fields.
    fields[3, [0, 1, 8, 16, 18]] = 1
    return fields


def _expected(likelihood: Tensor, fields: Tensor, eligible: Tensor) -> Tensor:
    active = fields * eligible[:, None]
    result = likelihood.sum() * 0
    for columns, weight in zip(
        ([0, 8], [1, 9], [2, 10], [16, 18], [17, 19]), (1, 1, 1, 3, 1), strict=True
    ):
        result -= (
            (likelihood[:, columns] * active[:, columns]).sum()
            / active[:, columns].sum().clamp_min(1)
            * weight
            / 7
        )
    return result


def _objective() -> SupervisedLoss:
    return SupervisedLoss(GroupedLoss(weights=LossWeights(market_operation=3)), units=2)


def test_chunks_and_masked_rows_preserve_complete_batch_gradient() -> None:
    """Compare uneven chunks with a direct five-term objective and absent categories."""
    fields = _fields()
    fields[:, [2, 10]] = 0  # No quantities anywhere: other weights must stay fixed.
    eligible = torch.tensor([True, True, False, True])
    logits = torch.randn(4, 20, 3, generator=torch.Generator().manual_seed(29), requires_grad=True)
    likelihood = logits.log_softmax(-1)[..., 0]
    expected = _expected(likelihood, fields, eligible)
    (reference,) = torch.autograd.grad(expected, logits, retain_graph=True)
    objective = _objective()
    scales = objective.scales(fields, eligible)
    compiled = torch.compile(objective, backend="eager", fullgraph=True)
    actual = sum(
        compiled(likelihood[s], fields[s], eligible[s], eligible.sum(), scales)
        for s in (slice(0, 1), slice(1, 3), slice(3, 4))
    )
    assert isinstance(actual, Tensor)
    actual.backward()  # type: ignore[no-untyped-call]
    torch.testing.assert_close(actual, expected)
    torch.testing.assert_close(logits.grad, reference)
    assert logits.grad is not None and not logits.grad[2].any()


def test_more_workers_do_not_reduce_market_gradient() -> None:
    """Duplicating unit fields changes neither domain losses nor market coefficients."""
    objective = _objective()
    fields = torch.zeros(1, 20)
    fields[0, [0, 1, 2, 16, 17]] = 1
    likelihood = torch.full((1, 20), -2.0, requires_grad=True)
    eligible = torch.ones(1, dtype=torch.bool)
    first = objective(
        likelihood, fields, eligible, eligible.sum(), objective.scales(fields, eligible)
    )
    (first_gradient,) = torch.autograd.grad(first, likelihood)
    fields[0, [8, 9, 10]] = 1
    second = objective(
        likelihood, fields, eligible, eligible.sum(), objective.scales(fields, eligible)
    )
    (second_gradient,) = torch.autograd.grad(second, likelihood)
    torch.testing.assert_close(first, second)
    torch.testing.assert_close(first_gradient[:, 16:], second_gradient[:, 16:])


def _distributed(rank: int, directory: str) -> None:
    torch.set_num_threads(1)
    root = Path(directory)
    dist.init_process_group(
        "gloo",
        init_method=f"file://{root / 'rendezvous'}",
        rank=rank,
        world_size=2,
        timeout=timedelta(seconds=30),
    )
    try:
        for tail in (False, True):
            parameter = torch.nn.Parameter(torch.linspace(-1, 1, 60).reshape(20, 3))
            fields = _fields()
            eligible = torch.tensor([True, True, False, not tail])
            reference = parameter.detach().clone().requires_grad_()
            expected = _expected(reference.log_softmax(-1)[:, 0].expand(4, -1), fields, eligible)
            expected.backward()  # type: ignore[no-untyped-call]
            section = slice(rank * 2, (rank + 1) * 2)
            local_fields, local_mask = fields[section], eligible[section]
            objective = _objective()
            scales = objective.scales(local_fields, local_mask)
            likelihood = parameter.log_softmax(-1)[:, 0].expand(2, -1)
            loss = objective(likelihood, local_fields, local_mask, eligible.sum() / 2, scales)
            loss.backward()  # type: ignore[no-untyped-call]
            average_gradients([parameter])
            dist.all_reduce(loss.detach())
            torch.testing.assert_close(parameter.grad, reference.grad)
            torch.testing.assert_close(loss.detach() / 2, expected.detach())
    finally:
        dist.destroy_process_group()


def test_two_ranks_match_one_batch_including_empty_tail_rank(tmp_path: Path) -> None:
    """One quantity exists globally, and the second case has an entirely padded rank."""
    mp.spawn(  # type: ignore[attr-defined, no-untyped-call]
        _distributed, args=(str(tmp_path),), nprocs=2, join=True
    )


def test_selection_aggregates_fields_before_normalizing() -> None:
    """Unequal validation groups cannot change the selected objective."""
    first = [2.0, 0.0, 1.0] * 5
    second = [8.0, 0.0, 4.0] * 3 + [90.0, 0.0, 9.0] + [0.0, 0.0, 0.0]
    records = [
        {"loss_sum": 2.0, "rows": 1, "field_totals": first},
        {"loss_sum": 50.0, "rows": 5, "field_totals": second},
    ]
    merged = [
        {
            "loss_sum": 52.0,
            "rows": 6,
            "field_totals": [a + b for a, b in zip(first, second, strict=True)],
        }
    ]
    assert partition_nll(records, GroupedLoss()) == pytest.approx((2 * 4 + 9.2) / 5)
    assert partition_nll(records, GroupedLoss()) == partition_nll(merged, GroupedLoss())
    assert partition_nll(records, None) == 52 / 6


def test_field_mean_shares_one_weighted_denominator() -> None:
    """Chunked field-mean equals the batch objective; selection uses the same weights."""
    fields = _fields()
    eligible = torch.tensor([True, True, False, True])
    likelihood = torch.randn(4, 20, generator=torch.Generator().manual_seed(31))
    config = GroupedLoss(normalization="field_mean", weights=LossWeights(market_operation=3))
    objective = SupervisedLoss(config, units=2)
    scales = objective.scales(fields, eligible)
    actual = sum(
        objective(likelihood[s], fields[s], eligible[s], eligible.sum(), scales)
        for s in (slice(0, 2), slice(2, 4))
    )
    multipliers = torch.ones(20)
    multipliers[[16, 18]] = 3
    active = fields * eligible[:, None] * multipliers
    torch.testing.assert_close(actual, -(likelihood * active).sum() / active.sum())
    second = [8.0, 0.0, 4.0] * 3 + [90.0, 0.0, 9.0] + [0.0, 0.0, 0.0]
    records = [
        {"loss_sum": 1.0, "rows": 1, "field_totals": [2.0, 0.0, 1.0] * 5},
        {"loss_sum": 1.0, "rows": 1, "field_totals": second},
    ]
    assert partition_nll(records, config) == pytest.approx((30 + 3 * 92 + 2) / (15 + 3 * 10 + 1))


def test_invalid_weights_are_rejected_and_zero_weights_are_supported() -> None:
    """Bad configurations fail before training, while individual domains can be disabled."""
    for value in (-1.0, float("nan"), float("inf")):
        with pytest.raises(ValidationError):
            LossWeights(market_operation=value)
    with pytest.raises(ValidationError):
        LossWeights(
            unit_target=0, unit_operation=0, unit_quantity=0, market_operation=0, market_quantity=0
        )
    assert LossWeights(unit_quantity=0).unit_quantity == 0
