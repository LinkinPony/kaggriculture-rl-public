"""Authenticated numeric portfolio extracted from the frozen artifact."""

from __future__ import annotations

import hashlib
from importlib import resources
from io import BytesIO

import numpy as np
from numpy.typing import NDArray

from kagg_revue.opponents.boatlee.provenance import (
    PORTFOLIO_ASSET_SHA256,
    PORTFOLIO_SEMANTIC_SHA256,
    SOURCE_SHA256,
)

TAPE_NAMES = (
    "moon_current_10c4s_3q",
    "moon_current_8c6s_3q",
    "moon_current_6c8s_3q",
    "moon_current_6c12s_4q_first_yarn",
    "moon_current_6c12s_4q_second_yarn",
    "moon_legacy_10c4s_3q",
    "moon_legacy_8c6s_3q",
    "moon_legacy_6c8s_3q",
    "moon_legacy_6c12s_4q_first_yarn",
    "moon_legacy_6c12s_4q_second_yarn",
    "moon_r5_market",
    "moon_md_market",
    "mutoy",
    "munib",
)
TAPE_TURNS = 720


def _scalar_text(value: NDArray[np.str_], name: str) -> str:
    if value.shape != ():
        raise ValueError(f"Boatlee portfolio {name} must be a scalar")
    return str(value.item())


def load_portfolio() -> tuple[
    NDArray[np.int64],
    NDArray[np.int64],
    NDArray[np.int64],
    NDArray[np.int64],
]:
    """Load and validate the offline-encoded immutable action tapes."""
    asset = resources.files(__package__).joinpath("portfolio.npz").read_bytes()
    if hashlib.sha256(asset).hexdigest() != PORTFOLIO_ASSET_SHA256:
        raise RuntimeError("optimized Boatlee portfolio asset hash mismatch")
    with np.load(BytesIO(asset), allow_pickle=False) as archive:
        tokens = np.asarray(archive["tokens"], dtype=np.int64)
        quantities = np.asarray(archive["quantities"], dtype=np.int64)
        decision_counts = np.asarray(archive["decision_counts"], dtype=np.int64)
        unit_counts = np.asarray(archive["unit_counts"], dtype=np.int64)
        names = tuple(str(value) for value in archive["tape_names"].tolist())
        source_sha256 = _scalar_text(archive["source_sha256"], "source hash")
        semantic_sha256 = _scalar_text(archive["semantic_sha256"], "semantic hash")
    expected_prefix = (len(TAPE_NAMES), TAPE_TURNS)
    if (
        tokens.ndim != 3
        or tokens.shape[:2] != expected_prefix
        or quantities.shape != tokens.shape
        or decision_counts.shape != expected_prefix
        or unit_counts.shape != expected_prefix
    ):
        raise ValueError("optimized Boatlee portfolio arrays have invalid shapes")
    if names != TAPE_NAMES:
        raise ValueError("optimized Boatlee tape ordering differs from the frozen artifact")
    if source_sha256 != SOURCE_SHA256:
        raise ValueError("optimized Boatlee portfolio source identity mismatch")
    if semantic_sha256 != PORTFOLIO_SEMANTIC_SHA256:
        raise ValueError("optimized Boatlee portfolio semantic identity mismatch")
    return tokens, quantities, decision_counts, unit_counts


__all__ = ["TAPE_NAMES", "TAPE_TURNS", "load_portfolio"]
