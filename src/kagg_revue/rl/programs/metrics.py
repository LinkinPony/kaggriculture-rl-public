"""Direct terminal outcome summaries for conditional-program matches."""

from __future__ import annotations

from collections import Counter
from collections.abc import Sequence

import numpy as np

from kagg_revue.rl.programs.data import ProgramEpisode

ProgramOutcomeRow = tuple[str, int, float, float]


def outcome_rows(episodes: Sequence[ProgramEpisode]) -> list[ProgramOutcomeRow]:
    """Extract the terminal surface safe to aggregate across rollout ranks."""
    return [
        (
            episode.opponent_id,
            episode.outcome,
            episode.terminal_cash,
            episode.opponent_cash,
        )
        for episode in episodes
    ]


def outcome_metrics(rows: Sequence[ProgramOutcomeRow]) -> dict[str, object]:
    """Summarize complete-match W/D/L and cash diagnostics by opponent."""
    if not rows:
        raise ValueError("conditional-program outcomes cannot be empty")
    outcomes = np.asarray([row[1] for row in rows], dtype=np.int8)
    cash = np.asarray([row[2] for row in rows], dtype=np.float64)
    opponent_cash = np.asarray([row[3] for row in rows], dtype=np.float64)
    result: dict[str, object] = {
        "episodes": len(rows),
        "wins": int(np.count_nonzero(outcomes > 0)),
        "ties": int(np.count_nonzero(outcomes == 0)),
        "losses": int(np.count_nonzero(outcomes < 0)),
        "win_rate": float(np.mean(outcomes > 0)),
        "tie_rate": float(np.mean(outcomes == 0)),
        "mean_terminal_cash": float(cash.mean()),
        "mean_cash_difference": float((cash - opponent_cash).mean()),
    }
    opponents: dict[str, object] = {}
    for opponent in Counter(row[0] for row in rows):
        selected = [row for row in rows if row[0] == opponent]
        selected_outcomes = np.asarray([row[1] for row in selected], dtype=np.int8)
        differences = np.asarray(
            [row[2] - row[3] for row in selected],
            dtype=np.float64,
        )
        opponents[opponent] = {
            "episodes": len(selected),
            "wins": int(np.count_nonzero(selected_outcomes > 0)),
            "ties": int(np.count_nonzero(selected_outcomes == 0)),
            "losses": int(np.count_nonzero(selected_outcomes < 0)),
            "win_rate": float(np.mean(selected_outcomes > 0)),
            "mean_cash_difference": float(differences.mean()),
        }
    result["opponents"] = opponents
    return result


__all__ = ["ProgramOutcomeRow", "outcome_metrics", "outcome_rows"]
