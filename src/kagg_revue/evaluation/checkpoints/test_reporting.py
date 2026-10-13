"""Check weighting and seed-pair completeness for checkpoint selection."""

import pytest

from kagg_revue.evaluation.checkpoints.reporting import panel_values
from kagg_revue.evaluation.checkpoints.schedule import panel


def test_families_receive_weight_independent_of_opponent_count() -> None:
    """Seven easy scripts cannot outweigh one difficult policy family."""
    manifest = {
        "opponents": [{"name": "strong", "group": "neural"}],
        "scripts": ["script1", "script2"],
        "group_weights": {"neural": 0.5, "scripts": 0.5},
    }
    rows = [
        {
            "candidate": "model",
            "opponent": opponent,
            "group": "neural" if opponent == "strong" else "scripts",
            "seed": seed,
            "seat": seat,
            "outcome": -1 if opponent == "strong" else 1,
        }
        for opponent in ("strong", "script1", "script2")
        for seed in (10, 11)
        for seat in (0, 1)
    ]
    values, _, seeds = panel_values(manifest, rows, ["model"])
    assert seeds == [10, 11]
    assert values.tolist() == [[0.5, 0.5]]
    with pytest.raises(ValueError, match="incomplete"):
        panel_values(manifest, rows[:-1], ["model"])
    with pytest.raises(ValueError, match="duplicate"):
        panel_values(manifest, rows + [rows[0]], ["model"])


def test_extension_preserves_existing_games_and_adds_new_paired_seeds() -> None:
    """An equal-cohort extension cannot silently replace previous evidence."""
    manifest = {"opponents": [{"name": "opponent", "group": "family"}], "scripts": ["script"]}
    base = panel(manifest, ["a", "b"], "confirmation", 128, 1000, 2000)
    extended = panel(manifest, ["a", "b"], "confirmation", 192, 1000, 2000)
    indexed = {task.name: task for task in extended}
    assert all(indexed[task.name] == task for task in base)
    added = [task for task in extended if task.name not in {row.name for row in base}]
    assert len(added) == 4
    assert {task.seed for task in added} == {1064}
