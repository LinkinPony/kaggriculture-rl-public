"""Check native teacher likelihood gradients across stateless and recurrent BC."""

import copy
from pathlib import Path

import numpy as np
import pytest
import torch

from kagg_revue.datasets.sequences.loading import SequenceDataset
from kagg_revue.learning.adapter import runtime_settings
from kagg_revue.learning.config import Experiment
from kagg_revue.learning.initialization import random_policy
from kagg_revue.learning.pretraining.config import GroupedLoss, LossWeights
from kagg_revue.learning.pretraining.flat import FlatSequenceOptimizer
from kagg_revue.learning.sequences.pretraining import SequenceOptimizer
from kagg_revue.native.batches import create_selfplay_batch
from kagg_revue.policy.contracts import ContractLayout
from kagg_revue.policy.memory.policy import MemoryPolicy


@pytest.mark.parametrize("grouped", [False, True])
@pytest.mark.parametrize("memory", [False, True])
def test_bc_matches_full_abi_with_masked_rows_and_chunk_accumulation(
    grouped: bool,
    memory: bool,
) -> None:
    """Compare a real native batch against the complete logits and every parameter gradient."""
    torch.set_num_threads(1)
    config = Experiment(
        output_dir=Path("outputs/learning/flat-test"),
        device="cpu",
        architecture="grounded-v2",
        agronomy=True,
        market_budget=True,
        decision_interval=1,
        width=32,
        depth=1,
        critic_width=32,
        critic_depth=1,
        unit_limit=4,
        quantity_max=4,
        compile=False,
        precision="fp32",
        microbatch_rows=2,
        memory_turns=4 if memory else 0,
        memory_width=32,
        memory_layers=1,
        memory_tokens=2,
        sequence_chunk_turns=3,
        environment={
            "boardSize": 4,
            "episodeSteps": 17,
            "turnsPerDay": 4,
            "maxMarketOrdersPerTurn": 3,
        },
    )
    settings = runtime_settings(config)
    actor = random_policy(ContractLayout.resolve(settings), 741, config.exploration)
    reference = copy.deepcopy(actor)
    array = np.empty((8, actor.layout.observation.features), np.float16)
    create_selfplay_batch(settings, list(range(4))).observe_selfplay_into(array)
    inputs = torch.from_numpy(array)
    turns = torch.arange(4).repeat_interleave(2)
    with torch.no_grad():
        if isinstance(actor, MemoryPolicy):
            actions, _, _ = actor.sequence(
                inputs.view(4, 2, -1),
                torch.arange(4),
                actor.memory.temporal.empty(2, torch.device("cpu")),
                sample=True,
            )
            actions = actions.flatten(0, 1)
        else:
            actions, _ = actor.act(inputs, turns, sample=True)
    # Exercise quantities, STOP, BUY_LAND and ignored suffixes in the same batch.
    actions[:, actor.layout.work_factors :] = torch.tensor([11, 2, 22, 0, 0, 0])
    eligible = torch.tensor([True, False, True, True, False, True, True, True])

    class Batch(SequenceDataset):
        def __init__(self) -> None:
            pass

        def episode(
            self, index: int, device: torch.device, rank: int, world: int
        ) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
            return inputs.view(4, 2, -1), actions.view(4, 2, -1), eligible.view(4, 2)

    if isinstance(reference, MemoryPolicy):
        state = reference.memory.temporal.empty(2, torch.device("cpu"))
        chunks = []
        for start, stop in ((0, 3), (3, 4)):
            _, logits, state = reference.sequence(
                inputs.view(4, 2, -1)[start:stop],
                torch.arange(start, stop),
                state,
                actions.view(4, 2, -1)[start:stop],
            )
            chunks.append(logits)
        logits = torch.cat(chunks).flatten(0, 1)
    else:
        logits = reference(inputs, turns, actions)
    likelihood = logits.log_softmax(-1).gather(-1, actions[..., None]).squeeze(-1)
    fields = reference.field_weights(actions, turns, inputs)
    loss = GroupedLoss(weights=LossWeights(market_operation=3.0)) if grouped else None
    if loss is None:
        rows = -(likelihood * fields).sum(-1) / fields.sum(-1).clamp_min(1)
        expected = (rows * eligible).sum() / eligible.sum()
    else:
        active = fields * eligible[:, None]
        selections = [list(range(i, actor.layout.work_factors, 8)) for i in range(3)]
        selections += [
            list(range(actor.layout.work_factors + i, actor.layout.factors, 2)) for i in range(2)
        ]
        expected = torch.stack(
            [
                -(likelihood[:, selected] * active[:, selected]).sum()
                / active[:, selected].sum().clamp_min(1)
                * weight
                / 7
                for selected, weight in zip(selections, (1, 1, 1, 3, 1), strict=True)
            ]
        ).sum()
    expected.backward()  # type: ignore[no-untyped-call]
    torch.nn.utils.clip_grad_norm_(reference.parameters(), 1.0)
    optimizer_class = SequenceOptimizer if memory else FlatSequenceOptimizer
    optimizer = optimizer_class(actor, settings, 0.0001, loss=loss)
    result = optimizer.shard(Batch(), 0, 8, (741, 0, 0))
    assert result["rows"] == int(eligible.sum())
    assert result["optimizer_steps"] == 1
    assert abs(result["loss_sum"] / result["rows"] - float(expected.detach())) < 1e-6
    assert len(result["field_totals"]) == 15
    for left, right in zip(actor.parameters(), reference.parameters(), strict=True):
        assert (left.grad is None) == (right.grad is None)
        if left.grad is not None:
            torch.testing.assert_close(left.grad, right.grad, atol=3e-6, rtol=3e-5)
