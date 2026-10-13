"""Bounded conditional decoding: investment, assets, upkeep, harvest, priority, sales."""

import torch
from torch import Tensor, nn

from kagg_revue.policy.contracts import ContractLayout
from kagg_revue.policy.spatial.encoder import EntityEncoder
from kagg_revue.policy.spatial.model import Policy, log_probabilities, sample_categorical


def _head(width: int, outputs: int) -> nn.Sequential:
    final = nn.Linear(2 * width, outputs)
    result = nn.Sequential(nn.LayerNorm(width), nn.Linear(width, 2 * width), nn.GELU(), final)
    nn.init.zeros_(final.weight)
    nn.init.zeros_(final.bias)
    return result


class EntityPolicy(Policy):
    """One shared entity encoding, followed by six fully device-resident stages."""

    control_offsets: Tensor

    def __init__(self, layout: ContractLayout) -> None:
        """Initialize residual heads at zero so the demonstrated prior remains intact."""
        nn.Module.__init__(self)
        self.layout = layout
        width = layout.observation.width
        self.encoder = EntityEncoder(layout, width, layout.network.depth)
        self.controls = _head(width, 5 * 32)
        self.assets = _head(width, 32)
        self.upkeep = _head(width, 32)
        self.harvest = _head(width, 32)
        self.priority = _head(width, 32)
        self.market = _head(width, 2 * 32)
        self.control_embedding = nn.Embedding(5 * 32, width)
        self.asset_embedding = nn.Embedding(10, width)
        self.upkeep_embedding = nn.Embedding(4, width)
        self.harvest_embedding = nn.Embedding(4, width)
        self.priority_embedding = nn.Embedding(4, width)
        self.condition = nn.Sequential(nn.Linear(width, width), nn.GELU(), nn.Linear(width, width))
        self.prior = nn.Parameter(torch.zeros(layout.decisions, layout.factors, 32))
        self.register_buffer(
            "vocabulary", torch.arange(32)[None] < torch.tensor(layout.cardinalities)[:, None]
        )
        self.register_buffer("control_offsets", 32 * torch.arange(5))

    def _decode(
        self,
        observations: Tensor,
        steps: Tensor,
        actions: Tensor | None,
        sample: bool,
        temperature: float | Tensor = 1.0,
    ) -> tuple[Tensor, Tensor]:
        encoded = self.encoder(observations)
        cells = self.layout.cells
        prior = self.prior[steps]
        cell_prior = prior[:, : 4 * cells].reshape(-1, cells, 4, 32)
        mask = self.vocabulary[: 4 * cells].reshape(cells, 4, 32)

        def choose(logits: Tensor, teacher: Tensor | None) -> Tensor:
            if teacher is not None:
                return teacher
            if sample:
                return sample_categorical(logits, temperature)
            return logits.argmax(-1)

        control_logits = self.controls(encoded[:, 0]).reshape(-1, 5, 32)
        control_logits = (control_logits.float() + prior[:, 4 * cells : 4 * cells + 5]).masked_fill(
            ~self.vocabulary[4 * cells : 4 * cells + 5], -1e9
        )
        controls = choose(
            control_logits, None if actions is None else actions[:, 4 * cells : 4 * cells + 5]
        )
        control_code = self.condition(
            self.control_embedding(controls + self.control_offsets).mean(1)
        )
        local = encoded[:, 1 : 1 + cells] + control_code[:, None]
        teacher_cells = None if actions is None else actions[:, : 4 * cells].reshape(-1, cells, 4)
        selected, logits = [], []
        embeddings = (
            self.asset_embedding,
            self.upkeep_embedding,
            self.harvest_embedding,
            self.priority_embedding,
        )
        for field, (head, embedding) in enumerate(
            zip((self.assets, self.upkeep, self.harvest, self.priority), embeddings, strict=True)
        ):
            scores = (head(local).float() + cell_prior[:, :, field]).masked_fill(
                ~mask[:, field], -1e9
            )
            choice = choose(scores, None if teacher_cells is None else teacher_cells[:, :, field])
            selected.append(choice)
            logits.append(scores)
            local = local + embedding(choice)
        product_start = 1 + 2 * cells + 2 * self.layout.observation.units
        market_input = encoded[:, product_start : product_start + 9] + local.mean(1)[:, None]
        market_logits = self.market(market_input).reshape(-1, 18, 32)
        market_logits = (market_logits.float() + prior[:, 4 * cells + 5 :]).masked_fill(
            ~self.vocabulary[4 * cells + 5 :], -1e9
        )
        market = choose(market_logits, None if actions is None else actions[:, 4 * cells + 5 :])
        chosen = torch.cat((torch.stack(selected, -1).flatten(1), controls, market), -1)
        scores = torch.cat((torch.stack(logits, 2).flatten(1, 2), control_logits, market_logits), 1)
        return chosen, scores

    def forward(self, observations: Tensor, steps: Tensor, actions: Tensor | None = None) -> Tensor:
        """Replay the exact conditional distribution using sampled/teacher predecessor fields."""
        return self._decode(observations, steps, actions, False)[1]

    def act(
        self,
        observations: Tensor,
        steps: Tensor,
        *,
        sample: bool,
        temperature: float | Tensor = 1.0,
    ) -> tuple[Tensor, Tensor]:
        """Sample all conditional stages in one graph, with no host handshake between fields."""
        actions, logits = self._decode(observations, steps, None, sample, temperature)
        return actions, log_probabilities(logits, actions, temperature)
