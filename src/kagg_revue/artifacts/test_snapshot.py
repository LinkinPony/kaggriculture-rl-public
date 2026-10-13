"""Live optimizer mutation must not change a submitted checkpoint."""

from typing import Any

import pytest
import torch

from kagg_revue.artifacts.snapshot import capture


@pytest.mark.parametrize("device_name", ["cpu", "cuda:0"])
def test_snapshot_isolates_mutation_and_preserves_views(device_name: str) -> None:
    """Exercise ordered CUDA copies, CPU copies, aliases and non-tensor metadata."""
    if device_name.startswith("cuda") and not torch.cuda.is_available():
        pytest.skip("CUDA is unavailable")
    device = torch.device(device_name)
    original = torch.arange(250000, device=device, dtype=torch.float32)
    payload: dict[str, Any] = {
        "model": original,
        "view": original[7::13],
        "pfsp": {"games": [4, 8]},
    }
    saved = capture(payload, device)
    original.add_(100)
    payload["pfsp"]["games"].append(16)
    result = saved.wait()
    assert torch.equal(result["model"], torch.arange(250000, dtype=torch.float32))
    assert torch.equal(result["view"], result["model"][7::13])
    assert result["pfsp"] == {"games": [4, 8]}
    result["model"][7] = -25
    assert result["view"][0] == -25
