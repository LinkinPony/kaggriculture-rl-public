"""Force a few model-proposed choices, then conditionally complete whole work programs."""

import torch
from torch import Tensor

from kagg_revue.policy.contracts import ContractLayout
from kagg_revue.policy.spatial.work import WorkPolicy


class ProposalPolicy(WorkPolicy):
    """Share all neural semantics; external controls are research-only decoder interventions."""

    forced: Tensor

    def __init__(self, layout: ContractLayout, rows: int) -> None:
        """Precompute the shared decoder's field order for one bounded actor shape."""
        super().__init__(layout)
        self.register_buffer(
            "forced", torch.full((rows, layout.factors), -1, dtype=torch.long), persistent=False
        )
        self.columns = [
            torch.arange(layout.observation.units) * (layout.capacity + 1) * 4 + slot * 4 + field
            for slot in range(layout.capacity + 1)
            for field in range(4)
        ] + [
            layout.work_factors
            + torch.arange(layout.capacity) * layout.observation.markets * 2
            + slot * 2
            + field
            for slot in range(layout.observation.markets)
            for field in range(2)
        ]
        for index, columns in enumerate(self.columns):
            self.register_buffer(f"columns_{index}", columns, persistent=False)
        self.call = 0

    def act(
        self,
        observations: Tensor,
        steps: Tensor,
        *,
        sample: bool,
        temperature: float | Tensor = 1.0,
    ) -> tuple[Tensor, Tensor]:
        """Generate complete queues and market requests under the actual chosen prefixes."""
        self.call = 0
        return super().act(observations, steps, sample=sample, temperature=temperature)

    def choose(
        self, scores: Tensor, teacher: Tensor | None, sample: bool, temperature: float | Tensor
    ) -> Tensor:
        """Apply an intervention only when it remains valid after earlier conditional choices."""
        if teacher is not None:
            return teacher
        columns = getattr(self, f"columns_{self.call}")
        self.call += 1
        desired = self.forced[:, columns]
        supported = scores.gather(-1, desired.clamp_min(0)[..., None]).squeeze(-1) > -1e8
        return torch.where((desired >= 0) & supported, desired, scores.argmax(-1))


def proposal_controls(
    policy: WorkPolicy,
    observations: Tensor,
    steps: Tensor,
    actions: Tensor,
    logits: Tensor,
    candidates: int,
    pivots: int,
    alternatives: int,
) -> Tensor:
    """Sample active fields and alternative ranks, escaping a sharp categorical prior."""
    rows, fields = actions.shape
    device, layout = actions.device, policy.layout
    eligible = policy.field_weights(actions, steps)
    base = layout.observation
    present = observations[
        :, base.board_features : base.board_features + base.units * base.unit_features
    ]
    present = present.reshape(rows, base.units, base.unit_features)[..., 0]
    eligible[:, : layout.work_factors] *= present.repeat_interleave((layout.capacity + 1) * 4, -1)
    count = min(alternatives + 1, logits.shape[-1])
    values, tokens = logits.topk(count, dim=-1)
    support = (values > -1e8) & (tokens != actions[..., None])
    eligible *= support.any(-1)
    # Balance grammatical families, without prescribing any business action or date.
    work, market = eligible[:, : layout.work_factors], eligible[:, layout.work_factors :]
    work /= work.sum(-1, keepdim=True).clamp_min(1)
    market /= market.sum(-1, keepdim=True).clamp_min(1)
    weights = eligible[:, None].expand(-1, candidates - 1, -1).reshape(-1, fields)
    chosen = torch.multinomial(weights, pivots, replacement=False)
    roots = torch.arange(rows, device=device).repeat_interleave(candidates - 1)
    selected_tokens = tokens[roots[:, None], chosen]
    selected_support = support[roots[:, None], chosen]
    random = torch.rand_like(selected_tokens, dtype=torch.float32).masked_fill(
        ~selected_support, -1
    )
    alternate = selected_tokens.gather(-1, random.argmax(-1, keepdim=True)).squeeze(-1)
    valid = selected_support.any(-1) & (eligible[roots[:, None], chosen] > 0)
    forced = torch.full((rows, candidates, fields), -1, dtype=torch.long, device=device)
    proposals = forced[:, 1:].reshape(-1, fields).clone()
    proposals.scatter_(1, chosen, torch.where(valid, alternate, -1))
    forced[:, 1:] = proposals.reshape(rows, candidates - 1, fields)
    return forced
