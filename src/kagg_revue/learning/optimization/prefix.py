"""Causal public-state and plan-prefix values for terminal-outcome PPO."""

from typing import cast

import torch
from torch import Tensor, nn
from torch.nn import functional as F

from kagg_revue.policy.contracts import ContractLayout
from kagg_revue.policy.grounded.fields import semantic_fields
from kagg_revue.policy.spatial.model import Critic


class PrefixCritic(Critic):
    """Predict V(h) and V(h, a_<k) with one independent observation encoder.

    Work fields use the native flattened order: unit, job, field, then market
    time, order, field. Parallel actor branches are conditionally independent,
    so this is a valid factorization of the unchanged actor distribution.
    Exclusive prefix pooling never reads the current or a future choice.
    """

    owners: Tensor
    roles: Tensor
    symbol_offsets: Tensor
    semantic_fields: Tensor
    restore_fields: Tensor

    def __init__(self, layout: ContractLayout) -> None:
        """Retain the state critic and add a compact causal action summary."""
        if not layout.work or not layout.network.critic_depth:
            raise ValueError("prefix values require a work policy with an entity critic")
        super().__init__(layout)
        width = layout.network.critic_width
        self.vocabulary_size = layout.vocabulary_size
        cardinalities = (
            [
                layout.cells + 1,
                44,
                len(layout.observation.quantities),
                1,
                23,
                len(layout.observation.quantities),
            ]
            if layout.network.architecture == "grounded-v2"
            else [self.vocabulary_size] * 6
        )
        self.symbols = nn.Embedding(sum(cardinalities), width)
        self.register_buffer(
            "symbol_offsets", torch.tensor([0, *cardinalities[:-1]]).cumsum(0), persistent=False
        )
        self.positions = nn.Parameter(torch.empty(layout.factors, width))
        nn.init.normal_(self.positions, std=width**-0.5)
        readout = nn.Linear(width, 1)
        self.delta = nn.Sequential(nn.Linear(2 * width, width), nn.GELU(), readout)
        # The initial prefix interface agrees with the state interface everywhere.
        nn.init.zeros_(readout.weight)
        nn.init.zeros_(readout.bias)
        jobs = layout.observation.units * (layout.capacity + 1)
        roles = torch.cat(
            (
                torch.arange(4).repeat(jobs),
                torch.arange(4, 6).repeat(layout.capacity * layout.observation.markets),
            )
        )
        owners = torch.cat(
            (
                (torch.arange(layout.observation.units) + 1 + 2 * layout.cells).repeat_interleave(
                    (layout.capacity + 1) * 4
                ),
                torch.zeros(layout.factors - layout.work_factors, dtype=torch.long),
            )
        )
        self.register_buffer("roles", roles)
        self.register_buffer("owners", owners)
        selected = (
            semantic_fields(layout)
            if layout.network.architecture == "grounded-v2"
            else torch.arange(layout.factors)
        )
        self.register_buffer("semantic_fields", selected, persistent=False)
        self.register_buffer(
            "restore_fields",
            torch.searchsorted(selected, torch.arange(layout.factors)),
            persistent=False,
        )

    def prefixes(
        self, observations: Tensor, actions: Tensor, fields: Tensor, *, compact: bool = False
    ) -> tuple[Tensor, Tensor]:
        """Return the state value and every pre-choice value, including STOP."""
        assert self.entity_encoder is not None
        return self.prefixes_encoded(
            self.entity_encoder(observations), actions, fields, compact=compact
        )

    def prefixes_encoded(
        self, encoded: Tensor, actions: Tensor, fields: Tensor, *, compact: bool = False
    ) -> tuple[Tensor, Tensor]:
        """Score values from an explicit scene while preserving exclusive prefix semantics."""
        state = encoded[:, 0]
        value = cast(Tensor, self.network(state)).float().squeeze(-1)
        positions: Tensor = self.positions
        roles, owners = self.roles, self.owners
        if compact:
            selected = self.semantic_fields
            actions, fields = actions[:, selected], fields[:, selected]
            roles, positions, owners = roles[selected], positions[selected], owners[selected]
        symbols = self.symbols(actions + self.symbol_offsets[roles])
        content = torch.tanh(symbols + positions + encoded[:, owners])
        content = content.float() * fields[..., None]
        # Shift before scanning: subtraction of inclusive sums can leak suffix
        # choices through floating-point cancellation at the current field.
        prefix = F.pad(content[:, :-1], (0, 0, 1, 0)).cumsum(1)
        count = F.pad(fields[:, :-1], (1, 0)).cumsum(1)
        prefix = prefix / count.clamp_min(1).sqrt()[..., None]
        context = state[:, None].expand(-1, actions.shape[1], -1)
        delta = self.delta(torch.cat((context, prefix), -1)).float().squeeze(-1)
        prefixes = value[:, None] + torch.where(count > 0, delta, 0.0)
        # Padding has zero field weight, so its exclusive prefix equals the next
        # semantic column's prefix. Restore the complete ABI and its loss divisor.
        return value, prefixes[:, self.restore_fields] if compact else prefixes


