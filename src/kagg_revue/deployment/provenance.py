"""Authenticate deployment inputs for random and transferred policy roots."""

import json
from pathlib import Path
from typing import Any

from kagg_revue.learning.config import Experiment
from kagg_revue.learning.pretraining import weights


def load_run(directory: Path) -> tuple[Experiment, dict[str, Any]]:
    """Validate the declared root and its preserved parent before loading a member."""
    state = json.loads((directory / "state.json").read_text())
    if not weights.valid_root(state) or state["protocol"]["output_dir"] != str(directory):
        raise ValueError("deployment requires an authenticated policy-root ledger")
    experiment = Experiment.model_validate(state["protocol"])
    weights.verify(directory, state)
    return experiment, state
