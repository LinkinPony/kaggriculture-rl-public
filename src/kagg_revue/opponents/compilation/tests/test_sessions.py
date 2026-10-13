"""Repeated observations, new episodes and fork ownership for compiled policies."""

from pathlib import Path
from typing import Any

import pytest

from kagg_revue.native import _revue_native as native
from kagg_revue.opponents.compilation.diagnostics import source_diagnostics, stable
from kagg_revue.opponents.compilation.sources import CANDIDATES
from kagg_revue.opponents.portfolios.native import create_native_session, native_action
from kagg_revue.opponents.public import PublicAgentRuntime, load_public_agent_manifest


def test_native_closure_lifetimes() -> None:
    """Release lambda aliases and retain captured values only while closures live."""
    assert native.native_compiled_closure_lifetimes()


def test_dictionary_get_preserves_binding_and_attribute_errors() -> None:
    """Observe argument-side mutations without rebinding an already captured method."""
    assert native.native_compiled_dictionary_get()


@pytest.mark.parametrize("name", [candidate.agent_id for candidate in CANDIDATES])
def test_repeated_calls_episode_reset_and_fork_ownership(name: str) -> None:
    """Keep source reset behavior while a divergent child owns all mutable state."""
    manifest = Path("data/external/kaggriculture-public-native-20260921/manifest.json")
    record = load_public_agent_manifest(manifest).by_id()[name]
    source = PublicAgentRuntime(record, Path.cwd(), native.Engine(1, {}).configuration)
    session = create_native_session(name)
    for seat in (0, 1):
        engine = native.Engine(1860914300 + seat, {})
        for step in range(146):
            for _ in range(2 if step in (0, 144) else 1):
                expected = source.act(engine.observation(seat))
                actual = native_action(session, engine, seat)
                assert native.canonical_opponent_action(actual, 10) == (
                    native.canonical_opponent_action(expected, 10)
                )
                assert stable(native.native_opponent_diagnostics(session)) == (
                    source_diagnostics(source)
                )
            if step == 144:
                before = native.native_opponent_diagnostics(session)
                child = session.clone()
                native_action(child, engine, seat)
                assert native.native_opponent_diagnostics(session) == before
            actions: list[dict[str, Any]] = [{}, {}]
            actions[seat] = actual
            engine.step(*actions)
