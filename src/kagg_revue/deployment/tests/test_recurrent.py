"""Recurrent exports preserve sampling, cache eviction and fresh-game independence."""

import subprocess
import sys
from pathlib import Path

import pytest
import torch

from kagg_revue.deployment.actor import freeze
from kagg_revue.deployment.recurrent import empty_inputs
from kagg_revue.learning.adapter import runtime_settings
from kagg_revue.learning.config import Experiment
from kagg_revue.policy.contracts import ContractLayout
from kagg_revue.policy.memory.policy import MemoryPolicy, RecurrentExecution
from kagg_revue.policy.spatial.model import Policy


@pytest.mark.parametrize("temperature", [0.0, 1.0])
def test_recurrent_actor_in_fresh_process(tmp_path: Path, temperature: float) -> None:
    """Compare actions and every cache tensor past eviction and a new episode boundary."""
    config = Experiment(
        output_dir=Path("outputs/learning/recurrent-export-test"),
        architecture="grounded-v2",
        width=16,
        depth=1,
        heads=4,
        critic_width=16,
        critic_depth=1,
        unit_limit=2,
        decision_interval=1,
        agronomy=True,
        memory_turns=4,
        memory_width=16,
        memory_layers=2,
        sequence_chunk_turns=2,
    )
    policy = Policy.from_layout(ContractLayout.resolve(runtime_settings(config))).eval()
    assert isinstance(policy, MemoryPolicy)
    threads = torch.get_num_threads()
    try:
        torch.set_num_threads(1)
        freeze(policy, tmp_path / "actor.pt", temperature=temperature)
        observations = torch.zeros((1, policy.layout.observation.features), dtype=torch.float16)
        records = []
        for length in (9, 3):
            runtime = RecurrentExecution(policy, 1, torch.device("cpu"))
            for turn in range(length):
                steps = torch.tensor([turn])
                torch.manual_seed(17 + turn)
                with torch.inference_mode():
                    actions = runtime.act(observations, steps, sample=temperature > 0)[0]
                records.append(
                    {
                        "turn": turn,
                        "actions": actions,
                        "state": (
                            torch.stack(runtime.state.keys).clone(),
                            torch.stack(runtime.state.values).clone(),
                            runtime.state.turns.clone(),
                        ),
                    }
                )
        torch.save(
            {"observations": observations, "empty": empty_inputs(policy), "records": records},
            tmp_path / "reference.pt",
        )
    finally:
        torch.set_num_threads(threads)
    script = """
import sys, torch
torch.set_num_threads(1)
model = torch.jit.load(sys.argv[1], map_location='cpu').eval()
reference = torch.load(sys.argv[2], weights_only=True)
assert not any(name.startswith('kagg_revue') for name in sys.modules)
with torch.inference_mode():
    for row in reference['records']:
        turn = row['turn']
        if turn == 0:
            state = tuple(value.clone() for value in reference['empty'])
        torch.manual_seed(17 + turn)
        before = torch.get_rng_state()
        actions, *following = model(reference['observations'], torch.tensor([turn]), *state)
        assert torch.equal(actions, row['actions'])
        for actual, expected in zip(following, row['state'], strict=True):
            torch.testing.assert_close(actual, expected, rtol=1e-5, atol=1e-6)
        state = tuple(following)
        if float(sys.argv[3]) == 0:
            assert torch.equal(before, torch.get_rng_state())
print('recurrent export passed')
"""
    output = subprocess.check_output(
        [
            sys.executable,
            "-I",
            "-c",
            script,
            str(tmp_path / "actor.pt"),
            str(tmp_path / "reference.pt"),
            str(temperature),
        ],
        text=True,
    )
    assert output.strip() == "recurrent export passed"
