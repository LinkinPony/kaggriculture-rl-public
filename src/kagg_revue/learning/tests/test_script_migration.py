"""Manifest extensions preserve evidence only for authenticated identical policies."""

from copy import deepcopy
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest

from kagg_revue.learning.matchmaking.migration import preserve_script_evidence, restored_statistics
from kagg_revue.opponents.public import load_public_agent_manifest
from kagg_revue.opponents.settings import PublicPopulation


def test_manifest_extension_preserves_only_unchanged_evidence() -> None:
    """Moving identical scripts retains all counts; a changed source starts fresh."""
    manifest = Path("data/external/kaggriculture-public-native-20260916/manifest.json")
    records = load_public_agent_manifest(manifest).by_id()
    old = PublicPopulation(
        manifest=manifest, sha256="a" * 64, agents=("ahmed_v45", "metacounter_r1"), fraction=0
    )
    new = old.model_copy(update={"sha256": "b" * 64})
    following = dict(records)
    following["metacounter_r1"] = records["metacounter_r1"].model_copy(update={"sha256": "c" * 64})
    source = f"script:{old.sha256}:ahmed_v45"
    target = f"script:{new.sha256}:ahmed_v45"
    state: dict[str, Any] = {
        "completed_update": 91,
        "pfsp": {
            "records": {
                source: {"wins": 14, "losses": 7, "last_update": 90},
                f"script:{old.sha256}:metacounter_r1": {"wins": 3},
                "history:unchanged": {"wins": 2},
            }
        },
    }
    before = deepcopy(state)
    with patch(
        "kagg_revue.learning.collection.public.records", side_effect=[records, following]
    ):
        preserve_script_evidence(state, old, new)
    assert state["pfsp"]["records"][target] == before["pfsp"]["records"][source]
    assert source not in state["pfsp"]["records"]
    assert f"script:{new.sha256}:metacounter_r1" not in state["pfsp"]["records"]
    assert state["pfsp"]["records"]["history:unchanged"] == {"wins": 2}
    assert len(state["script_identity_history"][0]["moved"]) == 1
    conflict = deepcopy(before)
    conflict["pfsp"]["records"][target] = {"wins": 99}
    snapshot = deepcopy(conflict)
    with (
        patch(
            "kagg_revue.learning.collection.public.records", side_effect=[records, following]
        ),
        pytest.raises(ValueError, match="already has evidence"),
    ):
        preserve_script_evidence(conflict, old, new)
    assert conflict == snapshot


def test_checkpoint_rekeys_only_at_registered_boundary() -> None:
    """Preserve old checkpoint bytes and reject incompatible migration histories."""
    saved = {"last_update": 155, "records": {"old": {"wins": 11, "losses": 7}}}
    before = deepcopy(saved)
    state = {
        "script_identity_history": [
            {"completed_update": 155, "moved": [{"source": "old", "target": "new"}]}
        ]
    }
    expected = {"last_update": 155, "records": {"new": {"wins": 11, "losses": 7}}}
    assert restored_statistics(saved, state) == expected
    assert saved == before
    later = {**expected, "last_update": 156}
    assert restored_statistics(later, state) == later
    with pytest.raises(ValueError, match="cannot replay"):
        restored_statistics(expected, state)
