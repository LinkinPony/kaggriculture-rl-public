"""Separate counterfactual training labels from independent student match evidence."""

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np

from kagg_revue.artifacts.io import write_json
from kagg_revue.policy.spatial.model import Policy
from kagg_revue.production.branching.data import BranchTape
from kagg_revue.production.expert.assessment import Assessment
from kagg_revue.production.expert.telemetry import panel_summary
from kagg_revue.production.expert.train import _comparison


def search_summary(tape: BranchTape) -> dict[str, Any]:
    """Report direct improvements as hindsight labels, never as a deployable agent's wins."""
    outcomes = tape.outcomes.cpu().numpy()
    scripts = tape.scripts.cpu().numpy()
    values = outcomes.mean(1)
    gains = values - values[:, :1]
    useful = gains.max(-1) > 0
    candidates = []
    for candidate in range(outcomes.shape[-1]):
        record: dict[str, Any] = {"candidate": candidate}
        for name, selected in (("scripts", scripts), ("selfplay", ~scripts)):
            candidate_outcomes = outcomes[selected, :, candidate]
            record[name] = {
                "wins": int((candidate_outcomes > 0).sum()),
                "ties": int((candidate_outcomes == 0).sum()),
                "losses": int((candidate_outcomes < 0).sum()),
                "wdl_gain": float(
                    (outcomes[selected, :, candidate] - outcomes[selected, :, 0]).sum()
                ),
            }
        candidates.append(record)
    return {
        "roots": len(outcomes),
        "improved_roots": int(useful.sum()),
        "script_improved_roots": int((useful & scripts).sum()),
        "selfplay_improved_roots": int((useful & ~scripts).sum()),
        "informative_pairs": int(((gains != 0) & useful[:, None]).sum()),
        "physical_games": int(outcomes.size),
        "root_decisions": sorted(np.unique(tape.steps.cpu().numpy()).tolist()),
        "candidates": candidates,
        "hindsight_labels_only": True,
        "continuations": ["frozen_current_student", "frozen_search_g40"],
    }


class StudentAssessment(Assessment):
    """Compare the unassisted student to its start, the frozen expert and original PPO."""

    def run_student(
        self, student: Policy, initial: Policy, expert: Policy, seed: int, path: Path
    ) -> dict[str, Any]:
        """Keep common seeds/seats and retain raw per-game outcomes for all controls."""
        panels = {}
        for name, model in (
            ("student", student),
            ("initial", initial),
            ("expert", expert),
            ("origin", self.reference),
        ):
            self.policy.load_state_dict(model.state_dict())
            panels[name] = self.matches.run(seed)
        record = {
            "population": "scripts" if self.rank == 0 else "neural",
            "seed_start": seed,
            **panels,
            **{
                f"paired_to_{role}": _comparison(panels["student"], panels[role])
                for role in ("initial", "expert", "origin")
            },
        }
        write_json(path, record)
        return {
            **{name: panel_summary(panel, opponents=True) for name, panel in panels.items()},
            **{name: value for name, value in record.items() if name not in panels},
            "report": str(path),
            "physical_games": sum(len(panel["games"]) for panel in panels.values()),
        }


def evaluation_report(
    directory: Path,
    workers: list[dict[str, Any]],
    checkpoint: dict[str, Any],
    source: dict[str, Any],
) -> dict[str, Any]:
    """Publish only independently executed whole-policy outcomes in the model panel."""
    assessments = {w["assessment"]["population"]: w["assessment"] for w in workers}
    outcomes = {}
    for population, assessment in assessments.items():
        for role in ("student", "initial", "expert", "origin"):
            panel = assessment[role]
            outcomes[f"{role} / {population}"] = {
                **{key: panel[key] for key in ("wins", "ties", "losses")},
                "mean_terminal_cash": panel["mean_cash"],
                "mean_cash_difference": panel["mean_cash_difference"],
            }
    write_json(
        directory / "evaluation-report.json",
        {
            "generated_at": datetime.now(UTC).isoformat(),
            "checkpoint": checkpoint,
            "source": source,
            "completion": {"complete": True},
            "execution": {"backend": "native", "deployment_budget_qualified": False},
            "decision_surface": "unassisted argmax student on fresh paired complete games",
            "decision": {
                "status": "retain_incumbent",
                "reasons": ["状态分支仅产生训练标签；模型面板为学生独立 argmax 完整比赛。"],
            },
            "outcomes": outcomes,
        },
    )
    return assessments
