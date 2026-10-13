"""Enable PFSP defaults for new training without changing archived protocols."""

import json
from typing import Any

from kagg_revue.configuration import FrozenSettings
from kagg_revue.learning.config import Experiment
from kagg_revue.learning.matchmaking.config import Inheritance, Mastery

DEFAULTS: dict[str, type[FrozenSettings]] = {"mastery": Mastery, "inheritance": Inheritance}


def training_defaults(config: Experiment) -> Experiment:
    """Resolve omitted PFSP defaults at launch; restore saved values on continuation.

    Raw protocol parsing keeps its historical meaning. New training enables the
    mastery review budget and discounted evidence inheritance unless explicitly
    configured, including null. A bootstrap followed by a resume uses the
    effective values saved at bootstrap.
    """
    options = config.population.pfsp
    if options is None:
        return config
    missing = [name for name in DEFAULTS if name not in options.model_fields_set]
    if not missing:
        return config
    update: dict[str, Any] = {}
    if config.resume:
        saved = json.loads((config.output_dir / "state.json").read_text())
        previous = saved["protocol"]["population"].get("pfsp") or {}
        for name in missing:
            value = previous.get(name)
            update[name] = DEFAULTS[name].model_validate(value) if value is not None else None
    else:
        update = {name: DEFAULTS[name]() for name in missing}
    return config.model_copy(
        update={
            "population": config.population.model_copy(
                update={"pfsp": options.model_copy(update=update)}
            )
        }
    )
