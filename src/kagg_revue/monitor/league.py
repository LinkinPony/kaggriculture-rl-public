"""Read specialist league telemetry without loading models or training modules."""

import math
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from kagg_revue.monitor.snapshots import read_snapshot

MEMBERS = ("a", "bc", "spataro")


def progress(run_dir: Path) -> dict[str, Any]:
    """Combine the small parent snapshot and three live BC progress snapshots."""
    live = read_snapshot(run_dir / "league-progress.json")
    if not live:
        return {}
    config = read_snapshot(run_dir / "resolved-config.json")
    experiment = config.get("experiment", {})
    status = read_snapshot(run_dir / "run-status.json")
    members = live.get("members", {})
    pretraining = {
        name: {
            **read_snapshot(run_dir / name / "learning-progress.json"),
            "completed_epochs": members.get(name, {}).get("bc_epochs", 0),
        }
        for name in members
    }
    active = str(live.get("active_member", ""))
    return {
        **(pretraining.get(active, {}) if live.get("phase") == "bc" else {}),
        **live,
        "league": True,
        "phase": {"bc": "demonstrations", "rl": "reinforcement_learning"}.get(
            str(live.get("phase", "")), live.get("phase")
        ),
        "update": live.get("completed_update", 0),
        "checkpoint_update": status.get("completed_update", 0),
        "checkpoint_interval": experiment.get("checkpoint_interval"),
        "games_per_update": experiment.get("games"),
        "games_per_pair": config.get("games_per_pair"),
        "selfplay_games_per_member": config.get("selfplay_games_per_member", 0),
        "script_opponents": experiment.get("script_population", {}).get("agents", [])
        if experiment.get("script_population")
        else [],
        "games_per_script_per_member": config.get("games_per_script_per_member", 0),
        "epochs": config.get("bc_epochs", live.get("epochs")),
        "pretraining": pretraining,
    }


def _number(value: object) -> float | None:
    if isinstance(value, int | float) and not isinstance(value, bool) and math.isfinite(value):
        return float(value)
    return None


def pair_summaries(row: Mapping[str, object]) -> dict[str, dict[str, float]]:
    """Return each pairing from the named left member's perspective, in either seat."""
    pairs = row.get("pairs")
    if not isinstance(pairs, Mapping):
        return {}
    output = {}
    for name, values in pairs.items():
        if not isinstance(name, str) or not isinstance(values, Mapping):
            continue
        sides = name.split("_vs_")
        if len(sides) != 2 or not any(side in MEMBERS for side in sides):
            continue
        panel = {
            "ties" if key == "draws" else key: number
            for key, value in values.items()
            if (number := _number(value)) is not None
        }
        games = panel.get("games", 0)
        if games <= 0:
            continue
        for count, rate in (("wins", "win_rate"), ("ties", "tie_rate"), ("losses", "loss_rate")):
            if count in panel:
                panel[rate] = panel[count] / games
        for side in ("left", "right"):
            total = panel.get(f"cash_{side}_sum")
            if total is not None:
                panel[f"mean_cash_{side}"] = total / games
        if "mean_cash_left" in panel and "mean_cash_right" in panel:
            panel["mean_cash_difference"] = panel["mean_cash_left"] - panel["mean_cash_right"]
            panel["mean_terminal_cash"] = (panel["mean_cash_left"] + panel["mean_cash_right"]) / 2
        if "absolute_cash_difference_sum" in panel:
            panel["mean_absolute_cash_difference"] = panel["absolute_cash_difference_sum"] / games
        output[name] = panel
    return output


def _outcome_metrics(row: Mapping[str, object]) -> dict[str, float]:
    output = {}
    members: dict[str, dict[str, float]] = {}
    pairs = pair_summaries(row)
    for pair, panel in pairs.items():
        output.update({f"rl/league/pairs/{pair}/{key}": value for key, value in panel.items()})
        left, right = pair.split("_vs_")
        if left == right:
            totals = members.setdefault(left, {})
            totals["games"] = totals.get("games", 0) + panel["games"]
            if "mean_terminal_cash" in panel:
                totals["cash_sum"] = (
                    totals.get("cash_sum", 0) + panel["mean_terminal_cash"] * panel["games"]
                )
            continue
        for side, member in zip(("left", "right"), (left, right), strict=True):
            if member not in MEMBERS:
                continue
            totals = members.setdefault(member, {})
            totals["mutual_games"] = totals.get("mutual_games", 0) + panel["games"]
            for target, source in (
                ("games", "games"),
                ("wins", "wins" if side == "left" else "losses"),
                ("ties", "ties"),
                ("losses", "losses" if side == "left" else "wins"),
                ("cash_sum", f"cash_{side}_sum"),
            ):
                if source in panel:
                    totals[target] = totals.get(target, 0) + panel[source]
    for name, values in members.items():
        games = values["games"]
        if "wins" in values:
            values["win_rate"] = values["wins"] / values["mutual_games"]
        if "cash_sum" in values:
            values["mean_terminal_cash"] = values["cash_sum"] / games
        output.update({f"rl/league/members/{name}/{key}": value for key, value in values.items()})
    cash_panels = [panel for panel in pairs.values() if "mean_terminal_cash" in panel]
    cash_games = sum(panel["games"] for panel in cash_panels)
    if cash_games:
        output["rl/rollout/mean_terminal_cash"] = (
            sum(panel["mean_terminal_cash"] * panel["games"] for panel in cash_panels) / cash_games
        )
    return output


