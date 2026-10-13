"""Exported actors must load without registering training-only custom operators."""

import json
import subprocess
import sys
from pathlib import Path

import pytest
import torch

from kagg_revue.deployment.actor import freeze
from kagg_revue.learning.adapter import runtime_settings
from kagg_revue.learning.config import Experiment
from kagg_revue.policy.contracts import ContractLayout
from kagg_revue.policy.grounded.normalization import LayerNorm
from kagg_revue.policy.spatial.model import Policy


@pytest.mark.parametrize("temperature", [0.0, 1.0])
def test_actor_loads_in_fresh_torch_process_and_preserves_sampling(
    tmp_path: Path, temperature: float
) -> None:
    """Match eager draws while preserving the caller's weights and normalization modules."""
    config = Experiment(
        output_dir=Path("outputs/learning/export-test"),
        architecture="grounded-v2",
        width=16,
        depth=1,
        heads=4,
        critic_width=16,
        critic_depth=1,
        unit_limit=2,
        decision_interval=1,
    )
    policy = Policy.from_layout(ContractLayout.resolve(runtime_settings(config))).eval()
    original = {name: value.clone() for name, value in policy.state_dict().items()}
    norms = {
        name: module for name, module in policy.named_modules() if isinstance(module, LayerNorm)
    }
    assert norms
    actor = tmp_path / "actor.pt"
    threads = torch.get_num_threads()
    try:
        torch.set_num_threads(1)
        freeze(policy, actor, temperature=temperature)
        features = policy.layout.observation.features
        observations = torch.zeros((1, features), dtype=torch.float16)
        steps = torch.zeros(1, dtype=torch.long)
        expected = []
        for seed in (11, 12):
            torch.manual_seed(seed)
            with torch.inference_mode():
                expected.append(policy.act(observations, steps, sample=temperature > 0)[0].tolist())
        if temperature == 0:
            assert expected[0] == expected[1]
    finally:
        torch.set_num_threads(threads)
    assert all(torch.equal(value, policy.state_dict()[name]) for name, value in original.items())
    assert all(policy.get_submodule(name) is module for name, module in norms.items())
    script = """
import json, sys, torch
torch.set_num_threads(1)
model = torch.jit.load(sys.argv[1], map_location='cpu').eval()
assert not any(name.startswith('kagg_revue') for name in sys.modules)
observations = torch.zeros((1, int(sys.argv[2])), dtype=torch.float16)
steps = torch.zeros(1, dtype=torch.long)
results = []
for seed in (11, 12):
    torch.manual_seed(seed)
    before = torch.get_rng_state()
    with torch.inference_mode():
        results.append(model(observations, steps).tolist())
    if float(sys.argv[3]) == 0:
        assert torch.equal(before, torch.get_rng_state())
print(json.dumps(results))
"""
    output = subprocess.check_output(
        [sys.executable, "-I", "-c", script, str(actor), str(features), str(temperature)], text=True
    )
    assert json.loads(output) == expected
