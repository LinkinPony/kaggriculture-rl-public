"""Static semantic columns of the typed actor's fixed-width native action ABI."""

import torch
from torch import Tensor

from kagg_revue.policy.contracts import ContractLayout


def semantic_fields(layout: ContractLayout) -> Tensor:
    """Retain all three unit choices and every market choice, omitting fixed padding."""
    if layout.network.architecture != "grounded-v2" or layout.capacity != 1:
        raise ValueError("semantic field compression requires single-turn typed actions")
    units = (8 * torch.arange(layout.observation.units)[:, None] + torch.arange(3)).flatten()
    return torch.cat((units, torch.arange(layout.work_factors, layout.factors)))
