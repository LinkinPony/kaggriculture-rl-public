import pytest
import torch
from torch.nn import functional as F

from kagg_revue.policy.spatial.attention import masked_attention


@pytest.mark.skipif(not torch.cuda.is_available(), reason="compiled attention requires CUDA")
@pytest.mark.parametrize("width", [40, 48])
def test_masked_attention_matches_fp32_and_reads_updated_mask(width):
    torch.manual_seed(74021)
    inputs = tuple(
        torch.randn(2, 4, 286, width, device="cuda", dtype=torch.bfloat16).requires_grad_()
        for _ in range(3)
    )
    reference = tuple(x.detach().float().requires_grad_() for x in inputs)
    valid = torch.ones(2, 286, device="cuda", dtype=torch.bool)
    gradient = torch.randn_like(inputs[0])
    compiled = torch.compile(masked_attention, fullgraph=True, dynamic=False)
    for sparse in (False, True):
        if sparse:
            valid[:, 1::2] = False
            valid[0, 47:] = False
        expected = F.scaled_dot_product_attention(*reference, valid[:, None, None, :])
        expected_grad = torch.autograd.grad(expected, reference, gradient.float())
        actual = compiled(*inputs, valid)
        actual_grad = torch.autograd.grad(actual, inputs, gradient)
        for result, control in zip((actual, *actual_grad), (expected, *expected_grad), strict=True):
            assert bool(result.isfinite().all())
            error = (result.detach().float() - control.detach()).norm() / control.detach().norm()
            assert float(error) < 0.008
        if sparse:
            for grad in actual_grad[1:]:
                assert torch.count_nonzero(grad.masked_select(~valid[:, None, :, None])) == 0
