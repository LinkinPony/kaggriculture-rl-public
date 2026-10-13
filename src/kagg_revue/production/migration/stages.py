"""End teacher distillation at zero and resume direct-outcome PPO."""

from typing import Any

from torch import Tensor
from torch.optim import Optimizer

from kagg_revue.learning.collection.sampling import Rollout
from kagg_revue.learning.optimization.learner import Learner
from kagg_revue.policy.spatial.model import Critic
from kagg_revue.policy.spatial.work import WorkPolicy
from kagg_revue.production.migration.artifacts import at_scale
from kagg_revue.production.migration.config import MigrationSettings
from kagg_revue.production.migration.learning import Distiller


def restore_optimizer(optimizer: Optimizer, saved: dict[str, Any]) -> None:
    """Restore moments without replacing the learning rates resolved for this run."""
    rates = [group["lr"] for group in optimizer.param_groups]
    optimizer.load_state_dict(saved)
    for group, rate in zip(optimizer.param_groups, rates, strict=True):
        group["lr"] = rate


class TrainingStage:
    """Preserve student weights across objectives and checkpoint the active learner."""

    def __init__(
        self,
        config: MigrationSettings,
        student: WorkPolicy,
        critic_state: dict[str, Tensor],
        teacher: WorkPolicy | None,
        saved: dict[str, Any] | None,
    ) -> None:
        """Restore the active objective, including both PPO optimizers after switching."""
        self.config = config
        self.student = student
        self.critic_state = critic_state
        self.distiller: Distiller | None = None
        self.ppo: Learner | None = None
        if student.layout.network.time_prior:
            if teacher is None or (saved and saved.get("training_phase") == "ppo"):
                raise ValueError("distillation requires a teacher and a student with a table")
            self.distiller = Distiller(config, student, teacher)
            if saved:
                self.distiller.optimizer.load_state_dict(saved["migration_optimizer"])
        else:
            self.start_ppo(saved)

    @property
    def name(self) -> str:
        """Identify the objective used for the next actual optimizer update."""
        return "distillation" if self.distiller is not None else "ppo"

    def start_ppo(self, saved: dict[str, Any] | None = None) -> None:
        """Release the teacher and KL moments; initialize PPO from the existing WDL critic."""
        if self.ppo is not None:
            return
        if self.student.layout.network.time_prior:
            self.student.remove_prior()
        # Dropping the distiller retires its teacher, graphs, gradients and optimizer.
        self.distiller = None
        device = next(self.student.parameters()).device
        critic = Critic(self.student.layout).to(device)
        critic.load_state_dict(self.critic_state)
        self.critic_state = {}
        self.ppo = Learner(
            at_scale(self.config.production, 0.0, table=False), self.student, critic, None
        )
        if saved and saved.get("training_phase") == "ppo":
            restore_optimizer(self.ppo.actor_optimizer, saved["actor_optimizer"])
            restore_optimizer(self.ppo.critic_optimizer, saved["critic_optimizer"])

    def update(self, rollout: Rollout) -> dict[str, Any]:
        """Use exactly one objective; PPO has no teacher or distillation loss."""
        if self.distiller is not None:
            return self.distiller.update(rollout)
        assert self.ppo is not None
        return self.ppo.update(rollout)

    def state_dict(self) -> dict[str, Any]:
        """Persist the active optimizer state without retaining the retired objective."""
        if self.distiller is not None:
            return {
                "training_phase": self.name,
                "migration_optimizer": self.distiller.optimizer.state_dict(),
                "critic": self.critic_state,
            }
        assert self.ppo is not None
        return {
            "training_phase": self.name,
            "actor_optimizer": self.ppo.actor_optimizer.state_dict(),
            "critic_optimizer": self.ppo.critic_optimizer.state_dict(),
            "critic": self.ppo.critic.state_dict(),
        }
