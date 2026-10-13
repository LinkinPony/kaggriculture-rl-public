"""Full-actor gradient learning from the current search expert on apprentice states."""

import time
from typing import Any, cast

import torch
from torch import Tensor, nn

from kagg_revue.learning.collection.population import script_games
from kagg_revue.learning.optimization.learner import average_gradients, global_mean
from kagg_revue.policy.inference import ActorRuntime
from kagg_revue.policy.spatial.work import WorkPolicy
from kagg_revue.production.expert.collection import StateTape, collect_states
from kagg_revue.production.expert.config import ApprenticeSettings
from kagg_revue.production.migration.objectives import distillation_rows
from kagg_revue.production.migration.runtime import GradientBuffers, GraphReplay


class ExpertLabels(nn.Module):
    """Use the shared conditional decoder to produce actions and soft targets together."""

    def __init__(self, teacher: WorkPolicy, bf16: bool) -> None:
        """Bind a frozen expert without a separate copy of neural decoding semantics."""
        super().__init__()
        self.teacher, self.bf16 = teacher, bf16

    def forward(self, observations: Tensor, steps: Tensor) -> tuple[Tensor, Tensor]:
        """Label the apprentice's observations under the expert's own action prefixes."""
        with torch.autocast("cuda", dtype=torch.bfloat16, enabled=self.bf16, cache_enabled=False):
            return self.teacher._decode(observations, steps, None, False)


class ApprenticeLearner:
    """Synchronized Adam updates of every actor parameter using bounded graph buffers."""

    def __init__(
        self, config: ApprenticeSettings, student: WorkPolicy, teacher: WorkPolicy
    ) -> None:
        """Reuse the production autograd graph and gradient accumulation primitives."""
        self.config, self.student, self.teacher = config, student, teacher
        teacher.requires_grad_(False)
        student.requires_grad_(True)
        self.parameters = list(student.parameters())
        self.optimizer = torch.optim.AdamW(
            self.parameters, lr=config.learning_rate, weight_decay=0.0, fused=True
        )
        self.gradients = GradientBuffers(self.parameters)
        micro = config.microbatch_rows // len(config.production.devices)
        self.widths = {micro, (config.learner_rows // len(config.production.devices)) % micro} - {0}
        self.forward = GraphReplay(student, self.widths, config.production.precision)
        self.targets: dict[int, nn.Module] = {}
        self.capture_seconds = 0.0

    def labels(self, observations: Tensor, steps: Tensor) -> tuple[Tensor, Tensor]:
        """Capture the single production target width, retaining no per-row Python objects."""
        width = len(steps)
        if width not in self.widths:
            raise ValueError("unplanned expert target graph width")
        if width not in self.targets:
            started = time.perf_counter()
            wrapper = ExpertLabels(self.teacher, self.config.production.precision == "bf16").eval()
            with torch.no_grad():
                self.targets[width] = cast(
                    nn.Module,
                    torch.cuda.make_graphed_callables(
                        wrapper, (observations.detach().clone(), steps.detach().clone())
                    ),
                )
            self.capture_seconds += time.perf_counter() - started
        return cast(tuple[Tensor, Tensor], self.targets[width](observations, steps))

    def update(self, tape: StateTape) -> dict[str, Any]:
        """Minimize expert KL, then report real optimizer participation and parameter change."""
        started = time.perf_counter()
        c = self.config
        world = len(c.production.devices)
        rows, micro = c.learner_rows // world, c.microbatch_rows // world
        device = tape.steps.device
        encoder_before = {
            n: p.detach().clone()
            for n, p in self.student.named_parameters()
            if n.startswith("encoder.")
        }
        totals = torch.zeros(3, device=device)
        norms = []
        for _ in range(c.learner_steps):
            # Sampling with replacement uses equal physical-game mass, independent of WDL.
            indices = torch.multinomial(tape.weights, rows, replacement=True)
            self.gradients.zero()
            for index in torch.split(indices, micro):
                observations, steps = tape.observations[index], tape.steps[index]
                with torch.no_grad():
                    actions, target = self.labels(observations, steps)
                logits = self.forward(observations, steps, actions)
                fields = self.student.field_weights(actions, steps)
                losses = distillation_rows(logits, target, fields, c.temperature)
                loss = losses.sum() / rows
                loss.backward()  # type: ignore[no-untyped-call]
                with torch.no_grad():
                    totals += torch.stack(
                        (
                            losses.sum(),
                            ((logits.argmax(-1) == actions) * fields).sum(),
                            fields.sum(),
                        )
                    )
                del logits, losses, loss, target
            average_gradients(self.parameters)
            norm = torch.nn.utils.clip_grad_norm_(self.parameters, 1.0, error_if_nonfinite=True)
            norms.append(float(norm))
            self.optimizer.step()
        totals = global_mean(totals)
        encoder_delta = torch.stack(
            [
                (p.detach() - encoder_before[n]).float().square().sum()
                for n, p in self.student.named_parameters()
                if n in encoder_before
            ]
        ).sum()
        torch.cuda.synchronize(device)
        return {
            "actor_steps": c.learner_steps,
            "teacher_kl_loss": float(totals[0]) / (rows * c.learner_steps),
            "conditional_action_agreement": float(totals[1] / totals[2].clamp_min(1)),
            "maximum_gradient_norm": max(norms),
            "encoder_parameter_delta_l2": float(encoder_delta.sqrt()),
            "learner_seconds": time.perf_counter() - started,
            "learning_rate": self.optimizer.param_groups[0]["lr"],
        }


def fit_round(
    config: ApprenticeSettings,
    runtime: ActorRuntime,
    learner: ApprenticeLearner,
    rank: int,
    update: int,
) -> dict[str, Any]:
    """Collect and fit only when the accepted expert has an unused learning budget."""
    from kagg_revue.production.expert.telemetry import progress

    p, directory = config.production, config.production.output_dir
    games = p.ppo.games_per_update // len(p.devices)
    progress(directory, update, rank, "collect", 0, 1)
    seed = config.collection_seed + (update - 1) * p.ppo.games_per_update + rank * games
    tape = collect_states(
        p, runtime, [seed + i // 2 for i in range(games)], config.observations_per_trajectory
    )
    progress(directory, update, rank, "learn", 0, config.learner_steps)
    optimization = learner.update(tape)
    started = time.perf_counter()
    path = directory / "data" / f"update-{update:06d}-rank-{rank}.npz"
    tape.save(path)
    selfplay = games - script_games(p, games)
    return {
        "rollout": tape.timing,
        "optimization": optimization,
        "data_seconds": time.perf_counter() - started,
        "data": str(path),
        "data_rows": len(tape.steps),
        "mean_cash": float(
            (tape.cash[:selfplay].mean(1).sum() + tape.cash[selfplay:, 0].sum()) / games
        ),
    }
