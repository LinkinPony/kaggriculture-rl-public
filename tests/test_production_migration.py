import pytest
import torch

from kagg_revue.production.migration.objectives import (
    distillation_rows,
    scheduled_scale,
)
from kagg_revue.production.migration.runtime import GradientBuffers, GraphReplay


def test_distillation_masks_fields_and_only_trains_the_student() -> None:
    student = torch.tensor([[[0.0, 0.0], [1.0, -1.0]]], requires_grad=True)
    teacher = torch.tensor([[[3.0, -2.0], [-5.0, 5.0]]], requires_grad=True)
    fields = torch.tensor([[1.0, 0.0]])
    loss = distillation_rows(student, teacher, fields, 1.7).sum()
    loss.backward()
    assert teacher.grad is None
    assert student.grad is not None
    assert student.grad[0, 0, 0] < 0 < student.grad[0, 0, 1]
    assert torch.count_nonzero(student.grad[0, 1]) == 0
    shifted = teacher.detach() + torch.tensor([[[9.0], [-4.0]]])
    torch.testing.assert_close(
        distillation_rows(shifted, teacher, fields, 1.7), torch.zeros(1), atol=1e-6, rtol=0
    )


def test_fade_uses_completed_intervals_and_stays_at_zero() -> None:
    values = [scheduled_scale(0.37, elapsed, 3, 0.13) for elapsed in range(13)]
    assert values[:3] == [0.37] * 3
    assert values[3:6] == [0.24] * 3
    assert values[6:9] == [0.11] * 3
    assert values[9:] == [0.0] * 4


@pytest.mark.skipif(not torch.cuda.is_available(), reason="autograd graph needs CUDA")
@pytest.mark.parametrize("precision", ["fp32", "bf16"])
def test_graph_microbatches_accumulate_without_aliasing_reused_outputs(precision: str) -> None:
    class Projection(torch.nn.Module):
        def __init__(self) -> None:
            super().__init__()
            self.layer = torch.nn.Linear(2, 2)

        def forward(self, observations, steps, actions):
            return self.layer(observations)

    model = Projection().cuda()
    inputs = torch.randn(3, 2, device="cuda")
    times = torch.zeros(3, dtype=torch.long, device="cuda")
    actions = torch.zeros(3, 1, dtype=torch.long, device="cuda")
    graph = GraphReplay(model, {3}, precision)
    gradients = GradientBuffers(model.parameters())
    gradients.zero()
    for scale in (1.0, 2.0, 4.0):
        graph(inputs * scale, times, actions).sum().backward()
    result = [parameter.grad.clone() for parameter in model.parameters()]
    gradients.zero()
    for scale in (1.0, 2.0, 4.0):
        with torch.autocast("cuda", dtype=torch.bfloat16, enabled=precision == "bf16"):
            model(inputs * scale, times, actions).sum().backward()
    for actual, parameter in zip(result, model.parameters(), strict=True):
        torch.testing.assert_close(actual, parameter.grad)
