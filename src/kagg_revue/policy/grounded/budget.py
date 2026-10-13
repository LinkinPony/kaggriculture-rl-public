"""Causal quote-based budget features for the autoregressive market decoder.

This is an exposure estimate, not a simulator or an affordability mask. Opponent
orders, price impact and changes to the shed during the unit phase are unknown
to this ledger. Observed quotes and the actor's own requested prefix are its only
inputs; oversize requests retain full action support.
"""

from typing import cast

import torch
from torch import Tensor, nn

from kagg_revue.policy.contracts import ContractLayout


def _scale(value: Tensor, divisor: float) -> Tensor:
    return value.sign() * torch.log1p(value.abs() / divisor)


class MarketBudget(nn.Module):
    """Expose bank, quoted prefix exposure, inventory and candidate funding gaps."""

    quantities: Tensor
    inventory: Tensor
    hire_ratios: Tensor

    def __init__(self, layout: ContractLayout) -> None:
        """Bind feature offsets and quantity literals to the existing native ABI."""
        super().__init__()
        base = layout.observation
        self.global_start = base.board_features + base.units * base.unit_features
        self.product_start = (
            self.global_start + base.global_features + base.units * base.unit_features
        )
        self.product_width = base.product_features
        self.context = nn.Sequential(
            nn.Linear(70, base.width), nn.GELU(), nn.Linear(base.width, base.width)
        )
        self.candidates = nn.Sequential(nn.Linear(4, 16), nn.GELU(), nn.Linear(16, 1))
        self.register_buffer("quantities", torch.tensor(base.quantities, dtype=torch.float32))
        # Product inventory deltas per requested unit. Seeds, hire and land have
        # separate storage; animals occupy shed item slots 9..11.
        inventory = torch.zeros(23, 12)
        inventory[2:11, :9] = -torch.eye(9)
        inventory[16, 0] = inventory[17, 8] = 1
        inventory[18:21, 9:] = torch.eye(3)
        self.register_buffer("inventory", inventory)
        fibonacci = [1, 1]
        for _ in range(64):
            fibonacci.append(sum(fibonacci[-2:]))
        ratios = [b / a for a, b in zip(fibonacci, fibonacci[1:], strict=False)]
        self.register_buffer("hire_ratios", torch.tensor(ratios, dtype=torch.float32))

    def start(self, observations: Tensor) -> tuple[Tensor, Tensor]:
        """Recover current public quotes and own bank in float32, including under AMP."""
        global_state = observations[:, self.global_start : self.global_start + 82].float()
        products = observations[:, self.product_start : self.product_start + 9 * self.product_width]
        products = products.float().reshape(-1, 9, self.product_width)
        prices = products[..., 1] * products[..., 6] * 250
        fixed = products[..., 22] * 500
        cash = global_state[:, 5:6] * 100000
        stock = torch.expm1(global_state[:, 28:40] * 4.605170185988092).round()
        hire = torch.expm1(global_state[:, 81:82] * 10)
        land = 1000 * 2 ** (global_state[:, 69:73].sum(-1, keepdim=True) - 1)
        costs = torch.cat(
            (
                torch.zeros_like(cash).expand(-1, 2),
                -prices,
                fixed[:, :5],
                prices[:, ::8],
                fixed[:, 5:8],
                hire,
                land,
            ),
            -1,
        )
        # Columns: initial cash, quote-based remaining cash, gross buy exposure,
        # own shed estimates, product flow, requested hires today, requested land.
        ledger = torch.cat(
            (
                cash,
                cash,
                torch.zeros_like(cash),
                stock,
                torch.zeros_like(prices),
                global_state[:, 79:80] * 8,
                global_state[:, 69:73].sum(-1, keepdim=True) - 1,
            ),
            -1,
        )
        return ledger, costs

    def features(self, ledger: Tensor, costs: Tensor) -> Tensor:
        """Expose an explicit small-integer affordability estimate for each operation."""
        bank = ledger[:, 1:2]
        affordable = (bank.clamp_min(0) / costs.clamp_min(1)).floor().clamp_max(128)
        affordable = torch.where(costs > 0, affordable, torch.zeros_like(affordable))
        values = torch.cat(
            (
                _scale(ledger[:, :3], 1000),
                _scale(costs, 100),
                _scale(ledger[:, 3:15], 10),
                affordable / 32,
                _scale(ledger[:, 15:24], 100),
            ),
            -1,
        )
        return cast(Tensor, self.context(values))

    def quantity_scores(self, ledger: Tensor, costs: Tensor, operation: Tensor) -> Tensor:
        """Learn candidate funding-gap effects with the same BC/PPO likelihood loss."""
        cost = costs.gather(1, operation[:, None])
        quote = cost * self.quantities[None]
        bank = ledger[:, 1:2]
        short = (cost > 0) & (quote > bank)
        stock = (ledger[:, 3:15] * (-self.inventory[operation]).clamp_min(0)).sum(-1, keepdim=True)
        shortage = torch.where(cost < 0, (self.quantities[None] - stock).clamp_min(0), 0)
        values = torch.stack(
            (_scale(quote, 1000), _scale(bank - quote, 1000), short.float(), _scale(shortage, 10)),
            -1,
        )
        return cast(Tensor, self.candidates(values)).squeeze(-1).float()

    def advance(
        self, ledger: Tensor, costs: Tensor, operation: Tensor, quantity: Tensor, active: Tensor
    ) -> tuple[Tensor, Tensor]:
        """Accumulate requested exposure; never read later labels or opponent actions."""
        amount = torch.where(operation >= 21, 1, self.quantities[quantity])
        amount = amount * (active & (operation >= 2)).float()
        cost = costs.gather(1, operation[:, None])
        requested = cost * amount[:, None]
        available = (ledger[:, 3:15] * (-self.inventory[operation]).clamp_min(0)).sum(-1)
        affordable = (ledger[:, 1].clamp_min(0) / cost[:, 0].clamp_min(1)).floor()
        filled = torch.minimum(amount, torch.where(cost[:, 0] < 0, available, affordable))
        filled = filled.clamp_min(0)
        delta = self.inventory[operation] * filled[:, None]
        quoted = cost * filled[:, None]
        hire_done = (operation == 21) & active & (filled >= 1)
        land_done = (operation == 22) & active & (filled >= 1)
        hires = ledger[:, 24:25] + hire_done[:, None]
        land = ledger[:, 25:26] + land_done[:, None]
        updated = torch.cat(
            (
                ledger[:, :1],
                ledger[:, 1:2] - quoted,
                ledger[:, 2:3] + requested.clamp_min(0),
                ledger[:, 3:15] + delta,
                ledger[:, 15:24] + delta[:, :9],
                hires,
                land,
            ),
            -1,
        )
        # Consecutive hire prices follow Fibonacci increments (the first two are
        # equal). A bounded table is sufficient for at most 32 units + 10 orders.
        index = ledger[:, 24:25].round().long().clamp(0, len(self.hire_ratios) - 1)
        ratio = self.hire_ratios[index]
        new_hire = costs[:, 21:22] * torch.where(hire_done[:, None], ratio, 1)
        new_land = costs[:, 22:23] * torch.where(land_done[:, None], 2, 1)
        return updated, torch.cat((costs[:, :21], new_hire, new_land), -1)
