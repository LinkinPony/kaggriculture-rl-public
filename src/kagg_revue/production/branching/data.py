"""Compact root-to-candidate tapes with direct terminal outcomes and immutable identities."""

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import torch
from torch import Tensor


@dataclass
class BranchTape:
    """Store each root observation once; candidate programs contain their conditional prefixes."""

    observations: Tensor
    actions: Tensor
    previous: Tensor
    steps: Tensor
    outcomes: Tensor
    cash: Tensor
    seeds: Tensor
    seats: Tensor
    scripts: Tensor
    timing: dict[str, float]
    prefix_cash: np.ndarray[Any, Any] | None = None

    @classmethod
    def allocate(
        cls, roots: int, candidates: int, features: int, factors: int, device: torch.device
    ) -> "BranchTape":
        """Preallocate the whole update, including both continuation outcomes."""
        return cls(
            torch.empty((roots, features), device=device, dtype=torch.float16),
            torch.empty((roots, candidates, factors), device=device, dtype=torch.int16),
            torch.empty((roots, candidates), device=device),
            torch.empty(roots, device=device, dtype=torch.long),
            torch.empty((roots, 2, candidates), device=device, dtype=torch.int8),
            torch.empty((roots, 2, candidates, 2), device=device, dtype=torch.float64),
            torch.empty(roots, device=device, dtype=torch.long),
            torch.empty(roots, device=device, dtype=torch.int8),
            torch.empty(roots, device=device, dtype=torch.bool),
            {},
        )

    def save(self, path: Path) -> None:
        """Write compact arrays; source, opponents and continuation identities live in manifests."""
        path.parent.mkdir(parents=True, exist_ok=True)
        np.savez_compressed(
            path,
            **{
                name: getattr(self, name).cpu().numpy()
                for name in (
                    "observations",
                    "actions",
                    "previous",
                    "steps",
                    "outcomes",
                    "cash",
                    "seeds",
                    "seats",
                    "scripts",
                )
            },
        )
