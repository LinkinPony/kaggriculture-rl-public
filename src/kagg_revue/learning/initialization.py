"""Random neural roots with explicit, state-independent exploration priors."""

import math

import torch
from torch import nn

from kagg_revue.learning.config import Exploration
from kagg_revue.policy.contracts import ContractLayout
from kagg_revue.policy.grounded.model import GroundedPolicy
from kagg_revue.policy.spatial.model import Policy
from kagg_revue.policy.spatial.work import WorkPolicy


def _readout(head: nn.Module) -> nn.Linear:
    assert isinstance(head, nn.Sequential)
    layer = head[-1]
    assert isinstance(layer, nn.Linear)
    return layer


def random_policy(layout: ContractLayout, seed: int, exploration: Exploration) -> WorkPolicy:
    """Initialize random feedback and low-rate market actions without loading data.

    Uniform market op sampling spends the starting bank to zero in almost every
    full season. STOP odds and exponentially decaying quantity odds address
    this exploration degeneracy. They are trainable head biases, shared across
    time and states, not a script, demonstration, fixed mask, or time table.
    Every quantity retains finite support, including large terminal sells.
    """
    with torch.random.fork_rng(devices=[]):
        torch.set_rng_state(torch.Generator(device="cpu").manual_seed(seed).get_state())
        policy = Policy.from_layout(layout)
        assert isinstance(policy, WorkPolicy)
        for head in (*policy.jobs, *policy.market_heads):
            nn.init.normal_(_readout(head).weight, std=exploration.head_standard_deviation)
        stop = exploration.market_stop_probability
        quantities = torch.tensor(layout.observation.quantities)
        quantity_bias = (-exploration.quantity_decay * (quantities - 1)).clamp_min(-20)
        with torch.no_grad():
            market = _readout(policy.market_heads[0]).bias
            assert market is not None
            market[0] = math.log(22 * stop / (1 - stop))
            for head in (policy.jobs[2], policy.market_heads[1]):
                bias = _readout(head).bias
                assert bias is not None
                bias[: len(quantities)].copy_(quantity_bias)
            if isinstance(policy, GroundedPolicy) and layout.network.operation_quantity_bias:
                # Buying has immediate cash exposure; selling is capped by owned
                # inventory. Give all sell sizes initial support of similar mass,
                # with a separately trainable offset for every order operation.
                policy.quantity_offsets[2:11, : len(quantities)].copy_(-quantity_bias)
    return policy
