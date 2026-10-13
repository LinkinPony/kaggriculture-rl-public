"""Predecessor PFSP evidence seeds only unmet opponents and replays at resume."""

import copy
import json
from pathlib import Path
from typing import Any

import pytest

from kagg_revue.artifacts.io import digest
from kagg_revue.learning.config import Experiment, Population
from kagg_revue.learning.matchmaking.archives import HistoricalArchive
from kagg_revue.learning.matchmaking.config import Inheritance, Mastery, Pfsp
from kagg_revue.learning.matchmaking.inheritance import inherit
from kagg_revue.learning.matchmaking.migration import restored_statistics
from kagg_revue.learning.matchmaking.scheduler import SamplerState
from kagg_revue.learning.matchmaking.statistics import Inherited, Record
from kagg_revue.learning.state import protocol

PFSP = Pfsp(mastery=Mastery(), inheritance=Inheritance(discount=0.5))


def _record(**values: Any) -> dict[str, Any]:
    return Record(**values).model_dump(mode="json", exclude_none=True)


def _donor(name: str, update: int, records: dict[str, Any]) -> HistoricalArchive:
    run = Path("outputs/learning") / name
    run.mkdir(parents=True)
    config = Experiment(output_dir=run, population=Population(pfsp=PFSP))
    ledger = {
        "protocol": protocol(config),
        "completed_update": update,
        "pfsp": {"version": 1, "started_update": 1, "last_update": update, "records": records},
    }
    (run / "state.json").write_text(json.dumps(ledger))
    return HistoricalArchive(run=run, state_sha256=digest(run / "state.json"))


def _target(update: int, own: dict[str, Any]) -> tuple[Experiment, dict[str, Any]]:
    config = Experiment(
        output_dir=Path("outputs/learning/target"), population=Population(pfsp=PFSP)
    )
    members = {f"{name}.pt": name * 64 for name in "abcd"}
    state = {
        "completed_update": update,
        "members": members,
        "pool": list(members),
        "pfsp": {"version": 1, "started_update": 1, "last_update": update, "records": own},
    }
    return config, state


def test_nearest_discounted_evidence_keeps_mastery_until_met(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Own records win, nearer donors win, and a real encounter re-decides mastery."""
    monkeypatch.chdir(tmp_path)
    key = {name: f"history:{name * 64}" for name in "abcd"}
    near = _donor(
        "near",
        590,
        {
            key["a"]: _record(wins=64, effective_games=64, effective_score=64, last_update=590),
            key["b"]: _record(
                wins=58, losses=6, effective_games=64, effective_score=58, last_update=462
            ),
        },
    )
    far = _donor(
        "far",
        1729,
        {
            key["a"]: _record(losses=64, effective_games=64, last_update=1729),
            key["d"]: _record(wins=64, effective_games=64, effective_score=64, last_update=1729),
        },
    )
    own = {key["c"]: _record(losses=64, effective_games=64, last_update=300)}
    config, state = _target(300, copy.deepcopy(own))
    report = inherit(config, state, (near, far))
    records = {k: Record.model_validate(v) for k, v in state["pfsp"]["records"].items()}
    assert report["inherited"] == 3 and report["inherited_mastered"] == 2
    assert state["pfsp"]["records"][key["c"]] == own[key["c"]]
    assert (records[key["a"]].effective_games, records[key["a"]].mastered(PFSP)) == (32, True)
    # One half-life of donor decay, then one generation of discount.
    assert records[key["b"]].effective_games == pytest.approx(16)
    assert not records[key["b"]].mastered(PFSP)
    assert records[key["d"]].effective_games == pytest.approx(16)
    assert records[key["d"]].inherited is not None and records[key["d"]].mastered(PFSP)
    assert records[key["a"]].wins == 0 and records[key["a"]].last_update == 300
    records[key["a"]].observe({"games": 64, "wins": 50, "ties": 0, "losses": 14}, 301, PFSP)
    assert not records[key["a"]].mastered(PFSP)


def test_chained_inheritance_keeps_the_original_observation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Unmet inherited evidence compounds its discount but not its mastery source."""
    monkeypatch.chdir(tmp_path)
    key = "history:" + "a" * 64
    origin = Inherited(run="outputs/learning/origin", update=100, games=64, score=64)
    donor = _donor(
        "donor",
        590,
        {key: _record(effective_games=32, effective_score=32, last_update=590, inherited=origin)},
    )
    config, state = _target(0, {})
    inherit(config, state, (donor,))
    record = Record.model_validate(state["pfsp"]["records"][key])
    assert record.inherited == origin and record.effective_games == pytest.approx(16)
    assert record.mastered(PFSP)


def test_boundary_checkpoint_replays_the_registered_event(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Resume equality holds without rewriting checkpoint statistics or old records."""
    monkeypatch.chdir(tmp_path)
    key = "history:" + "a" * 64
    donor = _donor(
        "donor",
        590,
        {key: _record(wins=64, effective_games=64, effective_score=64, last_update=590)},
    )
    own = {"history:" + "c" * 64: _record(wins=3, losses=61, effective_games=64, effective_score=3)}
    config, state = _target(300, own)
    saved = copy.deepcopy(state["pfsp"])
    inherit(config, state, (donor,))
    assert saved != state["pfsp"] and restored_statistics(saved, state) == state["pfsp"]
    dumped = SamplerState.model_validate(state["pfsp"]).model_dump(mode="json", exclude_none=True)
    assert dumped == state["pfsp"]
    assert "inherited" not in dumped["records"]["history:" + "c" * 64]
    later = {**copy.deepcopy(state["pfsp"]), "last_update": 301}
    assert restored_statistics(later, state) == later