@torch.no_grad()
def prefix_credit(
    values: Tensor, fields: Tensor, returns: Tensor, trace_lambda: float = 0.0
) -> Tensor:
    """Estimate gamma=1 prefix advantages with configurable GAE traces.

    Lambda zero retains the historical adjacent-value estimator. Lambda one
    uses the observed terminal return minus each exclusive prefix baseline;
    its on-policy expected gradient needs no accurate downstream value model.
    Intermediate lambdas trade variance for bootstrap bias. Only active choices
    advance the trace: padding and fields after STOP never consume a discount.
    """
    if not 0 <= trace_lambda <= 1:
        raise ValueError("prefix trace lambda must lie in [0, 1]")
    if trace_lambda == 1:
        return torch.where(fields.bool(), returns[:, None] - values, 0.0)
    width = values.shape[1]
    indices = torch.arange(width, device=values.device).expand_as(values)
    active_indices = torch.where(fields.bool(), indices, width)
    next_active = active_indices.flip(1).cummin(1).values.flip(1)
    successors = F.pad(next_active[:, 1:], (0, 1), value=width)
    downstream = torch.cat((values, returns[:, None]), 1).gather(1, successors)
    credit = torch.where(fields.bool(), downstream - values, 0.0)
    if trace_lambda == 0:
        return credit
    # Compose affine recurrences in log(width) bulk device operations. Inactive
    # columns carry the continuation unchanged instead of shortening the trace.
    discount = torch.where(fields.bool(), trace_lambda, 1.0)
    stride = 1
    while stride < width:
        credit = credit + discount * F.pad(credit[:, stride:], (0, stride))
        discount = discount * F.pad(discount[:, stride:], (0, stride))
        stride *= 2
    return torch.where(fields.bool(), credit, 0.0)


def prefix_surrogate(
    log_ratio: Tensor, fields: Tensor, advantages: Tensor, clip: float
) -> tuple[Tensor, Tensor]:
    """Clip conditional ratios and sum credit without sampled-length reweighting."""
    log_ratio = torch.where(fields.bool(), log_ratio, 0.0)
    ratio = log_ratio.exp()
    gain = torch.minimum(ratio * advantages, ratio.clamp(1 - clip, 1 + clip) * advantages)
    return (gain * fields).sum(-1), ((ratio - 1 - log_ratio) * fields).sum(-1)


def prefix_value_rows(
    values: Tensor, prefixes: Tensor, returns: Tensor, fields: Tensor, prefix_weight: float
) -> tuple[Tensor, Tensor, Tensor]:
    """Fit expected terminal outcomes with squared error at both value interfaces."""
    state_loss = (values - returns).square()
    # The first active prefix is exactly V(h), already covered by state_loss.
    inner = fields * (fields.cumsum(1) > 1)
    prefix_loss = ((prefixes - returns[:, None]).square() * inner).sum(1)
    # Use a fixed ABI width: normalization by sampled continuation length would
    # change the conditional terminal expectation that a prefix learns.
    prefix_loss = prefix_loss / max(1, prefixes.shape[1] - 1)
    return state_loss + prefix_weight * prefix_loss, state_loss, prefix_loss