def metrics(row: Mapping[str, object]) -> dict[str, float]:
    """Normalize global games, per-member PPO and per-rank resource measurements.

    PPO steps are synchronized across ranks: take the maximum, never the sum.
    Losses and learning rates are averaged across replicas; KL/flags/times use
    the maximum. The critical-path learner time is the largest rank's sum of
    sequential member times. Physical games already include both ranks.
    """
    if not isinstance(row.get("pairs"), Mapping) or not isinstance(row.get("workers"), list):
        return {}
    output = {"rl/run/league": 1.0, **_outcome_metrics(row)}
    panels = pair_summaries(row)
    selfplay_games = sum(
        panel["games"] for name, panel in panels.items() if len(set(name.split("_vs_"))) == 1
    )
    output["rl/league/selfplay_physical_games"] = selfplay_games
    output["rl/league/mutual_physical_games"] = (
        sum(
            panel["games"]
            for name, panel in panels.items()
            if all(side in MEMBERS for side in name.split("_vs_"))
        )
        - selfplay_games
    )
    output["rl/league/script_physical_games"] = sum(
        panel["games"]
        for name, panel in panels.items()
        if any(side not in MEMBERS for side in name.split("_vs_"))
    )
    for key, tag in (
        ("physical_games", "rl/rollout/physical_games"),
        ("cumulative_physical_games", "rl/rollout/cumulative_physical_games"),
        ("update_seconds", "rl/system/update_elapsed_seconds"),
    ):
        if (number := _number(row.get(key))) is not None:
            output[tag] = number
    replicas: dict[str, list[float]] = {}
    optimization_times = []
    workers = row["workers"]
    assert isinstance(workers, list)
    for worker in workers:
        if not isinstance(worker, Mapping):
            continue
        for field, tag in (
            ("rollout_seconds", "rl/rollout/elapsed_seconds"),
            ("encoding_seconds", "rl/system/encoding_seconds"),
            ("inference_seconds", "rl/system/inference_seconds"),
            ("native_seconds", "rl/system/native_seconds"),
            ("peak_allocated_bytes", "rl/system/cuda_peak_allocated_bytes"),
        ):
            value = _number(worker.get(field))
            if value is not None:
                output[tag] = max(output.get(tag, value), value)
                rank = worker.get("rank")
                if isinstance(rank, int) and not isinstance(rank, bool):
                    output[f"rl/league/ranks/{rank}/{field}"] = value
        optimization = worker.get("optimization")
        if not isinstance(optimization, Mapping):
            continue
        elapsed = []
        for name in optimization:
            panel = optimization.get(name)
            if not isinstance(panel, Mapping):
                continue
            for key, value in panel.items():
                number = float(value) if isinstance(value, bool) else _number(value)
                if number is not None:
                    replicas.setdefault(f"rl/league/optimization/{name}/{key}", []).append(number)
                    if key == "learner_seconds":
                        elapsed.append(number)
        if len(elapsed) == len(optimization):
            optimization_times.append(sum(elapsed))
    for tag, values in replicas.items():
        field = tag.rsplit("/", 1)[-1]
        use_max = field.endswith(("_steps", "_seconds", "_kl")) or field in {
            "actor_early_stop",
            "critic_warmup",
            "actor_skipped_constant_returns",
        }
        output[tag] = max(values) if use_max else sum(values) / len(values)
    if optimization_times:
        output["rl/system/optimization_seconds"] = max(optimization_times)
    for elapsed_tag, rate_tag in (
        ("rl/system/update_elapsed_seconds", "rl/system/physical_games_per_second"),
        ("rl/rollout/elapsed_seconds", "rl/rollout/games_per_second"),
    ):
        duration = output.get(elapsed_tag, 0)
        if duration > 0 and "rl/rollout/physical_games" in output:
            output[rate_tag] = output["rl/rollout/physical_games"] / duration
    return output
