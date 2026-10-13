"""Full-checkpoint unit-task initialization invariants."""

from pathlib import Path
from types import SimpleNamespace
from typing import cast

import pytest

from kagg_revue.rl.tasks.config import TaskRlSettings
from kagg_revue.rl.tasks.train import _validate_source_actor


def _settings() -> TaskRlSettings:
    return cast(
        TaskRlSettings,
        SimpleNamespace(
            initial_actor=None,
            initial_task_checkpoint=Path("synthetic-complete-checkpoint.pt"),
        ),
    )


def test_complete_checkpoint_keeps_scratch_actor_provenance() -> None:
    source = {
        "kind": "random_from_seed",
        "actor_encoder_version": "synthetic-encoder",
        "action_keys": ["synthetic-action"],
    }

    assert _validate_source_actor(source, _settings()) == source


def test_complete_checkpoint_requires_runtime_actor_provenance() -> None:
    with pytest.raises(ValueError, match="runtime provenance"):
        _validate_source_actor({"kind": "random_from_seed"}, _settings())
