"""Pipeline routing preserves learned seats, frozen pairs and original game ordering."""

from pathlib import Path

import pytest

from kagg_revue.learning.adapter import runtime_settings
from kagg_revue.learning.collection.partitions import partition
from kagg_revue.learning.config import Experiment
from kagg_revue.learning.optimization.settings import HistoricalPopulation


@pytest.mark.parametrize("allocation", [(("a", 12),), (("a", 14),), (("a", 2), ("b", 2))])
def test_partition_preserves_seats(allocation: tuple[tuple[str, int], ...]) -> None:
    """Every original physical game and learner row occurs once with the same seat parity."""
    settings = runtime_settings(Experiment(output_dir=Path("outputs/learning/partition-test")))
    scripts = sum(count for _, count in allocation)
    selfplay = 64 - 32 - scripts
    settings = settings.model_copy(
        update={
            "ppo": settings.ppo.model_copy(
                update={
                    "script_fraction": scripts / 64,
                    "script_allocation": allocation,
                    "script_opponents": tuple(name for name, _ in allocation),
                    "history": HistoricalPopulation(checkpoint=Path("unused.pt"), fraction=0.5),
                }
            )
        }
    )
    groups = partition(settings, 64)
    assert sorted(i for group in groups for i in group.games) == list(range(64))
    assert sorted(i for group in groups for i in group.rows) == list(range(64 + selfplay))
    for group in groups:
        expected: list[int] = []
        for game in group.games:
            expected.extend((2 * game, 2 * game + 1) if game < selfplay else (selfplay + game,))
        assert group.rows == tuple(expected)
        history = [i for i in group.games if i >= selfplay + scripts]
        assert len(history) % 2 == 0
        assert all((game - selfplay - scripts) % 2 == seat % 2 for seat, game in enumerate(history))
        assert sum(count for _, count in group.settings.ppo.script_allocation) == len(
            [i for i in group.games if selfplay <= i < selfplay + scripts]
        )
