"""Review budgets stay bounded despite stale evidence and resume without new state."""

import json
from pathlib import Path

import numpy as np
import pytest

from kagg_revue.learning.config import Experiment, Population
from kagg_revue.learning.matchmaking.config import Inheritance, Mastery, Pfsp
from kagg_revue.learning.matchmaking.defaults import training_defaults
from kagg_revue.learning.matchmaking.statistics import Record, probabilities
from kagg_revue.learning.state import protocol


def _panel(wins: int, games: int = 64) -> dict[str, int]:
    return {"games": games, "wins": wins, "ties": 0, "losses": games - wins}


def test_mastery_requires_exposure_and_releases_after_regression() -> None:
    """Insufficient exposure cannot qualify; poor review results restore priority."""
    config = Pfsp(mastery=Mastery())
    record = Record()
    assert not record.mastered(config)
    record.observe(_panel(32, 32), 1, config)
    assert not record.mastered(config)
    record.observe(_panel(64), 300, config)
    assert record.mastered(config)
    assert record.probability(10000, config) == pytest.approx(0.5)
    assert Record.model_validate_json(record.model_dump_json()).mastered(config)
    # The next real encounter discounts old evidence before adding fresh results.
    record.observe(_panel(48), 10000, config)
    assert not record.mastered(config)
    tied = Record(wins=0, ties=128, effective_games=128, effective_score=64)
    assert not tied.mastered(config)


def test_mastered_budget_does_not_grow_with_pool_or_age() -> None:
    """Hundreds of mastered policies share one review budget; latest remains covered."""
    config = Pfsp(mastery=Mastery())
    mastered = Record(wins=128, effective_games=100, effective_score=100, last_update=2)
    records = [mastered] * 300 + [Record(), mastered]
    before = [record.model_dump() for record in records]
    weights = probabilities(records, 10000, config, latest=True)
    assert weights[:300].sum() == pytest.approx(0.05)
    assert weights[-1] >= 0.95 * config.latest_fraction
    assert np.all(weights > 0) and weights.sum() == pytest.approx(1)
    assert [record.model_dump() for record in records] == before
    # Uniform exploration is also restricted to regular opponents.
    expected = probabilities(records[-2:], 10000, Pfsp(), latest=True)
    np.testing.assert_allclose(weights[-2:], 0.95 * expected)


def test_empty_mastery_sets_and_archived_protocol_remain_compatible() -> None:
    """Empty review sets preserve old probabilities and all-mastered sets stay finite."""
    config = Pfsp(mastery=Mastery())
    records = [Record(), Record(losses=64, effective_games=64)]
    np.testing.assert_array_equal(
        probabilities(records, 1, config, latest=True),
        probabilities(records, 1, Pfsp(), latest=True),
    )
    mastered = Record(wins=128, effective_games=128, effective_score=128)
    np.testing.assert_allclose(probabilities([mastered] * 4, 1, config, latest=False), [0.25] * 4)
    experiment = Experiment(
        output_dir=Path("outputs/learning/mastery-test"), population=Population(pfsp=Pfsp())
    )
    saved = protocol(experiment)
    assert not {"mastery", "inheritance"} & saved["population"]["pfsp"].keys()
    assert protocol(Experiment.model_validate(saved)) == saved


def test_new_training_enables_review_without_changing_explicit_choices() -> None:
    """Only an omitted setting receives the new training default."""
    config = Experiment(
        output_dir=Path("outputs/learning/mastery-default-test"),
        population=Population(pfsp=Pfsp()),
    )
    resolved = training_defaults(config)
    assert resolved.population.pfsp is not None
    assert resolved.population.pfsp.mastery == Mastery()
    assert resolved.population.pfsp.inheritance == Inheritance()
    assert training_defaults(resolved) == resolved
    assert config.population.pfsp is not None and config.population.pfsp.mastery is None
    for choice in (None, Mastery(review_fraction=0.1)):
        partial = Population(pfsp=Pfsp(mastery=choice))
        filled = training_defaults(config.model_copy(update={"population": partial}))
        assert filled.population.pfsp is not None
        assert filled.population.pfsp.mastery == choice
        assert filled.population.pfsp.inheritance == Inheritance()
        explicit = config.model_copy(
            update={"population": Population(pfsp=Pfsp(mastery=choice, inheritance=None))}
        )
        assert training_defaults(explicit) is explicit
    disabled = config.model_copy(update={"population": Population(pfsp=None)})
    assert training_defaults(disabled) is disabled


@pytest.mark.parametrize("enabled", [False, True])
def test_resume_preserves_archived_or_bootstrapped_default(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, enabled: bool
) -> None:
    """Legacy archives stay disabled; a new bootstrap restores its resolved rule."""
    monkeypatch.chdir(tmp_path)
    config = Experiment(
        output_dir=Path("outputs/learning/mastery-default-test"),
        population=Population(pfsp=Pfsp()),
    )
    config.output_dir.mkdir(parents=True)
    effective = training_defaults(config) if enabled else config
    saved = protocol(effective)
    (config.output_dir / "state.json").write_text(json.dumps({"protocol": saved}))
    restored = training_defaults(config.model_copy(update={"resume": True}))
    assert protocol(restored) == saved
    # Ordinary archived protocol parsing retains its original interpretation.
    assert protocol(Experiment.model_validate(saved)) == saved
