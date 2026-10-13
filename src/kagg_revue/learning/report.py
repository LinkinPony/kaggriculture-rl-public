"""Summarize completed random-root budget curves without promoting a policy."""

import json
from pathlib import Path
from typing import Any

import hydra
from omegaconf import DictConfig, OmegaConf

from kagg_revue.artifacts.io import digest, write_json
from kagg_revue.configuration import FrozenSettings
from kagg_revue.evaluation.comparison import paired_scores
from kagg_revue.learning.config import Experiment
from kagg_revue.learning.state import budget_member, member_path
from kagg_revue.learning.storage.roles import required_members


class Report(FrozenSettings):
    """Explicit completed runs and a repository-owned report destination."""

    runs: tuple[Path, ...]
    output_dir: Path


def summarize(directory: Path) -> dict[str, Any]:
    """Verify complete budgets, checkpoint identities and all scheduled evaluations."""
    state_path = directory / "state.json"
    state = json.loads(state_path.read_text())
    status = json.loads((directory / "run-status.json").read_text())
    config = Experiment.model_validate(state["protocol"])
    if (
        config.output_dir != directory
        or state["initialization"] != "random"
        or state["input_weights"]
        or status["status"] != "complete"
        or state["completed_update"] != config.updates
    ):
        raise ValueError("budget reporting requires a completed, authenticated random-root run")
    for name in required_members(config, state):
        member_path(config, state, name)
    identities = {**state.get("retired_members", {}), **state["members"]}
    records = state["records"]
    if [row["update"] for row in records] != list(range(1, config.updates + 1)):
        raise ValueError("training ledger has missing or duplicate updates")
    updates = sorted(
        {
            0,
            *range(config.evaluation.interval, config.updates + 1, config.evaluation.interval),
            config.updates,
        }
    )
    curves = []
    baseline = None
    for update in updates:
        result = json.loads((directory / "evaluation" / f"selection-{update:06d}.json").read_text())
        member = budget_member(state, update)
        if result["checkpoint_sha256"] != identities[member]:
            raise ValueError("evaluation does not identify the scheduled checkpoint")
        baseline = result if baseline is None else baseline
        curves.append(
            {
                "update": update,
                "physical_games": config.games * update,
                "policy_transitions": sum(row["official_transitions"] for row in records[:update]),
                "initial_state_games": sum(
                    row["physical_games"]
                    for row in records[:update]
                    if row.get("restart", {}).get("start_step", 0) == 0
                ),
                "mean_score": result["mean_score"],
                "mean_cash": result["mean_cash"],
                "score_change": paired_scores(baseline, result)["mean_score_change"],
            }
        )
    control = json.loads((directory / "evaluation" / "confirmation-000000.json").read_text())
    candidate = json.loads(
        (directory / "evaluation" / f"confirmation-{config.updates:06d}.json").read_text()
    )
    if (
        control["checkpoint_sha256"] != state["members"][budget_member(state, 0)]
        or candidate["checkpoint_sha256"] != state["members"][state["latest"]]
    ):
        raise ValueError("confirmation does not identify the initial and final checkpoints")
    return {
        "run": str(directory),
        "run_id": state["run_id"],
        "seed": config.seed,
        "operation_quantity_bias": config.operation_quantity_bias,
        "rl_initial": budget_member(state, 0),
        "pretraining": state.get("pretraining"),
        "state_sha256": digest(state_path),
        "source_sha256": state["source"],
        "training_games": sum(row["physical_games"] for row in records),
        "policy_transitions": sum(row["official_transitions"] for row in records),
        "initial_state_games": sum(
            row["physical_games"]
            for row in records
            if row.get("restart", {}).get("start_step", 0) == 0
        ),
        "cash_reward_weight": config.cash_weight,
        "cash_reward_scale": config.cash_scale,
        "cash_margin_reward": config.cash_margin.model_dump(mode="json")
        if config.cash_margin
        else None,
        "curriculum": None
        if config.curriculum is None
        else config.curriculum.model_dump(mode="json"),
        "actor_steps": sum(row["optimization"]["actor_steps"] for row in records),
        "rejected_actor_steps": sum(row["optimization"]["rejected_actor_steps"] for row in records),
        "starting_learning_rate": config.actor_learning_rate,
        "final_learning_rate": records[-1]["optimization"]["actor_learning_rate"],
        "sampled_opponents": sorted(
            {row["opponent"]["path"] for row in records if row["opponent"]}
        ),
        "selection": curves,
        "confirmation": paired_scores(control, candidate),
        "final_mean_cash": candidate["mean_cash"],
        "final_max_cash": max(game["cash"] for game in candidate["games"]),
    }


def run(config: Report) -> None:
    """Publish evidence and a compact reviewer-facing table for the fixed budget."""
    path = config.output_dir
    if path.is_absolute() or ".." in path.parts or path.parts[:1] != ("outputs",):
        raise ValueError("generated learning reports belong under outputs")
    if not config.runs or len(set(config.runs)) != len(config.runs):
        raise ValueError("comparison requires distinct explicitly selected runs")
    rows = [summarize(directory) for directory in config.runs]
    write_json(
        path / "comparison.json",
        {
            "runs": rows,
            "scope": "Each run's own initial and random neural controls; opponents differ between "
            "runs. No external competitive-strength evidence.",
            "distinct_initialization_seeds": len({row["seed"] for row in rows}),
            "scaling_verified": False,
            "deployment_qualified": False,
        },
    )
    lines = [
        "# Random-root reinforcement learning: initial budget curves",
        "",
        "Controls are each run's RL initial policy and random anchors; "
        "this does not establish external competitive strength.",
        "",
        "| Run | Seed | Training games | Confirmation score change | Seed-cluster 95% interval |",
        "| --- | --- | ---: | ---: | --- |",
    ]
    for row in rows:
        paired = row["confirmation"]
        lower, upper = paired["seed_cluster_bootstrap_95_interval"]
        lines.append(
            f"| {Path(row['run']).name} | {row['seed']} | {row['training_games']:,} | "
            f"{paired['mean_score_change']:+.2%} | [{lower:+.2%}, {upper:+.2%}] |"
        )
    lines.extend(
        [
            "",
            "Selection follows each run's fixed schedule; confirmation uses separate seeds.",
            "Intervals cluster both seats and opponents by seed; "
            "all these evaluations start at turn zero.",
            "Training game counts can include suffixes; "
            "the JSON also records policy transitions and whole games.",
            "Runs sharing an initialization seed are not independent training replications. "
            "Each row uses its own anchors; cross-run comparisons need a common opponent panel.",
            "No candidate is promoted by this report.",
            "Where demonstrations initialize a run, zero RL budget is the final fixed "
            "demonstration checkpoint. Those optimizer steps and rows are recorded separately.",
        ]
    )
    (path / "comparison.md").write_text("\n".join(lines) + "\n")
    print(json.dumps({"output_dir": str(path), "seeds": [row["seed"] for row in rows]}))


@hydra.main(
    version_base=None,
    config_path=str(Path(__file__).resolve().parents[3] / "configs"),
    config_name="learning_report",
)
def main(configuration: DictConfig) -> None:
    """Resolve explicit artifact paths before constructing a completed-budget report."""
    run(Report.model_validate(OmegaConf.to_container(configuration.report, resolve=True)))


if __name__ == "__main__":
    main()
