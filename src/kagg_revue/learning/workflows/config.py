"""Pin BC, validation selection and subsequent PPO before starting either stage."""

from pathlib import Path

from pydantic import model_validator

from kagg_revue.configuration import FrozenSettings
from kagg_revue.learning.config import Experiment
from kagg_revue.learning.matchmaking.archives import HistoricalArchive


class Workflow(FrozenSettings):
    """A fresh BC run followed by PPO from its validation-best saved actor.

    With ``attached_bc`` the BC stage was launched separately with exactly this
    protocol; the workflow only waits for it and never starts or resumes it.
    """

    output_dir: Path
    bc: Experiment
    rl: Experiment
    historical_archive: HistoricalArchive
    attached_bc: bool = False

    @model_validator(mode="after")
    def validate_stages(self) -> "Workflow":
        """Require explicit selection and prevent overlapping or resumed destinations."""
        if (
            self.output_dir.is_absolute()
            or ".." in self.output_dir.parts
            or self.output_dir.parts[:2] != ("outputs", "workflows")
            or self.bc.output_dir == self.rl.output_dir
            or self.bc.resume
            or self.rl.resume
            or not self.bc.pretraining_only
            or self.bc.demonstrations is None
            or self.bc.demonstrations.early_stopping is None
            or self.rl.pretraining_only
            or self.rl.demonstrations is not None
            or self.rl.initial_weights is not None
        ):
            raise ValueError("workflow requires fresh BC, validation selection and a PPO template")
        return self
