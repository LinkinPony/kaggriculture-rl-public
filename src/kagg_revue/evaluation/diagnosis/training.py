"""Freeze optimization and opponent evidence through the evaluated PPO checkpoint."""

import hashlib
import json
from collections import Counter
from pathlib import Path
from statistics import mean
from typing import Any

import hydra
from omegaconf import DictConfig, OmegaConf

from kagg_revue.artifacts.io import write_json
from kagg_revue.evaluation.diagnosis.imitation import Options


def summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Keep observed progress separate from causal or external-strength claims."""
    populations: Counter[str] = Counter()
    for row in rows:
        for name, population in row["populations"].items():
            populations[name] += population["games"]
    optimization = [row["optimization"] for row in rows]
    history_scores = [row["history_score"] for row in rows if row["history_score"] is not None]
    return {
        "updates": [rows[0]["update"], rows[-1]["update"]],
        "games": sum(row["physical_games"] for row in rows),
        "populations": dict(populations),
        "actor_steps": sum(row["actor_steps"] for row in optimization),
        "critic_steps": sum(row["critic_steps"] for row in optimization),
        "early_stop_updates": sum(row["actor_early_stop"] for row in optimization),
        "constant_return_updates": sum(
            row["actor_skipped_constant_returns"] for row in optimization
        ),
        "mean_maximum_prefix_kl": mean(row["maximum_prefix_kl"] for row in optimization),
        "maximum_prefix_kl": max(row["maximum_prefix_kl"] for row in optimization),
        "bc_retention_nonzero_updates": sum(row["bc_retention_loss"] != 0 for row in optimization),
        "mean_terminal_cash": mean(row["mean_cash"] for row in rows),
        "mean_history_score": mean(history_scores) if history_scores else None,
        "history_score_updates": len(history_scores),
    }


@hydra.main(version_base=None, config_path="../../../../configs", config_name="diagnosis_imitation")
def main(config: DictConfig) -> None:
    """Retain a compact immutable metric snapshot matched to the actor under test."""
    options = Options.model_validate(OmegaConf.to_container(config.analysis, resolve=True))
    snapshot = json.loads((options.output / "snapshot.json").read_text())
    stop = int(Path(snapshot["actors"]["ppo"]["member"]).stem.split("-")[-1])
    lines, rows = [], []
    for line in (options.run / "metrics.jsonl").read_bytes().splitlines(keepends=True):
        if not line.endswith(b"\n"):
            continue
        row = json.loads(line)
        if row["update"] > stop:
            break
        lines.append(line)
        rows.append(
            {
                k: row[k]
                for k in (
                    "update",
                    "physical_games",
                    "mean_cash",
                    "history_score",
                    "populations",
                    "optimization",
                    "pfsp",
                )
            }
        )
    if [row["update"] for row in rows] != list(range(1, stop + 1)):
        raise ValueError("metrics do not cover the frozen PPO checkpoint contiguously")
    target = options.output.parent / "training"
    target.mkdir(exist_ok=True)
    (target / "metrics.jsonl").write_text("".join(json.dumps(row) + "\n" for row in rows))
    write_json(
        target / "report.json",
        {
            "source": str(options.run / "metrics.jsonl"),
            "source_prefix_sha256": hashlib.sha256(b"".join(lines)).hexdigest(),
            "all": summarize(rows),
            "first_100": summarize(rows[:100]),
            "last_100": summarize(rows[-100:]),
            "opponent_selections": dict(Counter(row["pfsp"]["selected"]["name"] for row in rows)),
            "scope": "Changing policies and PFSP distribution: training averages are not paired "
            "strength comparisons; PPO/BC direct strength is measured separately.",
        },
    )


if __name__ == "__main__":
    main()
