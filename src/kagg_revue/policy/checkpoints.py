"""Structured policy checkpoint serialization, separate from legacy provenance."""

from pathlib import Path
from typing import Any

import torch

from kagg_revue.artifacts.serialization import save
from kagg_revue.learning.settings import RuntimeSettings
from kagg_revue.native.features import Layout
from kagg_revue.policy.contracts import ContractLayout, NetworkShape, layout_record
from kagg_revue.policy.spatial.model import Policy


def save_policy(path: Path, policy: Policy, settings: RuntimeSettings, **state: Any) -> None:
    """Atomically save learned priors and feedback weights together."""
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "layout": layout_record(policy.layout),
        "model": policy.state_dict(),
        "settings": settings.model_dump(mode="json"),
        **state,
    }
    save(payload, path)


def load_policy(path: Path, device: torch.device) -> tuple[Policy, dict[str, Any]]:
    """Load an explicitly selected local training artifact."""
    payload = torch.load(path, map_location=device, weights_only=False)
    stored = payload["layout"]
    layout = ContractLayout(
        Layout(**stored["observation"]),
        stored["board_size"],
        stored["interval"],
        NetworkShape(**stored.get("network", {})),
        stored.get("late_start", 0),
        stored.get("late_interval", 0),
    )
    policy = Policy.from_layout(layout).to(device)
    policy.load_state_dict(payload["model"])
    return policy, payload
