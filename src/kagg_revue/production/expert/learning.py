"""Learn successful deviations while retaining the frozen search root's behavior."""

import copy
import time
from typing import Any

import torch
from torch import Tensor
from torch.nn import functional as F

from kagg_revue.learning.optimization.learner import average_gradients, global_mean
from kagg_revue.policy.spatial.work import WorkPolicy
from kagg_revue.production.expert.config import ExpertSettings
from kagg_revue.production.expert.search import SearchResult, WindowTape
from kagg_revue.production.migration.objectives import distillation_rows
from kagg_revue.production.migration.runtime import GradientBuffers, GraphReplay


def _sample(tape: WindowTape, eligible: Tensor, count: int) -> tuple[Tensor, Tensor, Tensor]:
    # Choose the physical game first: a longer winning window must not receive
    # more optimization mass merely because it contains more recorded rows.
    games = eligible.any(0).nonzero().flatten()
    selected_games = games[torch.randint(len(games), (count,), device=games.device)]
    lengths = eligible[:, selected_games].sum(0)
    slots = (torch.rand(count, device=games.device) * lengths).long()
    selected = slots * eligible.shape[1] + selected_games
    return (
        tape.observations.flatten(0, 1)[selected],
        tape.steps.flatten()[selected],
        tape.actions.flatten(0, 1)[selected].long(),
    )


class Learner:
    """One synchronized actor step per fresh search; reject an excessive actual step."""

    def __init__(self, config: ExpertSettings, student: WorkPolicy, root: WorkPolicy) -> None:
        """Reuse bounded autograd graphs and independent accumulation buffers."""
        self.config, self.student, self.root = config, student, root
        root.requires_grad_(False)
        self.parameters = list(student.parameters())
        self.optimizer = torch.optim.AdamW(
            self.parameters, lr=config.learning_rate, weight_decay=0, fused=True
        )
        self.gradients = GradientBuffers(self.parameters)
        width = config.microbatch_rows // len(config.production.devices)
        widths = {width, (config.learner_rows // len(config.production.devices)) % width} - {0}
        self.forward = GraphReplay(student, widths, config.production.precision)
        self.target = GraphReplay(root, widths, config.production.precision)

    def update(self, result: SearchResult) -> dict[str, Any]:
        """Distill only changed conditional choices from strictly improved windows."""
        started = time.perf_counter()
        config = self.config
        device = next(self.student.parameters()).device
        total_improved = global_mean(result.improved.sum().float())
        if float(total_improved) == 0:
            return {
                "actor_steps": 0,
                "reason": "no_strict_wdl_improvement",
                "learner_seconds": time.perf_counter() - started,
            }
        rows = config.learner_rows // len(config.production.devices)
        micro = config.microbatch_rows // len(config.production.devices)
        eligible = result.expert.valid & result.improved[None]
        local_has_expert = bool(eligible.any())
        # Ranks without winners still contribute retention, with zero expert mass.
        expert = _sample(
            result.expert if local_has_expert else result.baseline,
            eligible if local_has_expert else result.baseline.valid,
            rows // 2,
        )
        retention = _sample(result.baseline, result.baseline.valid, rows - rows // 2)
        observations, steps, actions = (
            torch.cat(parts) for parts in zip(expert, retention, strict=True)
        )
        is_expert = torch.zeros(rows, device=device)
        if local_has_expert:
            # Equal game mass across ranks, including unequal winner counts.
            is_expert[: rows // 2] = result.improved.sum()
        mass = global_mean(is_expert.sum()).clamp_min(1)
        self.gradients.zero()
        metrics = torch.zeros(3, device=device)
        for start in range(0, rows, micro):
            index = slice(start, start + micro)
            obs, times, chosen = observations[index], steps[index], actions[index]
            with torch.no_grad():
                target = self.target(obs, times, chosen)
            logits = self.forward(obs, times, chosen)
            fields = self.student.field_weights(chosen, times)
            changed = fields * (chosen != target.argmax(-1))
            nll = -F.log_softmax(logits.float(), -1).gather(-1, chosen[..., None]).squeeze(-1)
            deviation = (nll * changed).sum(-1) / changed.sum(-1).clamp_min(1)
            keep = distillation_rows(logits, target, fields, 1.0)
            loss = (
                deviation * is_expert[index]
            ).sum() / mass + config.retention_weight * keep.sum() / rows
            loss.backward()  # type: ignore[no-untyped-call]
            metrics += torch.stack(
                (
                    (deviation.detach() * is_expert[index]).sum() / mass,
                    keep.detach().sum() / rows,
                    (changed.sum(-1) * is_expert[index]).sum() / mass,
                )
            )
        average_gradients(self.parameters)
        norm = torch.nn.utils.clip_grad_norm_(self.parameters, 1.0, error_if_nonfinite=True)
        before = [p.detach().clone() for p in self.parameters]
        optimizer_before = copy.deepcopy(self.optimizer.state_dict())
        # Check the step after applying it, rather than merely stopping the next step.
        # A fixed retention probe is chosen before optimization and contains no search labels.
        probe = slice(rows - micro, rows)
        attempts = []
        for _ in range(config.backtrack_attempts):
            learning_rate = self.optimizer.param_groups[0]["lr"]
            self.optimizer.step()
            with torch.no_grad():
                target = self.target(observations[probe], steps[probe], actions[probe])
                logits = self.forward(observations[probe], steps[probe], actions[probe])
                fields = self.student.field_weights(actions[probe], steps[probe])
                plan_kl = distillation_rows(logits, target, fields, 1.0) * fields.sum(-1)
                divergence = float(global_mean(plan_kl.mean()))
            accepted = divergence <= config.maximum_plan_kl
            attempts.append({"learning_rate": learning_rate, "plan_kl": divergence})
            if accepted:
                break
            with torch.no_grad():
                for parameter, old in zip(self.parameters, before, strict=True):
                    parameter.copy_(old)
            # load_state_dict may alias moment tensors; keep the rollback snapshot immutable.
            self.optimizer.load_state_dict(copy.deepcopy(optimizer_before))
            for group in self.optimizer.param_groups:
                group["lr"] = learning_rate * 0.5
        torch.cuda.synchronize(device)
        values = global_mean(metrics).tolist()
        return {
            "actor_steps": int(accepted),
            "attempted_actor_steps": len(attempts),
            "step_attempts": attempts,
            "deviation_nll": values[0],
            "retention_kl_per_field": values[1],
            "changed_fields_per_expert_row": values[2],
            "gradient_norm": float(norm),
            "post_step_plan_kl": divergence,
            "rolled_back": not accepted,
            "learning_rate": self.optimizer.param_groups[0]["lr"],
            "learner_seconds": time.perf_counter() - started,
        }
