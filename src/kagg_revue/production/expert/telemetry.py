"""Compact, direct-outcome observations for parameter-space policy search."""

import json
import time
from pathlib import Path
from typing import Any


def panel_summary(panel: dict[str, Any], *, opponents: bool = False) -> dict[str, Any]:
    """Strip per-game traces, optionally retaining each opponent's direct outcomes."""
    result: dict[str, Any] = {
        key: panel[key]
        for key in ("wins", "ties", "losses", "mean_cash", "mean_cash_difference")
        if key in panel
    }
    games = sum(result.get(key, 0) for key in ("wins", "ties", "losses"))
    result["games"] = games
    if games:
        result["win_rate"] = result["wins"] / games
    if opponents:
        groups: dict[str, list[dict[str, Any]]] = {}
        for game in panel.get("games", []):
            groups.setdefault(game["opponent"], []).append(game)
        result["opponents"] = {
            name: {
                "wins": sum(game["outcome"] > 0 for game in rows),
                "ties": sum(game["outcome"] == 0 for game in rows),
                "losses": sum(game["outcome"] < 0 for game in rows),
                "mean_cash": sum(game["cash"] for game in rows) / len(rows),
                "mean_cash_difference": sum(game["cash"] - game["opponent_cash"] for game in rows)
                / len(rows),
            }
            for name, rows in groups.items()
        }
    return result


def candidate_summary(candidate: dict[str, Any], controls: dict[str, Any]) -> dict[str, Any]:
    """Expose population-specific WDL changes used by the existing selection rule."""
    result = {key: candidate[key] for key in ("candidate", "mutation_seed", "scale")}
    gains = []
    for name in ("scripts", "neural"):
        panel, baseline = candidate[name], controls[name]
        gain = panel["wins"] - panel["losses"] - baseline["wins"] + baseline["losses"]
        gains.append(gain)
        result[name] = panel_summary(panel)
        result[f"{name}_wdl_gain"] = gain
    result["eligible"] = min(gains) >= 0 and sum(gains) > 0
    return result


def generation_summary(ranks: list[dict[str, Any]], selected: dict[str, Any]) -> dict[str, Any]:
    """Keep search candidates separate from the adopted policy's fresh selection panel."""
    candidates = sorted(
        (candidate for rank in ranks for candidate in rank["search"]["candidates"]),
        key=lambda candidate: candidate["candidate"],
    )
    selection = {
        key: selected[key] for key in ("seed_start", "selected", "paired_scripts", "paired_neural")
    }
    for name in ("scripts", "neural", "baseline_scripts", "baseline_neural"):
        selection[name] = panel_summary(selected[name], opponents=True)
    selection["candidates"] = [
        {
            "candidate": record["candidate"]["candidate"],
            "paired_scripts": record["paired_scripts"],
            "paired_neural": record["paired_neural"],
        }
        for record in selected["candidates"]
    ]
    return {
        "counts": {
            "candidates": len(candidates),
            "eligible": sum(candidate["eligible"] for candidate in candidates),
            "finalists": len(selected["candidates"]),
            "accepted": int(selected["selected"] is not None),
        },
        "search": {
            "seed_start": ranks[0]["search"]["seed_start"],
            "controls": ranks[0]["search"]["controls"],
            "candidates": candidates,
        },
        "selection": selection,
        "ranks": [
            {key: value for key, value in rank.items() if key not in {"search", "finalists"}}
            for rank in ranks
        ],
    }


def progress(
    directory: Path, generation: int, rank: int, phase: str, completed: int, total: int
) -> None:
    """Publish one atomic heartbeat per coarse match panel, never per environment turn."""
    path = directory / "progress" / f"rank-{rank}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".partial")
    temporary.write_text(
        json.dumps(
            {
                "generation": generation,
                "rank": rank,
                "phase": phase,
                "completed": completed,
                "total": total,
                "updated_at": time.time(),
            }
        )
        + "\n"
    )
    temporary.replace(path)
