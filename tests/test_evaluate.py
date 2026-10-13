from kagg_revue.bc.evaluate import summarize_games


def test_summary_reports_direct_outcomes() -> None:
    rows = [
        {
            "outcome": 1,
            "candidate_money": 4.0,
            "margin": 1.0,
            "candidate_error": None,
            "candidate_max_seconds": 0.1,
            "candidate_remaining_overage_seconds": 1.0,
        },
        {
            "outcome": -1,
            "candidate_money": 2.0,
            "margin": -3.0,
            "candidate_error": None,
            "candidate_max_seconds": 0.2,
            "candidate_remaining_overage_seconds": 0.8,
        },
    ]
    summary = summarize_games(rows)
    assert summary["wins"] == 1
    assert summary["losses"] == 1
    assert summary["mean_terminal_cash"] == 3.0
    assert summary["max_act_seconds"] == 0.2
