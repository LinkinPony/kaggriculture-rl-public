import pytest

from kagg_revue.rl.evaluate import advancement_decision, compare_paired_outcomes


def _row(opponent: str, seed: int, seat: int, outcome: int) -> dict[str, object]:
    return {
        "opponent_id": opponent,
        "seed": seed,
        "candidate_seat": seat,
        "outcome": outcome,
    }


def test_paired_outcome_comparison_uses_only_match_results() -> None:
    challenger = [_row("peer", 1, 0, 1), _row("peer", 1, 1, 0)]
    incumbent = [_row("peer", 1, 0, 0), _row("peer", 1, 1, 0)]

    assert compare_paired_outcomes(challenger, incumbent) == {
        "games": 2,
        "wins": 1,
        "ties": 1,
        "losses": 0,
    }


def test_paired_outcome_comparison_rejects_unmatched_panels() -> None:
    with pytest.raises(ValueError, match="not paired"):
        compare_paired_outcomes(
            [_row("peer", 1, 0, 1)],
            [_row("peer", 2, 0, 1)],
        )


def test_advancement_requires_clean_confirmed_evidence() -> None:
    improvement = {"wins": 2, "ties": 0, "losses": 1}
    eligible = advancement_decision(
        selection_population=improvement,
        selection_head_to_head=improvement,
        confirmation_population=improvement,
        confirmation_head_to_head=improvement,
        evidence_valid=True,
        clean_source=True,
        public_opponents=1,
    )
    dirty = advancement_decision(
        selection_population=improvement,
        selection_head_to_head=improvement,
        confirmation_population=improvement,
        confirmation_head_to_head=improvement,
        evidence_valid=True,
        clean_source=False,
        public_opponents=1,
    )

    assert eligible["promotion_eligible"] is True
    assert dirty["promotion_eligible"] is False
    assert isinstance(dirty["reasons"], list)
    assert "source_revision_is_dirty" in dirty["reasons"]
