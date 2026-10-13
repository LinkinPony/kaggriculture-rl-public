"""Independent frozen small-policy opponents for throughput experiments only."""

from pathlib import Path

from kagg_revue.artifacts.io import digest
from kagg_revue.learning.collection.archive import PopulationCache
from kagg_revue.learning.config import Experiment
from kagg_revue.learning.initialization import random_policy
from kagg_revue.learning.settings import RuntimeSettings
from kagg_revue.policy.checkpoints import save_policy
from kagg_revue.policy.contracts import ContractLayout


def create_peer(
    config: Experiment, settings: RuntimeSettings, output: Path
) -> tuple[PopulationCache, str, str]:
    """Archive a fresh same-architecture opponent, with no inherited PFSP evidence."""
    checkpoint = output.with_suffix(".opponent.pt")
    run_id = f"throughput-only-{output.stem}"
    actor = random_policy(ContractLayout.resolve(settings), config.seed + 19, config.exploration)
    save_policy(checkpoint, actor, settings, lineage={"run_id": run_id})
    identity = digest(checkpoint)
    state = {"run_id": run_id, "members": {checkpoint.name: identity}}
    cache = PopulationCache(config.model_copy(update={"output_dir": output.parent}), state)
    return cache, checkpoint.name, identity
