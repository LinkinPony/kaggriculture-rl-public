"""Lossless bounded-integer decoder for conditional EXACT quantities."""

from __future__ import annotations

from dataclasses import dataclass
from typing import cast

import torch
from torch import Tensor, nn

from kagg_revue.policy.cuda.categorical import sample_masked_factor
from kagg_revue.policy.programs.distributions import (
    choose_masked,
    evaluate_masked,
)
from kagg_revue.policy.programs.schema import ProgramArchitecture


@dataclass(frozen=True)
class ExactQuantityOutput:
    """Decoded integer and per-bit probability statistics."""

    quantity: Tensor
    factor_log_probability: Tensor
    factor_entropy: Tensor
    factors: Tensor


class ExactQuantityDecoder(nn.Module):
    """Generate every integer in ``[1, qmax]`` with legal binary prefixes."""

    def __init__(self, architecture: ProgramArchitecture) -> None:
        """Create an autoregressive bit state bound to the artifact width."""
        super().__init__()
        width = architecture.model_width
        self.maximum_bits = architecture.exact_quantity_bits
        self.maximum_quantity = (1 << self.maximum_bits) - 1
        self.register_buffer(
            "_bit_thresholds",
            torch.tensor(
                [1 << bit for bit in range(self.maximum_bits)],
                dtype=torch.long,
            ),
            persistent=False,
        )
        self.qmax = nn.Linear(1, width, bias=False)
        self.position = nn.Embedding(self.maximum_bits, width)
        self.bit = nn.Embedding(2, width)
        self.cell = nn.GRUCell(width, width)
        self.head = nn.Sequential(
            nn.LayerNorm(width),
            nn.Linear(width, architecture.feedforward_width),
            nn.SiLU(),
            nn.Linear(architecture.feedforward_width, 2),
        )

    def _bit_counts(self, quantity_max: Tensor) -> Tensor:
        maximum_index = (quantity_max - 1).clamp_min(0)
        thresholds = cast(Tensor, self._bit_thresholds)
        if thresholds.device != quantity_max.device:
            raise ValueError("conditional-program exact decoder is on another device")
        return (maximum_index[:, None] >= thresholds[None]).sum(dim=1)

    def _initial(self, state: Tensor, quantity_max: Tensor) -> Tensor:
        scaled = torch.log1p(quantity_max.float()).clamp_max(32.0) / 16.0
        return cast(Tensor, state + self.qmax(scaled[:, None]))

    @staticmethod
    def _mask(
        prefix: Tensor,
        maximum_index: Tensor,
        remaining: Tensor,
        active: Tensor,
    ) -> Tensor:
        scale = torch.bitwise_left_shift(torch.ones_like(remaining), remaining)
        lower_zero = (prefix * 2) * scale
        lower_one = (prefix * 2 + 1) * scale
        legal = torch.stack((lower_zero <= maximum_index, lower_one <= maximum_index), dim=1)
        canonical = torch.zeros_like(legal)
        canonical[:, 0] = True
        return torch.where(active[:, None], legal, canonical)

    def rollout(
        self,
        state: Tensor,
        quantity_max: Tensor,
        active: Tensor,
        *,
        sample: bool,
        generator: torch.Generator | None,
        compute_entropy: bool,
        validate: bool,
        static_execution: bool = False,
        uniforms: Tensor | None = None,
    ) -> ExactQuantityOutput:
        """Sample a bounded integer without constructing a ``Qmax`` head."""
        self._validate(quantity_max, active, validate=validate)
        if not static_execution and not bool(active.any()):
            shape = (active.shape[0], self.maximum_bits)
            return ExactQuantityOutput(
                quantity=torch.ones_like(quantity_max),
                factor_log_probability=torch.zeros(shape, dtype=torch.float32, device=state.device),
                factor_entropy=torch.zeros(shape, dtype=torch.float32, device=state.device),
                factors=torch.zeros(shape, dtype=torch.bool, device=state.device),
            )
        hidden = self._initial(state, quantity_max)
        prefix = torch.zeros_like(quantity_max)
        maximum_index = (quantity_max - 1).clamp_min(0)
        bit_counts = self._bit_counts(quantity_max)
        logs: list[Tensor] = []
        entropies: list[Tensor] = []
        factors: list[Tensor] = []
        if uniforms is not None and uniforms.shape != (
            self.maximum_bits,
            active.shape[0],
        ):
            raise ValueError("conditional-program exact uniforms have the wrong shape")
        for depth in range(self.maximum_bits):
            bit_active = active & (depth < bit_counts)
            remaining = (bit_counts - depth - 1).clamp_min(0)
            mask = self._mask(prefix, maximum_index, remaining, bit_active)
            position = self.position.weight[depth][None]
            logits = self.head(hidden + position)
            if uniforms is None:
                bit, log_probability, entropy, factor = choose_masked(
                    logits,
                    mask,
                    bit_active,
                    sample=sample,
                    generator=generator,
                    compute_entropy=compute_entropy,
                )
            else:
                bit, log_probability, factor = sample_masked_factor(
                    logits,
                    mask,
                    bit_active,
                    uniforms[depth],
                )
                entropy = torch.zeros_like(log_probability)
            prefix = torch.where(bit_active, prefix * 2 + bit, prefix)
            updated = cast(Tensor, self.cell(self.bit(bit), hidden))
            hidden = torch.where(bit_active[:, None], updated, hidden)
            logs.append(log_probability)
            entropies.append(entropy)
            factors.append(factor)
        quantity = torch.where(active, prefix + 1, torch.ones_like(prefix))
        return ExactQuantityOutput(
            quantity=quantity,
            factor_log_probability=torch.stack(logs, dim=1),
            factor_entropy=torch.stack(entropies, dim=1),
            factors=torch.stack(factors, dim=1),
        )

    def evaluate(
        self,
        state: Tensor,
        quantity_max: Tensor,
        quantity: Tensor,
        active: Tensor,
        *,
        validate: bool,
    ) -> ExactQuantityOutput:
        """Reconstruct exact per-bit likelihoods from one stored integer."""
        self._validate(quantity_max, active, validate=validate)
        if validate and bool(torch.any(active & ((quantity < 1) | (quantity > quantity_max)))):
            raise ValueError("conditional-program EXACT quantity exceeds Qmax")
        hidden = self._initial(state, quantity_max)
        bit_counts = self._bit_counts(quantity_max)
        encoded = (quantity - 1).clamp_min(0)
        depths = torch.arange(self.maximum_bits, device=state.device)
        remaining = (bit_counts[:, None] - depths[None] - 1).clamp_min(0)
        bit_active = active[:, None] & (depths[None] < bit_counts[:, None])
        bits = torch.bitwise_and(
            torch.bitwise_right_shift(encoded[:, None], remaining),
            1,
        )
        recurrent, _last = torch._VF.gru(
            self.bit(bits),
            hidden[None],
            [
                self.cell.weight_ih,
                self.cell.weight_hh,
                self.cell.bias_ih,
                self.cell.bias_hh,
            ],
            True,
            1,
            0.0,
            self.training,
            False,
            True,
        )
        hidden_before = torch.cat((hidden[:, None], recurrent[:, :-1]), dim=1)
        logits = self.head(hidden_before + self.position.weight[None])
        prefix = torch.bitwise_right_shift(encoded[:, None], remaining + 1)
        scale = torch.bitwise_left_shift(torch.ones_like(remaining), remaining)
        maximum_index = (quantity_max - 1).clamp_min(0)[:, None]
        legal = torch.stack(
            (
                (prefix * 2) * scale <= maximum_index,
                (prefix * 2 + 1) * scale <= maximum_index,
            ),
            dim=-1,
        )
        canonical = torch.zeros_like(legal)
        canonical[..., 0] = True
        masks = torch.where(bit_active[..., None], legal, canonical)
        flat_logs, flat_entropies, flat_factors = evaluate_masked(
            logits.flatten(0, 1),
            masks.flatten(0, 1),
            bits.flatten(),
            bit_active.flatten(),
            validate=validate,
        )
        shape = (state.shape[0], self.maximum_bits)
        decoded = torch.where(active, quantity, torch.ones_like(quantity))
        return ExactQuantityOutput(
            quantity=decoded,
            factor_log_probability=flat_logs.view(shape),
            factor_entropy=flat_entropies.view(shape),
            factors=flat_factors.view(shape),
        )

    def _validate(self, quantity_max: Tensor, active: Tensor, *, validate: bool) -> None:
        if quantity_max.ndim != 1 or active.shape != quantity_max.shape:
            raise ValueError("conditional-program EXACT inputs must be aligned vectors")
        if quantity_max.is_floating_point() or active.is_floating_point():
            raise ValueError("conditional-program EXACT bounds and activity are discrete")
        if validate and bool(
            torch.any(active & ((quantity_max < 2) | (quantity_max > self.maximum_quantity)))
        ):
            raise ValueError("conditional-program EXACT Qmax exceeds its artifact")


__all__ = ["ExactQuantityDecoder", "ExactQuantityOutput"]
