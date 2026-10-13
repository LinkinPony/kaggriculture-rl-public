from types import SimpleNamespace

import torch

from kagg_revue.bc.tasks.model import scratch_initialization_identity
from kagg_revue.bc.tasks.train import _Totals
from kagg_revue.policy.model import ActorArchitecture
from kagg_revue.policy.tasks.grammar import FACTORIZED_TASK_FACTOR_COUNT


class _Backend:
    """Synthetic encoder identity for scratch-checkpoint metadata."""

    def actor_encoder_spec(self) -> dict[str, object]:
        """Return the only field needed by the identity builder."""
        return {"version": "synthetic-encoder"}


def _architecture() -> ActorArchitecture:
    return ActorArchitecture(
        board_shape=(2, 1, 2, 2),
        unit_shape=(2, 1, 2),
        global_features=3,
        model_width=8,
        entity_width=4,
        attention_heads=1,
        feedforward_width=12,
        latent_tokens=2,
        scene_layers=0,
        temporal_layers=1,
        action_layers=1,
        max_history=3,
        max_decisions=2,
        unit_action_tokens=2,
        market_action_tokens=2,
        maximum_quantity=4,
        derived_fact_version=None,
        turn_fact_features=0,
        prefix_fact_features=0,
        candidate_fact_features=0,
        fact_dropout=0.0,
    )


def test_scratch_identity_carries_runtime_encoding_contract() -> None:
    action_keys = ("u0", "u1", "m0", "m1")

    identity = scratch_initialization_identity(
        _Backend(),
        _architecture(),
        action_keys,
        17,
        torch.nn.Linear(2, 2),
    )

    assert identity["actor_encoder_version"] == "synthetic-encoder"
    assert identity["derived_fact_version"] is None
    assert identity["action_keys"] == list(action_keys)
    assert identity["weight_artifact_imported"] is False


def test_task_bc_totals_cover_every_factorized_head() -> None:
    factors = torch.zeros((2, FACTORIZED_TASK_FACTOR_COUNT), dtype=torch.bool)
    factors[0] = True
    losses = torch.arange(
        1,
        2 * FACTORIZED_TASK_FACTOR_COUNT + 1,
        dtype=torch.float32,
    ).reshape(2, FACTORIZED_TASK_FACTOR_COUNT)
    output = SimpleNamespace(
        masks=SimpleNamespace(factors=factors),
        factor_log_probability=-losses,
        entropy=torch.tensor([2.0, 3.0]),
    )
    totals = _Totals()

    totals.update(output)
    totals.update(output)
    summary = totals.summary(1.0)

    assert summary["active_decisions"] == 2
    assert summary["stored_decisions"] == 4
    assert summary["forced_decisions"] == 2
    assert summary["factor_counts"] == [2] * FACTORIZED_TASK_FACTOR_COUNT
    assert summary["factor_nll"] == [
        float(value) for value in range(1, FACTORIZED_TASK_FACTOR_COUNT + 1)
    ]
