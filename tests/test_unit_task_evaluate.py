"""Held-out unit-task evaluation population invariants."""

from pathlib import Path
from types import SimpleNamespace
from typing import cast

from kagg_revue.core.backend import BackendApi
from kagg_revue.rl.tasks.config import TaskRlSettings
from kagg_revue.rl.tasks.evaluate import _opponent_factories


class _EmptyManifest:
    """Synthetic public population for a deterministic-only evaluation."""

    def by_id(self) -> dict[str, object]:
        """Return no public notebook records."""
        return {}


class _Backend:
    """Minimal backend surface used while resolving opponent factories."""

    def load_public_agent_manifest(self, _path: Path) -> _EmptyManifest:
        """Return the synthetic frozen population."""
        return _EmptyManifest()


def test_evaluation_population_is_independent_from_self_play_training() -> None:
    settings = SimpleNamespace(
        opponents=("self_play",),
        evaluation_opponents=("deterministic_incumbent",),
        public_agent_manifest=Path("synthetic-manifest.json"),
    )

    factories, identities, public_count = _opponent_factories(
        cast(BackendApi, _Backend()),
        cast(TaskRlSettings, settings),
    )

    assert tuple(factories) == ("deterministic_incumbent",)
    assert identities == {"deterministic_incumbent": {"kind": "deterministic_incumbent"}}
    assert public_count == 0
