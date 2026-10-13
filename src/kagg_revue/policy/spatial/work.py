"""Conditional ordered work and market plans over the existing entity backbone."""

from dataclasses import replace

import torch
from torch import Tensor, nn

from kagg_revue.policy.contracts import ContractLayout
from kagg_revue.policy.spatial.encoder import EntityEncoder
from kagg_revue.policy.spatial.entity import _head
from kagg_revue.policy.spatial.model import Policy, log_probabilities, sample_categorical


class WorkPolicy(Policy):
    """Generate bounded job queues and ordered market requests in one device call."""

    vocabulary: Tensor
    singleton: Tensor
    spans: Tensor
    market_times: Tensor
    prior_scale: Tensor

    def __init__(self, layout: ContractLayout) -> None:
        """Retain entity capacity and condition each job on its preceding choices."""
        nn.Module.__init__(self)
        self.layout = layout
        width = layout.observation.width
        vocabulary = layout.vocabulary_size
        self.encoder = EntityEncoder(layout, width, layout.network.depth)
        self.jobs = nn.ModuleList(_head(width, vocabulary) for _ in range(4))
        self.job_embeddings = nn.ModuleList(nn.Embedding(vocabulary, width) for _ in range(4))
        self.market_heads = nn.ModuleList(_head(width, vocabulary) for _ in range(2))
        self.market_embeddings = nn.ModuleList(nn.Embedding(vocabulary, width) for _ in range(2))
        self.condition = nn.Sequential(nn.Linear(width, width), nn.GELU(), nn.Linear(width, width))
        self.job_positions = nn.Parameter(torch.zeros(layout.capacity + 1, width))
        self.market_positions = nn.Parameter(torch.zeros(layout.capacity, width))
        self.order_positions = nn.Parameter(torch.zeros(layout.observation.markets, width))
        if layout.network.time_prior:
            self.prior = nn.Parameter(torch.zeros(layout.decisions, layout.factors, vocabulary))
            self.register_buffer(
                "prior_scale", torch.tensor(layout.network.prior_scale), persistent=False
            )
        support = torch.arange(vocabulary)[None] < torch.tensor(layout.cardinalities)[:, None]
        work_support = support[: layout.work_factors].reshape(
            layout.observation.units, layout.capacity + 1, 4, vocabulary
        )
        work_support[:, :, 1, 1:5] = False
        self.register_buffer("vocabulary", support)
        self.register_buffer("singleton", torch.arange(vocabulary) == 0)
        self.register_buffer("spans", torch.tensor(layout.spans))
        self.register_buffer("market_times", torch.arange(layout.capacity))

    def _decode(
        self,
        observations: Tensor,
        steps: Tensor,
        actions: Tensor | None,
        sample: bool,
        temperature: float | Tensor = 1.0,
    ) -> tuple[Tensor, Tensor]:
        layout = self.layout
        batch = len(observations)
        units, slots, vocabulary = (
            layout.observation.units,
            layout.capacity + 1,
            layout.vocabulary_size,
        )
        encoded = self.encoder(observations)
        prior = self.prior[steps] * self.prior_scale if layout.network.time_prior else None
        job_prior = (
            None
            if prior is None
            else prior[:, : layout.work_factors].reshape(batch, units, slots, 4, vocabulary)
        )
        job_support = self.vocabulary[: layout.work_factors].reshape(units, slots, 4, vocabulary)
        teacher_jobs = (
            None
            if actions is None
            else actions[:, : layout.work_factors].reshape(batch, units, slots, 4)
        )
        unit_start = 1 + 2 * layout.cells
        hidden = encoded[:, unit_start : unit_start + units]
        base = layout.observation
        # The native presence field is exactly zero or one. Use it directly:
        # comparing again lets Inductor alias a saved mask to an unaligned slice
        # of SDPA's concatenated bool mask during backward.
        present = observations[
            :, base.board_features : base.board_features + units * base.unit_features
        ].reshape(batch, units, base.unit_features)[..., :1]
        gate = present.to(hidden.dtype)
        hidden = gate * hidden + (1 - gate) * (encoded[:, :1] + self.encoder.unit_position)
        active = torch.ones((batch, units), dtype=torch.bool, device=observations.device)
        selected_jobs, job_logits = [], []

        for slot in range(slots):
            state = hidden + self.job_positions[slot]
            selected: list[Tensor] = []
            logits: list[Tensor] = []
            for field, (head, embedding) in enumerate(
                zip(self.jobs, self.job_embeddings, strict=True)
            ):
                valid = active
                if field:
                    valid = valid & (selected[0] > 0)
                if field == 2:
                    op = selected[1]
                    valid = valid & (((op >= 5) & (op < 17)) | ((op >= 18) & (op < 30)))
                if field == 3:
                    valid = valid & (selected[1] > 0)
                support = torch.where(valid[..., None], job_support[:, slot, field], self.singleton)
                scores = head(state).float()
                if job_prior is not None:
                    scores = scores + job_prior[:, :, slot, field]
                scores = scores.masked_fill(~support, -1e9)
                choice = self.choose(
                    scores,
                    None if teacher_jobs is None else teacher_jobs[:, :, slot, field],
                    sample,
                    temperature,
                )
                selected.append(choice)
                logits.append(scores)
                state = state + embedding(choice)
            active = active & (selected[0] > 0)
            hidden = hidden + self.condition(state)
            selected_jobs.append(torch.stack(selected, -1))
            job_logits.append(torch.stack(logits, -2))

        market_prior = (
            None
            if prior is None
            else prior[:, layout.work_factors :].reshape(
                batch, layout.capacity, layout.observation.markets, 2, vocabulary
            )
        )
        market_support = self.vocabulary[layout.work_factors :].reshape(
            layout.capacity, layout.observation.markets, 2, vocabulary
        )
        teacher_market = (
            None
            if actions is None
            else actions[:, layout.work_factors :].reshape(
                batch, layout.capacity, layout.observation.markets, 2
            )
        )
        hidden = encoded[:, :1] + hidden.mean(1)[:, None] + self.market_positions
        active = self.market_times[None] < self.spans[steps, None]
        selected_orders, market_logits = [], []
        for slot in range(layout.observation.markets):
            state = hidden + self.order_positions[slot]
            selected, logits = [], []
            for field, (head, embedding) in enumerate(
                zip(self.market_heads, self.market_embeddings, strict=True)
            ):
                valid = active
                if field:
                    valid = valid & (selected[0] >= 2) & (selected[0] <= 20)
                support = torch.where(
                    valid[..., None], market_support[:, slot, field], self.singleton
                )
                scores = head(state).float()
                if market_prior is not None:
                    scores = scores + market_prior[:, :, slot, field]
                scores = scores.masked_fill(~support, -1e9)
                choice = self.choose(
                    scores,
                    None if teacher_market is None else teacher_market[:, :, slot, field],
                    sample,
                    temperature,
                )
                selected.append(choice)
                logits.append(scores)
                state = state + embedding(choice)
            active = active & (selected[0] != 0)
            hidden = hidden + self.condition(state)
            selected_orders.append(torch.stack(selected, -1))
            market_logits.append(torch.stack(logits, -2))
        chosen = torch.cat(
            (torch.stack(selected_jobs, 2).flatten(1), torch.stack(selected_orders, 2).flatten(1)),
            -1,
        )
        scores = torch.cat(
            (torch.stack(job_logits, 2).flatten(1, 3), torch.stack(market_logits, 2).flatten(1, 3)),
            1,
        )
        return chosen, scores

    def choose(
        self, scores: Tensor, teacher: Tensor | None, sample: bool, temperature: float | Tensor
    ) -> Tensor:
        """Select one conditional field before conditioning the remaining program."""
        if teacher is not None:
            return teacher
        return sample_categorical(scores, temperature) if sample else scores.argmax(-1)

    def forward(self, observations: Tensor, steps: Tensor, actions: Tensor | None = None) -> Tensor:
        """Reconstruct every conditional distribution using the actual preceding choices."""
        return self._decode(observations, steps, actions, False)[1]

    def remove_prior(self) -> None:
        """Delete a zero-weight table without replacing any neural parameter objects."""
        if not self.layout.network.time_prior:
            return
        if float(self.prior_scale) != 0:
            raise ValueError("the table coefficient must reach zero before removal")
        del self.prior
        del self.prior_scale
        self.layout = replace(
            self.layout, network=replace(self.layout.network, time_prior=False, prior_scale=0)
        )

    def act(
        self,
        observations: Tensor,
        steps: Tensor,
        *,
        sample: bool,
        temperature: float | Tensor = 1.0,
    ) -> tuple[Tensor, Tensor]:
        """Sample the complete native program without a host handshake between jobs."""
        actions, logits = self._decode(observations, steps, None, sample, temperature)
        return actions, log_probabilities(logits, actions, temperature)

    def field_weights(
        self,
        actions: Tensor,
        steps: Tensor,
        observations: Tensor | None = None,
    ) -> Tensor:
        """Exclude fields after STOP and quantities unused by the selected operation."""
        layout = self.layout
        jobs = actions[:, : layout.work_factors].reshape(
            -1, layout.observation.units, layout.capacity + 1, 4
        )
        target, op = jobs[..., 0], jobs[..., 1]
        stop = target == 0
        active = stop.cumsum(-1) - stop.long() == 0
        quantity = ((op >= 5) & (op < 17)) | ((op >= 18) & (op < 30))
        fields = torch.stack(
            (active, active & ~stop, active & ~stop & quantity, active & ~stop & (op > 0)), -1
        )
        market = actions[:, layout.work_factors :].reshape(
            -1, layout.capacity, layout.observation.markets, 2
        )
        op = market[..., 0]
        stop = op == 0
        active = (stop.cumsum(-1) - stop.long() == 0) & (
            self.market_times[None] < self.spans[steps, None]
        )[..., None]
        orders = torch.stack((active, active & (op >= 2) & (op <= 20)), -1)
        return torch.cat((fields.flatten(1), orders.flatten(1)), -1).float()
