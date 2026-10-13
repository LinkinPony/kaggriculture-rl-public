"""Authenticated compact portfolio extracted from the frozen v39 artifact."""

from __future__ import annotations

import hashlib
from functools import cache
from importlib import resources
from io import BytesIO
from typing import Any

import numpy as np
from numpy.typing import NDArray

from kagg_revue.opponents.kaito.v39.provenance import PORTFOLIO_ASSET_SHA256

_ASSET_NAME = "portfolio.npz"
_REQUIRED_ARRAYS = frozenset(
    {
        "schema_version",
        "tokens",
        "quantities",
        "decision_counts",
        "unit_counts",
        "parts_layout",
        "parts_numeric",
        "parts_actor_lengths",
        "parts_unlocks",
        "parts_shop_counts",
        "parts_seats",
        "nested_indices",
        "nested_margins",
        "fallback_indices",
        "fallback_margins",
        "stage1_indices",
        "stage1_margins",
        "stage2_indices",
        "stage2_margins",
    }
)


@cache
def portfolio_arrays() -> dict[str, NDArray[Any]]:
    """Load and authenticate the process-shared v39 portfolio arrays."""
    payload = resources.files(__package__).joinpath(_ASSET_NAME).read_bytes()
    if hashlib.sha256(payload).hexdigest() != PORTFOLIO_ASSET_SHA256:
        raise RuntimeError("optimized v39 portfolio asset hash mismatch")
    with np.load(BytesIO(payload), allow_pickle=False) as archive:
        if set(archive.files) != _REQUIRED_ARRAYS:
            raise ValueError("optimized v39 portfolio asset schema differs")
        arrays = {name: np.ascontiguousarray(archive[name]) for name in archive.files}
    if arrays["schema_version"].tolist() != [1]:
        raise ValueError("unsupported optimized v39 portfolio schema")
    for value in arrays.values():
        value.setflags(write=False)
    return arrays


__all__ = ["portfolio_arrays"]

