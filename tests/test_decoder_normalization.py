"""Check the fused-reduction repair preserves the exact native derivatives."""

import pytest
import torch

from kagg_revue.policy.grounded.normalization import LayerNorm


@pytest.mark.parametrize("shape", [(3, 192), (2, 32, 192)])
def test_native_forward_and_gradients(shape):
    torch.manual_seed(74001)
    reference = torch.nn.LayerNorm(shape[-1]).double()
    actual = LayerNorm(shape[-1]).double()
    actual.load_state_dict(reference.state_dict(), strict=True)
    x = torch.randn(shape, dtype=torch.float64, requires_grad=True)
    y = x.detach().clone().requires_grad_()
    gradient = torch.randn_like(x)
    expected = reference(x)
    observed = torch.compile(actual, backend="aot_eager", fullgraph=True)(y)
    torch.testing.assert_close(observed, expected, rtol=0, atol=0)
    expected.backward(gradient)
    observed.backward(gradient)
    for left, right in [
        (x.grad, y.grad),
        (reference.weight.grad, actual.weight.grad),
        (reference.bias.grad, actual.bias.grad),
    ]:
        torch.testing.assert_close(left, right, rtol=0, atol=0)
