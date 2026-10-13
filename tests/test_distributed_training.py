import pytest

from kagg_revue.rl.distributed import (
    aggregate_optimization_summaries,
    even_shard,
    local_value,
    partition_cpus,
)


def test_equal_shards_cover_global_panel_without_overlap() -> None:
    shards = [tuple(even_shard(12, rank, 3)) for rank in range(3)]

    assert shards == [(0, 1, 2, 3), (4, 5, 6, 7), (8, 9, 10, 11)]
    assert local_value(12, 3, "items") == 4
    with pytest.raises(ValueError, match="divide evenly"):
        even_shard(10, 0, 3)


def test_cpu_partitions_are_balanced_and_disjoint() -> None:
    cpus = (4, 6, 8, 10, 12)
    first = partition_cpus(cpus, 0, 2)
    second = partition_cpus(cpus, 1, 2)

    assert first == (4, 6, 8)
    assert second == (10, 12)
    assert set(first).isdisjoint(second)
    assert first + second == cpus


def test_optimization_summary_uses_global_factor_weights() -> None:
    common = {
        "total_loss": 0.0,
        "value_nll": 2.0,
        "entropy": 1.0,
        "approximate_kl": 0.1,
        "clip_fraction": 0.2,
        "value_accuracy": 0.5,
        "value_brier": 0.6,
        "maximum_gradient_norm": 1.0,
        "epochs_completed": 2.0,
        "minibatches": 6.0,
    }
    first = {
        **common,
        "policy_loss": 1.0,
        "optimized_turns": 4.0,
        "optimized_decisions": 3.0,
        "optimized_policy_factors": 2.0,
    }
    second = {
        **common,
        "policy_loss": 3.0,
        "optimized_turns": 8.0,
        "optimized_decisions": 7.0,
        "optimized_policy_factors": 6.0,
        "maximum_gradient_norm": 2.0,
    }

    summary = aggregate_optimization_summaries([first, second])

    assert summary["policy_loss"] == pytest.approx(2.5)
    assert summary["optimized_turns"] == 12.0
    assert summary["optimized_decisions"] == 10.0
    assert summary["maximum_gradient_norm"] == 2.0
    assert summary["minibatches"] == 6.0
