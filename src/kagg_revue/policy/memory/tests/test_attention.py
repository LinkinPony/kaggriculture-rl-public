"""Gradient and padding regressions for fused relative-time attention."""

import copy

import pytest
import torch

from kagg_revue.learning.performance.temporal import dense_attention
from kagg_revue.policy.memory import temporal
from kagg_revue.policy.memory.attention import relative_attention
from kagg_revue.policy.memory.temporal import TemporalMemory


@pytest.mark.skipif(not torch.cuda.is_available(), reason="compiled CUDA attention required")
@pytest.mark.parametrize("start", [0, 5])
def test_compiled_temporal_gradients_and_padding(
    start: int, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Match dense SDPA with empty caches, causal masking and full-window eviction."""
    torch.manual_seed(73001)
    torch.set_num_threads(2)
    reference = TemporalMemory(32, 2, 2, turns=5, tokens=4).cuda()
    optimized = copy.deepcopy(reference)
    reference.compile(fullgraph=True, dynamic=False, options={"triton.cudagraphs": False})
    optimized.compile(fullgraph=True, dynamic=False, options={"triton.cudagraphs": False})
    inputs = torch.randn(2, 7, 4, 32, device="cuda")
    gradient = torch.randn_like(inputs)
    state = reference.empty(2, torch.device("cuda"))
    if start:
        state.turns.copy_(torch.arange(start - 5, start, device="cuda").repeat_interleave(4))
        for layer in state.layers:
            layer.normal_()
    steps = torch.arange(start, start + 7, device="cuda")
    monkeypatch.setattr(temporal, "relative_attention", dense_attention)
    with torch.autocast("cuda", dtype=torch.bfloat16):
        expected, expected_state = reference(inputs, state, steps)
    expected.backward(gradient)
    monkeypatch.setattr(temporal, "relative_attention", relative_attention)
    with torch.autocast("cuda", dtype=torch.bfloat16):
        actual, actual_state = optimized(inputs, state, steps)
    actual.backward(gradient)
    torch.testing.assert_close(actual, expected, atol=0.015, rtol=0.02)
    assert torch.equal(actual_state.turns, expected_state.turns)
    for (name, before), after in zip(
        reference.named_parameters(), optimized.parameters(), strict=True
    ):
        assert before.grad is not None and after.grad is not None
        assert torch.isfinite(after.grad).all()
        relative = (after.grad - before.grad).norm() / before.grad.norm().clamp_min(1e-6)
        assert float(relative) < 0.04, (name, float(relative), float(before.grad.norm()))
