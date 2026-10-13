"""Necessary checks for causal and episode-safe temporal processing."""

import torch

from kagg_revue.policy.memory.blocks import Gate
from kagg_revue.policy.memory.temporal import TemporalMemory


def test_chunking_and_future_isolation() -> None:
    """Segmented inference must agree across window eviction and ignore future frames."""
    torch.set_num_threads(1)
    torch.manual_seed(10)
    model = TemporalMemory(16, 2, 2, turns=5, tokens=4).eval()
    values = torch.randn(2, 13, 4, 16)
    with torch.no_grad():
        complete, _ = model(values, model.empty(2, torch.device("cpu")), torch.arange(13))
        state = model.empty(2, torch.device("cpu"))
        pieces = []
        for start in range(0, 13, 3):
            end = min(start + 3, 13)
            output, state = model(values[:, start:end], state, torch.arange(start, end))
            pieces.append(output)
        torch.testing.assert_close(torch.cat(pieces, 1), complete, atol=2e-6, rtol=2e-5)
        assert state.turns.tolist() == [turn for turn in range(8, 13) for _ in range(4)]
        inference = model.inference_empty(2, torch.device("cpu"))
        cached = []
        for turn in range(13):
            output, inference = model.step(values[:, turn], inference, torch.tensor([turn]))
            cached.append(output)
        torch.testing.assert_close(torch.stack(cached, 1), complete, atol=2e-6, rtol=2e-5)
        assert torch.equal(inference.turns, state.turns)
        changed = values.clone()
        changed[:, 7:] = torch.randn_like(changed[:, 7:]) * 20
        altered, _ = model(changed, model.empty(2, torch.device("cpu")), torch.arange(13))
        torch.testing.assert_close(altered[:, :7], complete[:, :7], atol=2e-6, rtol=2e-5)


def test_cache_capacity_and_episode_reset() -> None:
    """384 turns means 1536 summary slots, and a fresh episode receives empty state."""
    model = TemporalMemory(16, 2, 2, turns=384, tokens=4)
    state = model.empty(2, torch.device("cpu"))
    assert state.turns.shape == (1536,)
    assert all(layer.shape == (2, 1536, 16) for layer in state.layers)
    assert (state.turns == -1).all()
    state.layers[0][0].fill_(1)
    assert (state.layers[0][1] == 0).all()
    assert (model.empty(2, torch.device("cpu")).layers[0] == 0).all()


def test_gate_identity_bias_and_gradients() -> None:
    """The update bias is subtracted and every gate branch remains trainable."""
    gate = Gate(8)
    assert torch.equal(gate.bias, torch.full((8,), 2.0))
    x, y = torch.randn(3, 8), torch.randn(3, 8)
    gate(x, y).square().mean().backward()
    for parameter in gate.parameters():
        assert parameter.grad is not None
        assert torch.isfinite(parameter.grad).all()
        assert parameter.grad.abs().sum() > 0
