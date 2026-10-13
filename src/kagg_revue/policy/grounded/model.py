"""Causal local work decisions with no sampled choices for missing units."""

import torch
from torch import Tensor, nn
from torch.nn import functional as F

from kagg_revue.policy.contracts import ContractLayout
from kagg_revue.policy.spatial.work import WorkPolicy


class GroundedPolicy(WorkPolicy):
    """Choose PASS, one neighboring move, or a supported on-tile operation.

    Every raw unit operation remains expressible. Market orders retain their
    complete ordering and quantity vocabulary. The native support is exact
    for an isolated unit at quantity one; shared-stock conflicts and market
    effects are resolved by the official executor. No future unit is sampled.
    """

    cell_x: Tensor
    cell_y: Tensor
    quantity_offsets: Tensor

    def __init__(self, layout: ContractLayout) -> None:
        """Reuse observation attention and the work ABI at one-turn resolution."""
        if layout.capacity != 1 or layout.network.time_prior:
            raise ValueError("grounded policies require single turns without a time prior")
        if layout.observation.support_features != layout.observation.units * 44:
            raise ValueError("grounded policy requires authenticated native unit support")
        super().__init__(layout)
        if layout.network.operation_quantity_bias:
            self.quantity_offsets = nn.Parameter(torch.zeros(23, layout.vocabulary_size))
        self.register_buffer("cell_x", torch.arange(layout.cells) % layout.board_size)
        self.register_buffer("cell_y", torch.arange(layout.cells) // layout.board_size)

    def _units(self, observations: Tensor) -> tuple[Tensor, Tensor, Tensor]:
        base = self.layout.observation
        units = observations[
            :, base.board_features : base.board_features + base.units * base.unit_features
        ]
        units = units.reshape(-1, base.units, base.unit_features)
        positions = (units[..., 2:4].float() * (self.layout.board_size - 1)).round().long()
        current = positions[..., 1] * self.layout.board_size + positions[..., 0]
        support = observations[:, -base.support_features :].reshape(-1, base.units, 44) > 0
        return positions, current, support

    def _decode(
        self,
        observations: Tensor,
        steps: Tensor,
        actions: Tensor | None,
        sample: bool,
        temperature: float | Tensor = 1.0,
    ) -> tuple[Tensor, Tensor]:
        layout = self.layout
        n, units, vocabulary = len(observations), layout.observation.units, layout.vocabulary_size
        encoded = self.encoder(observations)
        positions, current, legal = self._units(observations)
        present = legal[..., 0]
        unit_start = 1 + 2 * layout.cells
        hidden = encoded[:, unit_start : unit_start + units] * present[..., None]
        distance = (positions[..., :1] - self.cell_x).abs()
        distance = distance + (positions[..., 1:] - self.cell_y).abs()
        target_support = present[..., None] & (
            (distance == 1) | ((distance == 0) & legal[..., 5:].any(-1, keepdim=True))
        )
        target_support = F.pad(target_support, (1, vocabulary - layout.cells - 1), value=False)
        target_support[..., 0] = True
        supplied = (
            None if actions is None else actions[:, : layout.work_factors].reshape(n, units, 2, 4)
        )
        target_logits = self.jobs[0](hidden).float().masked_fill(~target_support, -1e9)
        target = self.choose(
            target_logits, None if supplied is None else supplied[:, :, 0, 0], sample, temperature
        )
        tile = encoded[:, 1 : 1 + layout.cells].gather(
            1,
            (target - 1).clamp_min(0)[..., None].expand(-1, -1, hidden.shape[-1]),
        )
        hidden = hidden + self.job_embeddings[0](target) + tile * (target > 0)[..., None]
        local = (target > 0) & (target == current + 1)
        op_support = F.pad(legal, (0, vocabulary - 44))
        op_support[..., :5] = False
        op_support = torch.where(local[..., None], op_support, self.singleton)
        op_logits = self.jobs[1](hidden).float().masked_fill(~op_support, -1e9)
        op = self.choose(
            op_logits, None if supplied is None else supplied[:, :, 0, 1], sample, temperature
        )
        hidden = hidden + self.job_embeddings[1](op)
        has_quantity = ((op >= 5) & (op < 17)) | ((op >= 18) & (op < 30))
        quantity_support = torch.arange(vocabulary, device=observations.device) < len(
            layout.observation.quantities
        )
        quantity_support = torch.where(has_quantity[..., None], quantity_support, self.singleton)
        quantity_logits = self.jobs[2](hidden).float().masked_fill(~quantity_support, -1e9)
        quantity = self.choose(
            quantity_logits, None if supplied is None else supplied[:, :, 0, 2], sample, temperature
        )
        hidden = hidden + self.job_embeddings[2](quantity)
        zero = torch.zeros_like(target)
        unit_actions = torch.stack((target, op, quantity, zero), -1)
        unit_actions = torch.stack((unit_actions, torch.zeros_like(unit_actions)), 2)
        fixed = torch.zeros_like(target_logits).masked_fill(~self.singleton, -1e9)
        unit_logits = torch.stack((target_logits, op_logits, quantity_logits, fixed), -2)
        unit_logits = torch.stack((unit_logits, fixed[:, :, None].expand(-1, -1, 4, -1)), 2)
        pooled = (hidden * present[..., None]).sum(1) / present.sum(1).clamp_min(1)[:, None]
        market_actions, market_logits = self._market(
            encoded[:, 0] + pooled,
            actions,
            sample,
            temperature,
        )
        return (
            torch.cat((unit_actions.flatten(1), market_actions), -1),
            torch.cat((unit_logits.flatten(1, 3), market_logits), 1),
        )

    def _market(
        self,
        hidden: Tensor,
        actions: Tensor | None,
        sample: bool,
        temperature: float | Tensor,
    ) -> tuple[Tensor, Tensor]:
        layout = self.layout
        vocabulary = layout.vocabulary_size
        support = self.vocabulary[layout.work_factors :].reshape(
            layout.observation.markets, 2, vocabulary
        )
        supplied = (
            None
            if actions is None
            else actions[:, layout.work_factors :].reshape(-1, layout.observation.markets, 2)
        )
        active = torch.ones(len(hidden), dtype=torch.bool, device=hidden.device)
        choices, logits = [], []
        for slot in range(layout.observation.markets):
            state = hidden + self.order_positions[slot]
            selected: list[Tensor] = []
            scores: list[Tensor] = []
            for field, (head, embedding) in enumerate(
                zip(
                    self.market_heads,
                    self.market_embeddings,
                    strict=True,
                )
            ):
                valid = active
                if field:
                    valid = valid & (selected[0] >= 2) & (selected[0] <= 20)
                allowed = torch.where(valid[..., None], support[slot, field], self.singleton)
                field_logits = head(state).float()
                if field and layout.network.operation_quantity_bias:
                    field_logits = field_logits + self.quantity_offsets[selected[0]]
                field_logits = field_logits.masked_fill(~allowed, -1e9)
                choice = self.choose(
                    field_logits,
                    None if supplied is None else supplied[:, slot, field],
                    sample,
                    temperature,
                )
                selected.append(choice)
                scores.append(field_logits)
                state = state + embedding(choice)
            active = active & (selected[0] != 0)
            hidden = hidden + self.condition(state)
            choices.append(torch.stack(selected, -1))
            logits.append(torch.stack(scores, -2))
        return torch.stack(choices, 1).flatten(1), torch.stack(logits, 1).flatten(1, 2)

    def field_weights(
        self,
        actions: Tensor,
        steps: Tensor,
        observations: Tensor | None = None,
    ) -> Tensor:
        """Credit only sampled present-unit choices and active market requests."""
        if observations is None:
            raise ValueError("grounded action credit requires the decision observation")
        layout = self.layout
        _, current, support = self._units(observations)
        first = actions[:, : layout.work_factors].reshape(-1, layout.observation.units, 2, 4)[
            :, :, 0
        ]
        present = support[..., 0]
        local = present & (first[..., 0] == current + 1)
        op = first[..., 1]
        quantity = local & (((op >= 5) & (op < 17)) | ((op >= 18) & (op < 30)))
        weights = torch.stack((present, local, quantity, torch.zeros_like(present)), -1)
        weights = torch.stack((weights, torch.zeros_like(weights)), 2).flatten(1).float()
        market = super().field_weights(actions, steps)[:, layout.work_factors :]
        return torch.cat((weights, market), -1)
