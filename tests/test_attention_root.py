from copy import deepcopy

import torch

from kagg_revue.policy.effects.attention import pack_entities
from kagg_revue.policy.transformer import EncoderBlock


def test_root_attention_preserves_outputs_and_all_gradients() -> None:
    torch.manual_seed(13)
    reference = EncoderBlock(12, 3, 20, 16).double()
    selective = deepcopy(reference)
    inputs = torch.randn(3, 7, 12, dtype=torch.double, requires_grad=True)
    other_inputs = inputs.detach().clone().requires_grad_()
    valid = torch.arange(7)[None] < torch.tensor([1, 4, 7])[:, None]
    positions = torch.tensor([0, 2, 3, 6, 8, 9, 11])

    expected = reference(inputs, valid, causal=False, positions=positions)[:, :1]
    actual = selective.forward_root(other_inputs, valid, positions=positions)
    torch.testing.assert_close(actual, expected)
    expected.square().sum().backward()
    actual.square().sum().backward()
    torch.testing.assert_close(other_inputs.grad, inputs.grad)
    for actual_parameter, expected_parameter in zip(
        selective.parameters(), reference.parameters(), strict=True
    ):
        torch.testing.assert_close(actual_parameter.grad, expected_parameter.grad)


def test_entity_packing_preserves_multilayer_root_and_gradients() -> None:
    torch.manual_seed(19)
    reference = torch.nn.ModuleList([EncoderBlock(12, 3, 20, 16).double() for _ in range(2)])
    compact = deepcopy(reference)
    inputs = torch.randn(2, 8, 12, dtype=torch.double, requires_grad=True)
    other_inputs = inputs.detach().clone().requires_grad_()
    valid = torch.tensor(
        [
            [True, False, True, False, False, True, False, False],
            [True, True, False, False, True, False, False, True],
        ]
    )
    positions = torch.tensor([0, 1, 3, 4, 6, 8, 10, 13])
    hidden, mask, packed_positions = pack_entities(other_inputs, valid, positions, 4)
    expected = inputs
    for block in reference:
        expected = block(expected, valid, causal=False, positions=positions)
    hidden = compact[0](hidden, mask, causal=False, positions=packed_positions)
    actual = compact[1].forward_root(hidden, mask, positions=packed_positions)
    expected = expected[:, :1]
    torch.testing.assert_close(actual, expected)
    expected.square().sum().backward()
    actual.square().sum().backward()
    torch.testing.assert_close(other_inputs.grad, inputs.grad)
    for left, right in zip(compact.parameters(), reference.parameters(), strict=True):
        torch.testing.assert_close(left.grad, right.grad)
