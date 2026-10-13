"""Aggregate tape games: scores, paired differences, fidelity and Kaggle validation."""

import json
import math
import random
from collections import defaultdict
from pathlib import Path
from statistics import mean, median
from typing import Any

from kagg_revue.artifacts.io import write_json
from kagg_revue.evaluation.tapes.config import Study

Games = dict[tuple[int, int], dict[str, Any]]


def wilson(score: float, games: int, z: float = 1.96) -> list[float]:
    """Wilson interval on a win-rate style score (draws count as half a win)."""
    if games == 0:
        return [math.nan, math.nan]
    p = score / games
    centre = p + z * z / (2 * games)
    radius = z * math.sqrt(p * (1 - p) / games + z * z / (4 * games * games))
    scale = 1 + z * z / games
    return [(centre - radius) / scale, (centre + radius) / scale]


def load(study: Study) -> tuple[dict[str, Games], dict[str, int]]:
    """Games keyed by (episode, tape seat); failed games are counted, never scored."""
    games: dict[str, Games] = defaultdict(dict)
    errors: dict[str, int] = defaultdict(int)
    for path in sorted((study.output / "results").glob("*/*.json")):
        if path.name.endswith(".task.json"):
            continue
        record = json.loads(path.read_text())
        for game in record["games"]:
            if "error" in game:
                errors[record["label"]] += 1
            else:
                games[record["label"]][game["episode_id"], game["seat"]] = game
    return games, errors


def paired(ours: Games, base: Games, resamples: int) -> dict[str, Any]:
    """Same-tape score difference with a bootstrap over tapes."""
    keys = sorted(ours.keys() & base.keys())
    if not keys:
        return {"games": 0}
    diffs = [ours[key]["score"] - base[key]["score"] for key in keys]
    rng = random.Random(20260929)
    size = len(diffs)
    means = sorted(
        sum(diffs[rng.randrange(size)] for _ in range(size)) / size for _ in range(resamples)
    )
    return {
        "games": size,
        "difference": mean(diffs),
        "ci95": [means[int(0.025 * resamples)], means[int(0.975 * resamples) - 1]],
    }


def kaggle_record(submission: int, teams: dict[int, str], roots: list[Path]) -> dict[str, Any]:
    """Official record against the watched teams from the collectors' own-episode snapshots."""
    episodes: dict[int, dict[str, Any]] = {}
    for root in roots:
        for path in root.glob(f"snapshots/*/own/episodes/{submission}.json"):
            payload = json.loads(path.read_text())
            for episode in payload.get("episodes", []) if isinstance(payload, dict) else []:
                if episode.get("state") == "COMPLETED":
                    episodes[episode["id"]] = episode
    per_team: dict[str, list[int]] = defaultdict(lambda: [0, 0, 0])
    for episode in episodes.values():
        agents = episode["agents"]
        ours = [a for a in agents if a["submissionId"] == submission]
        other = [a for a in agents if a["submissionId"] != submission]
        if len(agents) != 2 or len(ours) != 1 or other[0].get("teamId") not in teams:
            continue
        if ours[0].get("reward") is None or other[0].get("reward") is None:
            continue
        margin = ours[0]["reward"] - other[0]["reward"]
        per_team[teams[other[0]["teamId"]]][0 if margin > 0 else 1 if margin == 0 else 2] += 1
    wins, draws, losses = (sum(row[i] for row in per_team.values()) for i in range(3))
    total = wins + draws + losses
    return {
        "games": total,
        "wins": wins,
        "draws": draws,
        "losses": losses,
        "score": (wins + 0.5 * draws) / total if total else None,
        "teams": {
            team: dict(zip(("wins", "draws", "losses"), row, strict=True))
            for team, row in per_team.items()
        },
    }


def _fidelity(games: dict[str, Games], checkpoints: tuple[int, ...]) -> dict[str, Any]:
    rows: dict[str, list[tuple[bool, float]]] = defaultdict(list)
    for cohort in games.values():
        for game in cohort.values():
            for step, value in game["fidelity"].items():
                rows[step].append((value["tiles_match"], abs(value["money_delta"])))
    return {
        str(step): {
            "tiles_match": mean(match for match, _ in rows[str(step)]),
            "median_abs_money_delta": median(delta for _, delta in rows[str(step)]),
        }
        for step in checkpoints
        if rows[str(step)]
    }


