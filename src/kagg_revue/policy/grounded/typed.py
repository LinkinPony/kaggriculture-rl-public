"""Typed conditional actions with a spatial pointer and no unused job outputs."""

import torch
from torch import Tensor, nn
from torch.nn import functional as F

from kagg_revue.policy.contracts import ContractLayout
from kagg_revue.policy.grounded.budget import MarketBudget
from kagg_revue.policy.grounded.encoder import ContextEncoder
from kagg_revue.policy.grounded.fields import semantic_fields
from kagg_revue.policy.grounded.joint import UnitContext
from kagg_revue.policy.grounded.model import GroundedPolicy
from kagg_revue.policy.grounded.normalization import LayerNorm


def _head(width: int, choices: int) -> nn.Sequential:
    return nn.Sequential(LayerNorm(width), nn.Linear(width, choices))


class TypedGroundedPolicy(GroundedPolicy):
    """Reuse grounded execution and credit with a deeper, fully used parameter set."""

    semantic_fields: Tensor

    def __init__(self, layout: ContractLayout) -> None:
        """Allocate only sampled semantic readouts while preserving the native ABI."""
        nn.Module.__init__(self)
        if layout.capacity != 1 or layout.network.time_prior:
            raise ValueError("typed grounded actions require one turn and no time table")
        self.layout = layout
        width, vocabulary = layout.observation.width, layout.vocabulary_size
        quantities = len(layout.observation.quantities)
        self.encoder = ContextEncoder(layout, width, layout.network.depth)
        self.query = nn.Linear(width, width)
        self.key = nn.Linear(width, width)
        self.pass_embedding = nn.Parameter(torch.zeros(width))
        self.jobs = nn.ModuleList((_head(width, 1), _head(width, 44), _head(width, quantities)))
        self.operation_embedding = nn.Embedding(44, width)
        self.quantity_embedding = nn.Embedding(quantities, width)
        self.market_heads = nn.ModuleList((_head(width, 23), _head(width, quantities)))
        self.market_embeddings = nn.ModuleList(
            (nn.Embedding(23, width), nn.Embedding(quantities, width))
        )
        self.condition = nn.Sequential(
            LayerNorm(width), nn.Linear(width, 2 * width), nn.GELU(), nn.Linear(2 * width, width)
        )
        self.pool = nn.Linear(width, 1)
        self.order_positions = nn.Parameter(torch.zeros(layout.observation.markets, width))
        self.quantity_offsets = nn.Parameter(torch.zeros(23, quantities))
        self.unit_quantity_offsets = nn.Parameter(torch.zeros(44, quantities))
        support = torch.arange(vocabulary)[None] < torch.tensor(layout.cardinalities)[:, None]
        self.register_buffer("vocabulary", support)
        self.register_buffer("singleton", torch.arange(vocabulary) == 0)
        self.register_buffer("spans", torch.tensor(layout.spans))
        self.register_buffer("market_times", torch.arange(layout.capacity))
        self.register_buffer("cell_x", torch.arange(layout.cells) % layout.board_size)
        self.register_buffer("cell_y", torch.arange(layout.cells) // layout.board_size)
        self.budget = MarketBudget(layout) if layout.network.market_budget else None
        network = layout.network
        self.joint = UnitContext(width, network.heads) if network.joint_units else None
        self.register_buffer("semantic_fields", semantic_fields(layout), persistent=False)

    def compact_logits(self, observations: Tensor, actions: Tensor) -> Tensor:
        """Evaluate every possible non-padding choice without materializing fixed columns."""
        return self.decode_encoded(
            self.encoder(observations), observations, actions, False, compact=True
        )[1]

    def _pad(self, logits: Tensor) -> Tensor:
        return F.pad(
            logits.float(), (0, self.layout.vocabulary_size - logits.shape[-1]), value=-1e9
        )

    def _decode(
        self,
        observations: Tensor,
        steps: Tensor,
        actions: Tensor | None,
        sample: bool,
        temperature: float | Tensor = 1.0,
    ) -> tuple[Tensor, Tensor]:
        return self.decode_encoded(
            self.encoder(observations), observations, actions, sample, temperature
        )

    def decode_encoded(
        self,
        encoded: Tensor,
        observations: Tensor,
        actions: Tensor | None,
        sample: bool,
        temperature: float | Tensor = 1.0,
        *,
        compact: bool = False,
    ) -> tuple[Tensor, Tensor]:
        """Decode the same grounded action language from an explicit scene encoding."""
        layout = self.layout
        n, units, vocabulary = len(observations), layout.observation.units, layout.vocabulary_size
        positions, current, legal = self._units(observations)
        present = legal[..., 0]
        unit_start = 1 + 2 * layout.cells
        hidden = encoded[:, unit_start : unit_start + units] * present[..., None]
        tiles = encoded[:, 1 : 1 + layout.cells]
        distance = (positions[..., :1] - self.cell_x).abs() + (
            positions[..., 1:] - self.cell_y
        ).abs()
        allowed = present[..., None] & (
            (distance == 1) | ((distance == 0) & legal[..., 5:].any(-1, keepdim=True))
        )
        allowed = F.pad(allowed, (1, vocabulary - layout.cells - 1), value=False)
        allowed[..., 0] = True
        supplied = (
            None
            if actions is None
            else actions[:, : layout.work_factors].reshape(n, units, 2, 4)[:, :, 0, :3]
        )
        scene = (tiles, self.key(tiles))
        if self.joint is None:
            decoded = self._unit_fields(
                hidden, scene, allowed, current, legal, supplied, sample, temperature
            )
        elif supplied is not None:
            earlier = torch.ones(units, units, dtype=torch.bool, device=hidden.device).tril(-1)
            context = self.joint(
                hidden, self._claims(hidden, tiles, supplied), earlier & present[:, None]
            )
            decoded = self._unit_fields(
                hidden + context, scene, allowed, current, legal, supplied, sample, temperature
            )
        else:
            decoded = self._joint_sample(
                hidden, scene, allowed, current, legal, present, sample, temperature
            )
        hidden, choices, scores = decoded
        target, op, quantity = choices.unbind(-1)
        target_logits, op_logits, quantity_logits = scores.unbind(-2)
        zero = torch.zeros_like(target)
        unit_actions = torch.stack((target, op, quantity, zero), -1)
        unit_actions = torch.stack((unit_actions, torch.zeros_like(unit_actions)), 2)
        if compact:
            unit_logits = scores.flatten(1, 2)
        else:
            fixed = torch.zeros_like(target_logits).masked_fill(~self.singleton, -1e9)
            unit_logits = torch.stack((target_logits, op_logits, quantity_logits, fixed), -2)
            unit_logits = torch.stack((unit_logits, fixed[:, :, None].expand(-1, -1, 4, -1)), 2)
            unit_logits = unit_logits.flatten(1, 3)
        pooling = self.pool(hidden).float().squeeze(-1).masked_fill(~present, -1e9).softmax(-1)
        pooled = (hidden * pooling[..., None]).sum(1)
        market_actions, market_logits = self._market_typed(
            encoded[:, 0] + pooled, actions, sample, temperature, observations
        )
        return (
            torch.cat((unit_actions.flatten(1), market_actions), -1),
            torch.cat((unit_logits, market_logits), 1),
        )

    def _destination(self, tiles: Tensor, target: Tensor) -> Tensor:
        tile = tiles.gather(1, (target - 1).clamp_min(0)[..., None].expand(-1, -1, tiles.shape[-1]))
        return torch.where((target > 0)[..., None], tile, self.pass_embedding)

    def _unit_fields(
        self,
        hidden: Tensor,
        scene: tuple[Tensor, Tensor],
        allowed: Tensor,
        current: Tensor,
        legal: Tensor,
        supplied: Tensor | None,
        sample: bool,
        temperature: float | Tensor,
    ) -> tuple[Tensor, Tensor, Tensor]:
        """Choose target, operation and quantity for any slice of unit slots."""
        tiles, keys = scene
        vocabulary = self.layout.vocabulary_size
        pointer = (self.query(hidden) @ keys.transpose(1, 2)) * hidden.shape[-1] ** -0.5
        target_logits = self._pad(torch.cat((self.jobs[0](hidden), pointer), -1)).masked_fill(
            ~allowed, -1e9
        )
        target = self.choose(
            target_logits, None if supplied is None else supplied[..., 0], sample, temperature
        )
        hidden = hidden + self._destination(tiles, target)
        hidden = hidden + self.condition(hidden)
        local = (target > 0) & (target == current + 1)
        op_support = F.pad(legal, (0, vocabulary - 44))
        op_support[..., :5] = False
        op_support = torch.where(local[..., None], op_support, self.singleton)
        op_logits = self._pad(self.jobs[1](hidden)).masked_fill(~op_support, -1e9)
        op = self.choose(
            op_logits, None if supplied is None else supplied[..., 1], sample, temperature
        )
        hidden = hidden + self.operation_embedding(op)
        hidden = hidden + self.condition(hidden)
        has_quantity = ((op >= 5) & (op < 17)) | ((op >= 18) & (op < 30))
        quantity_support = torch.arange(vocabulary, device=hidden.device) < len(
            self.layout.observation.quantities
        )
        quantity_support = torch.where(has_quantity[..., None], quantity_support, self.singleton)
        quantity_logits = self._pad(
            self.jobs[2](hidden) + self.unit_quantity_offsets[op]
        ).masked_fill(~quantity_support, -1e9)
        quantity = self.choose(
            quantity_logits, None if supplied is None else supplied[..., 2], sample, temperature
        )
        hidden = hidden + self.quantity_embedding(quantity)
        return (
            hidden,
            torch.stack((target, op, quantity), -1),
            torch.stack((target_logits, op_logits, quantity_logits), -2),
        )

    def _claims(self, hidden: Tensor, tiles: Tensor, choices: Tensor) -> Tensor:
        assert self.joint is not None
        target, op, quantity = choices.unbind(-1)
        return self.joint.claims(
            hidden
            + self._destination(tiles, target)
            + self.operation_embedding(op)
            + self.quantity_embedding(quantity)
        )

    def _joint_sample(
        self,
        hidden: Tensor,
        scene: tuple[Tensor, Tensor],
        allowed: Tensor,
        current: Tensor,
        legal: Tensor,
        present: Tensor,
        sample: bool,
        temperature: float | Tensor,
    ) -> tuple[Tensor, Tensor, Tensor]:
        """Decode unit slots in order; teacher forcing computes the same factors in parallel."""
        assert self.joint is not None
        claims = hidden[:, :0]
        decoded: list[tuple[Tensor, Tensor, Tensor]] = []
        for unit in range(hidden.shape[1]):
            base = hidden[:, unit : unit + 1]
            context = self.joint(base, claims, present[:, None, :unit])
            parts = slice(unit, unit + 1)
            result = self._unit_fields(
                base + context,
                scene,
                allowed[:, parts],
                current[:, parts],
                legal[:, parts],
                None,
                sample,
                temperature,
            )
            claim = self._claims(base, scene[0], result[1])
            claims = torch.cat((claims.to(claim.dtype), claim), 1)
            decoded.append(result)
        final, choices, scores = zip(*decoded, strict=True)
        return torch.cat(final, 1), torch.cat(choices, 1), torch.cat(scores, 1)

    def _market_typed(
        self,
        hidden: Tensor,
        actions: Tensor | None,
        sample: bool,
        temperature: float | Tensor,
        observations: Tensor,
    ) -> tuple[Tensor, Tensor]:
        layout = self.layout
        support = self.vocabulary[layout.work_factors :].reshape(
            layout.observation.markets, 2, layout.vocabulary_size
        )
        supplied = (
            None
            if actions is None
            else actions[:, layout.work_factors :].reshape(-1, layout.observation.markets, 2)
        )
        active = torch.ones(len(hidden), dtype=torch.bool, device=hidden.device)
        choices, logits = [], []
        budget_state = self.budget.start(observations) if self.budget is not None else None
        for slot in range(layout.observation.markets):
            state = hidden + self.order_positions[slot]
            if self.budget is not None and budget_state is not None:
                ledger, costs = budget_state[:2]
                state = state + self.budget.features(ledger, costs)
            selected: list[Tensor] = []
            scores: list[Tensor] = []
            for field, (head, embedding) in enumerate(
                zip(self.market_heads, self.market_embeddings, strict=True)
            ):
                valid = active if field == 0 else active & (selected[0] >= 2) & (selected[0] <= 20)
                allowed = torch.where(valid[..., None], support[slot, field], self.singleton)
                values = head(state).float()
                if field:
                    values = values + self.quantity_offsets[selected[0]]
                    if self.budget is not None and budget_state is not None:
                        values = values + self.budget.quantity_scores(ledger, costs, selected[0])
                field_logits = self._pad(values).masked_fill(~allowed, -1e9)
                choice = self.choose(
                    field_logits,
                    None if supplied is None else supplied[:, slot, field],
                    sample,
                    temperature,
                )
                selected.append(choice)
                scores.append(field_logits)
                state = state + embedding(choice)
                if field == 0:
                    state = state + self.condition(state)
            if self.budget is not None and budget_state is not None:
                ledger, costs = self.budget.advance(ledger, costs, selected[0], selected[1], active)
                budget_state = (ledger, costs)
            active = active & (selected[0] != 0)
            hidden = hidden + self.condition(state)
            choices.append(torch.stack(selected, -1))
            logits.append(torch.stack(scores, -2))
        return torch.stack(choices, 1).flatten(1), torch.stack(logits, 1).flatten(1, 2)
