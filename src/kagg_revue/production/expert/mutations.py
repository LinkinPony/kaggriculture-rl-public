"""Reproducible policy perturbations, fixed throughout each complete game."""

import torch
from torch import nn


class ParameterSearch:
    """Perturb neural parameters around a frozen center without changing its architecture."""

    def __init__(self, parameters: dict[str, nn.Parameter]) -> None:
        """Snapshot exactly the parameter set selected by the experiment."""
        if not parameters:
            raise ValueError("parameter search requires a nonempty parameter set")
        self.parameters = parameters
        self.center = {name: value.detach().clone() for name, value in parameters.items()}
        self.scales = {
            name: value.float().square().mean().sqrt() for name, value in self.center.items()
        }

    @torch.no_grad()
    def propose(self, seed: int, scale: float) -> None:
        """Use antithetic perturbations of the same direction for opposite signed scales."""
        device = next(iter(self.parameters.values())).device
        generator = torch.Generator(device=device).manual_seed(seed)
        for name, parameter in self.parameters.items():
            noise = torch.randn(parameter.shape, generator=generator, device=device)
            parameter.copy_(self.center[name] + scale * self.scales[name] * noise)

    @torch.no_grad()
    def recenter(self) -> None:
        """Make an accepted neural policy the center of subsequent proposals."""
        for name, parameter in self.parameters.items():
            self.center[name].copy_(parameter)
            self.scales[name].copy_(parameter.float().square().mean().sqrt())


def readout_parameters(policy: nn.Module) -> dict[str, nn.Parameter]:
    """Search all final work and market projections, preserving the shared perception stack."""
    names = {
        f"{family}.{index}.3.{field}"
        for family, count in (("jobs", 4), ("market_heads", 2))
        for index in range(count)
        for field in ("weight", "bias")
    }
    result = {name: value for name, value in policy.named_parameters() if name in names}
    if result.keys() != names:
        raise ValueError("the policy does not expose the expected work readout projections")
    return result