def summarize(study: Study) -> dict[str, Any]:
    """Publish report.json and summary.md for everything completed so far."""
    games, errors = load(study)
    teams = {}
    for manifest in study.tapes.manifests:
        data = json.loads(manifest.read_text())
        teams[data["team_id"]] = data["team_name"]
    roots = [manifest.parent for manifest in study.tapes.manifests]
    base = games.get(study.baseline or "", {})
    ranking = []
    for candidate in study.candidates:
        cohort = games.get(candidate.label, {})
        rows = list(cohort.values())
        score = sum(row["score"] for row in rows)
        by_team: dict[str, list[float]] = defaultdict(list)
        for row in rows:
            by_team[row["team"]].append(row["score"])
        ranking.append(
            {
                "label": candidate.label,
                "games": len(rows),
                "errors": errors.get(candidate.label, 0),
                "score": score / len(rows) if rows else None,
                "ci95": wilson(score, len(rows)),
                "wins": sum(row["score"] == 1.0 for row in rows),
                "draws": sum(row["score"] == 0.5 for row in rows),
                "losses": sum(row["score"] == 0.0 for row in rows),
                "mean_cash_margin": mean(r["own_money"] - r["tape_money"] for r in rows)
                if rows
                else None,
                "teams": {team: {"games": len(v), "score": mean(v)} for team, v in by_team.items()},
                "team_mean": mean(mean(v) for v in by_team.values()) if by_team else None,
                "paired_vs_baseline": paired(cohort, base, study.bootstrap)
                if base and candidate.label != study.baseline
                else None,
                "kaggle_watched": kaggle_record(candidate.submission, teams, roots)
                if candidate.submission
                else None,
            }
        )
    ranking.sort(key=lambda row: -1.0 if row["score"] is None else row["score"], reverse=True)
    tapes = {key: game for cohort in games.values() for key, game in cohort.items()}
    report = {
        "ranking": ranking,
        "tapes_played": len(tapes),
        "recorded_strong_seat_score": mean(
            1.0
            if g["recorded_rewards"][g["seat"]] > g["recorded_rewards"][1 - g["seat"]]
            else 0.5
            if g["recorded_rewards"][g["seat"]] == g["recorded_rewards"][1 - g["seat"]]
            else 0.0
            for g in tapes.values()
        )
        if tapes
        else None,
        "fidelity": _fidelity(games, study.checkpoints),
    }
    write_json(study.output / "report.json", report)
    (study.output / "summary.md").write_text(_markdown(report))
    return report


def _percent(value: float | None) -> str:
    return "-" if value is None or math.isnan(value) else f"{100 * value:.1f}%"


def _markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Recorded strong-team tapes against deployment packages",
        "",
        "| Candidate | Games | Score | 95% | W/D/L | Team mean | vs baseline | Kaggle watched |",
        "| --- | ---: | ---: | --- | --- | ---: | --- | --- |",
    ]
    for row in report["ranking"]:
        pair = row["paired_vs_baseline"]
        versus = (
            f"{100 * pair['difference']:+.1f} [{100 * pair['ci95'][0]:+.1f}, "
            f"{100 * pair['ci95'][1]:+.1f}]"
            if pair and pair.get("games")
            else "-"
        )
        watched = row["kaggle_watched"]
        official = (
            f"{watched['wins']}-{watched['draws']}-{watched['losses']}"
            if watched and watched["games"]
            else "-"
        )
        lines.append(
            f"| {row['label']} | {row['games']} | {_percent(row['score'])} | "
            f"{_percent(row['ci95'][0])}–{_percent(row['ci95'][1])} | "
            f"{row['wins']}/{row['draws']}/{row['losses']} | {_percent(row['team_mean'])} | "
            f"{versus} | {official} |"
        )
    lines += [
        "",
        f"Recorded strong-seat score in the original games: "
        f"{_percent(report['recorded_strong_seat_score'])}.",
        "",
    ]
    lines += ["| Step | Tape farm identical | Median abs cash drift |", "| ---: | ---: | ---: |"]
    for step, value in report["fidelity"].items():
        lines.append(
            f"| {step} | {_percent(value['tiles_match'])} | {value['median_abs_money_delta']:.0f} |"
        )
    return "\n".join(lines) + "\n"
