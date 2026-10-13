"""Legacy script panels with shared neural match compatibility imports."""

from typing import Any

from kagg_revue.evaluation.games import _complete, _summary
from kagg_revue.evaluation.neural import NeuralMatches, PairedPolicy
from kagg_revue.native.batches import paired_jobs
from kagg_revue.opponents.batches import create_batch
from kagg_revue.policy.inference import ActorRuntime
from kagg_revue.policy.spatial.model import Policy
from kagg_revue.production.config import Settings

__all__ = ["NeuralMatches", "PairedPolicy", "ScriptMatches"]


class ScriptMatches:
    """Keep one bounded actor graph across a population of full neural candidates."""

    def __init__(self, settings: Settings, policy: Policy, *, sample: bool = False) -> None:
        """Use the same decoder, batch shape and precision as the shared evaluator."""
        self.settings = settings
        self.runtime = ActorRuntime(
            policy,
            settings.evaluation_games,
            sample=sample,
            temperature=settings.ppo.temperature,
            precision=settings.precision,
            bf16_reduced_precision_reduction=settings.bf16_reduced_precision_reduction,
        )

    def run(self, seed: int) -> dict[str, Any]:
        """Run paired games against the unchanged frozen notebook ladder."""
        p = self.settings
        jobs = paired_jobs(p.evaluation_games, seed, p.opponents)
        cash, timing = _complete(p, self.runtime, create_batch(p, jobs), selfplay=False)
        result = _summary(cash, jobs, timing)
        result.update(sample=self.runtime.sample)
        return result
