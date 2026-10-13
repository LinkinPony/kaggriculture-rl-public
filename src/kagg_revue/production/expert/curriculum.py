"""Improve a neural search expert around the current gradient-trained apprentice."""

import json
from pathlib import Path
from typing import Any

import torch
import torch.distributed as dist

from kagg_revue.artifacts.io import digest, write_json
from kagg_revue.evaluation.neural import NeuralMatches
from kagg_revue.policy.checkpoints import load_policy, save_policy
from kagg_revue.policy.spatial.model import Policy
from kagg_revue.production.evaluation.matches import ScriptMatches
from kagg_revue.production.expert.config import ApprenticeSettings
from kagg_revue.production.expert.generation import propose_generation
from kagg_revue.production.expert.mutations import ParameterSearch, readout_parameters
from kagg_revue.production.expert.screen import score
from kagg_revue.production.expert.selection import select_generation
from kagg_revue.production.expert.telemetry import generation_summary
from kagg_revue.production.train import _gather


class Curriculum:
    """Keep proposal weights separate: the apprentice receives only supervised gradients."""

    def __init__(self, config: ApprenticeSettings, student: Policy, reference: Policy, rank: int):
        """Create persistent native/GPU search workers without changing the learner model."""
        self.config, self.rank = config, rank
        device = next(student.parameters()).device
        self.policy = Policy.from_layout(student.layout).to(device).eval().requires_grad_(False)
        self.parent = Policy.from_layout(student.layout).to(device).eval().requires_grad_(False)
        self.policy.load_state_dict(student.state_dict())
        self.parent.load_state_dict(student.state_dict())
        self.scripts = ScriptMatches(config.production, self.policy)
        self.neural = NeuralMatches(config.production, self.policy, self.parent)
        self.reference = (
            NeuralMatches(config.production, self.policy, reference) if rank == 0 else None
        )
        self.mutation = ParameterSearch(readout_parameters(self.policy))

    def improve(self, student: Policy, teacher: Policy, update: int) -> dict[str, Any]:
        """Replace the expert only after fresh paired improvement over student and old expert."""
        c, rank = self.config, self.rank
        world = len(c.production.devices)
        directory = c.production.output_dir
        self.parent.load_state_dict(student.state_dict())
        self.policy.load_state_dict(student.state_dict())
        self.mutation.recenter()
        local = propose_generation(
            c, self.policy, self.mutation, self.scripts, self.neural, rank, update
        )
        ranks = _gather(local, world)
        summary_path = directory / "search" / f"update-{update:06d}.json"
        if rank == 0:
            assert self.reference is not None
            finalists = sorted(
                (item for record in ranks for item in record["finalists"]),
                key=lambda item: (-item["fitness"], item["candidate"]),
            )[: c.finalists]
            seed = c.production.evaluation_seed + (update - 1) * c.production.evaluation_games // 2
            self.policy.load_state_dict(teacher.state_dict())
            previous = {"scripts": self.scripts.run(seed), "neural": self.reference.run(seed)}
            selected = select_generation(
                c, self.policy, self.parent, self.scripts, self.reference, finalists, update
            )
            gains = [score(selected[name]) - score(previous[name]) for name in previous]
            accepted = selected["selected"] is not None and min(gains) >= 0 and sum(gains) > 0
            identity = None
            if accepted:
                path = directory / "experts" / f"update-{update:06d}.pt"
                teacher.load_state_dict(self.policy.state_dict())
                save_policy(
                    path,
                    teacher,
                    c.production,
                    search_update=update,
                    training_phase="searched_expert",
                    selected=selected["selected"],
                )
                identity = {"path": str(path), "sha256": digest(path)}
            summary = {
                "update": update,
                "expert_replaced": accepted,
                "expert": identity,
                "paired_wdl_gain_over_previous_expert": dict(zip(previous, gains, strict=True)),
                "physical_games": sum(record["physical_games"] for record in ranks)
                + selected["physical_games"]
                + 2 * c.production.evaluation_games,
                "policy_search": generation_summary(ranks, selected),
            }
            write_json(directory / "selection" / f"generation-{update:06d}.json", selected)
            write_json(summary_path, summary)
        if world > 1:
            dist.barrier()
        summary = json.loads(summary_path.read_text())
        if rank != 0 and summary["expert_replaced"]:
            loaded, _ = load_policy(Path(summary["expert"]["path"]), torch.device("cpu"))
            teacher.load_state_dict(loaded.state_dict())
        return dict(summary)
