"""Authenticate public identities and reuse the existing native opponent batch."""

from pathlib import Path
from typing import Any

from kagg_revue.artifacts.io import digest
from kagg_revue.learning.settings import RuntimeSettings
from kagg_revue.opponents.batches import create_batch
from kagg_revue.opponents.public import (
    PublicAgentRecord,
    load_public_agent_manifest,
    resolve_public_agent_path,
)
from kagg_revue.opponents.registry import trusted_runtime_identity
from kagg_revue.opponents.settings import PublicPopulation


def records(config: PublicPopulation) -> dict[str, PublicAgentRecord]:
    """Require exact reviewed sources with existing native implementations."""
    if digest(config.manifest) != config.sha256:
        raise ValueError("training script manifest differs from its declared hash")
    available = load_public_agent_manifest(config.manifest).by_id()
    selected: dict[str, PublicAgentRecord] = {name: available[name] for name in config.agents}
    for record in selected.values():
        resolve_public_agent_path(record, Path.cwd())
        if trusted_runtime_identity(record) is None:
            raise ValueError(f"training script has no authenticated native port: {record.agent_id}")
    return selected


def create_public_batch(settings: RuntimeSettings, jobs: list[tuple[int, int, str]]) -> Any:
    """Use native ParallelBatch, without any per-turn Python opponent callbacks."""
    if settings.script_population is None:
        raise ValueError("public training requires explicitly declared native scripts")
    selected = records(settings.script_population)
    if any(name not in selected for _, _, name in jobs):
        raise ValueError("batch requested an undeclared script opponent")
    return create_batch(settings, jobs)
