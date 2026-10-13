from kagg_revue.rl.programs.metrics import outcome_metrics


def test_program_outcomes_preserve_direct_wdl_by_opponent() -> None:
    metrics = outcome_metrics(
        [
            ("fixed-a", 1, 11.0, 7.0),
            ("fixed-a", 0, 5.0, 5.0),
            ("fixed-b", -1, 3.0, 9.0),
        ]
    )

    assert metrics["wins"] == 1
    assert metrics["ties"] == 1
    assert metrics["losses"] == 1
    opponents = metrics["opponents"]
    assert isinstance(opponents, dict)
    assert opponents["fixed-a"]["wins"] == 1
    assert opponents["fixed-b"]["losses"] == 1
