"""Qualified self-play transitions preserving the complete three-model lineage."""

import copy
import fcntl
import os
import shutil
import tempfile
import time
from pathlib import Path
from typing import Any

import hydra
import orjson
from omegaconf import DictConfig, OmegaConf
from pydantic import Field

from kagg_revue.artifacts.io import digest, write_json
from kagg_revue.learning import state as artifacts
from kagg_revue.learning.league.config import MEMBERS, League
from kagg_revue.learning.performance.artifacts import archive_source
from kagg_revue.learning.pretraining.config import Demonstrations
from kagg_revue.learning.recovery.archive import materialize
from kagg_revue.learning.recovery.cli import Recovery


def read_state(directory: Path) -> dict[str, Any]:
    """Read a small joint league ledger."""
    result: dict[str, Any] = orjson.loads((directory / "league.json").read_bytes())
    return result


def changed_config(state: dict[str, Any], selfplay_games: int) -> League:
    """Trade mutual games for self-play while preserving total games, seeds and tensors."""
    previous = League.model_validate(state["protocol"])
    total = previous.games_per_pair + previous.selfplay_games_per_member
    if not 0 < selfplay_games < total:
        raise ValueError("the revised league must contain both mutual matches and self-play")
    return League.model_validate(
        {
            **state["protocol"],
            "games_per_pair": total - selfplay_games,
            "selfplay_games_per_member": selfplay_games,
        }
    )


def stopped_state(directory: Path) -> dict[str, Any]:
    """Require a clean, unfinished joint checkpoint and authenticate its hash."""
    status = orjson.loads((directory / "run-status.json").read_bytes())
    if status["status"] != "stopped":
        raise ValueError("finish the active round and stop before changing the league")
    try:
        os.kill(status["pid"], 0)
    except ProcessLookupError:
        pass
    else:
        raise RuntimeError("the recorded training process remains live")
    state = read_state(directory)
    if (
        state["schema"] != "three-specialist-league-v1"
        or state["protocol"]["experiment"]["output_dir"] != str(directory)
        or not 0 < state["completed_update"] < state["protocol"]["experiment"]["updates"]
        or status["completed_update"] != state["completed_update"]
        or digest(directory / state["latest"]) != state["checkpoints"][state["latest"]]
    ):
        raise ValueError("league checkpoint, protocol and clean stop must agree")
    return state


def qualification_copy(source: Path, destination: Path, selfplay_games: int) -> League:
    """Link immutable checkpoints into an isolated test branch with fresh training seeds."""
    state = stopped_state(source)
    proposed = changed_config(state, selfplay_games)
    identity = artifacts.source_identity()
    destination.mkdir(parents=True, exist_ok=False)
    original = copy.deepcopy(state)
    proposed = League.model_validate(
        {
            **proposed.protocol(),
            "experiment": {
                **proposed.protocol()["experiment"],
                "output_dir": str(destination),
                "train_seed": 3790000000,
            },
        }
    )
    for name in MEMBERS:
        child = orjson.loads((source / name / "state.json").read_bytes())
        target = destination / name
        target.mkdir()
        for relative in (*child["members"], child["native_artifact"]):
            old = source / name / relative
            expected = child["members"].get(relative, child["native"])
            if digest(old) != expected:
                raise ValueError("qualification source artifact differs from its ledger")
            new = target / relative
            new.parent.mkdir(parents=True, exist_ok=True)
            os.link(old, new)
        child.update(
            protocol=artifacts.protocol(
                proposed.member(
                    name,
                    committed=Demonstrations.model_validate(child["protocol"]["demonstrations"]),
                )
            ),
            source=identity["source_sha256"],
            source_directory=".",
        )
        archive_source(target, identity)
        write_json(target / "state.json", child)
        write_json(target / "resolved-config.json", child["protocol"])
        shutil.copy2(source / name / "learning-progress.json", target / "learning-progress.json")
    (destination / state["latest"]).parent.mkdir(parents=True, exist_ok=True)
    os.link(source / state["latest"], destination / state["latest"])
    state.update(
        protocol=proposed.protocol(),
        source=identity["source_sha256"],
        checkpoints={state["latest"]: state["checkpoints"][state["latest"]]},
        qualification_parent={"run": str(source), "checkpoint": original["latest"]},
        population_history=[
            *state.get("population_history", []),
            {
                "effective_from_update": state["completed_update"] + 1,
                "qualification_only": True,
            },
        ],
    )
    write_json(destination / "league.json", state)
    write_json(destination / "resolved-config.json", state["protocol"])
    for filename in ("metrics.jsonl", "run-status.json", "league-progress.json"):
        shutil.copy2(source / filename, destination / filename)
    return proposed


class SelfplayChange(Recovery):
    """Bind the requested composition to checkpoint-specific integration evidence."""

    selfplay_games_per_member: int = Field(default=32, gt=0)
    qualification: Path
    qualification_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")


def change(config: SelfplayChange) -> dict[str, Any]:
    """Publish new source archives and sampling controls without rewriting any weights."""
    root = config.run
    with (root / "run.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        state = stopped_state(root)
        proposed = changed_config(state, config.selfplay_games_per_member)
        identity = artifacts.source_identity()
        if proposed.protocol() == state["protocol"]:
            raise ValueError("this self-play composition is already active")
        if digest(config.qualification) != config.qualification_sha256:
            raise ValueError("qualification report fingerprint changed")
        qualified = orjson.loads(config.qualification.read_bytes())
        expected = {
            "passed": True,
            "run_id": state["run_id"],
            "completed_update": state["completed_update"],
            "checkpoint_sha256": state["checkpoints"][state["latest"]],
            "source_state_sha256": digest(root / "league.json"),
            "source_sha256": identity["source_sha256"],
            "native_sha256": identity["native_sha256"],
            "protocol": proposed.protocol(),
        }
        if any(qualified.get(key) != value for key, value in expected.items()):
            raise ValueError("qualification does not bind this checkpoint, source and composition")
        children = {
            name: orjson.loads((root / name / "state.json").read_bytes()) for name in MEMBERS
        }
        for name, child in children.items():
            if child["source"] != state["source"] or child["native"] != identity["native_sha256"]:
                raise ValueError("league members must share the original source and native engine")
            previous = League.model_validate(state["protocol"]).member(
                name, committed=Demonstrations.model_validate(child["protocol"]["demonstrations"])
            )
            for member in child["members"]:
                artifacts.member_path(previous, child, member)
        Path("tmp").mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(prefix="league-revision-", dir="tmp") as temporary:
            materialize(root / "a", children["a"], Path(temporary))
        index = f"{len(state.get('population_history', [])) + 1:04d}"
        revision = root / "population-revisions" / index
        revision.mkdir(parents=True, exist_ok=False)
        archive_source(revision, identity)
        write_json(revision / "previous-league.json", state)
        write_json(revision / "qualification.json", qualified)
        os.link(root / state["latest"], revision / "checkpoint.pt")
        transition = {
            "time": time.time(),
            "effective_from_update": state["completed_update"] + 1,
            "checkpoint_sha256": state["checkpoints"][state["latest"]],
            "previous_source": state["source"],
            "source": identity["source_sha256"],
            "previous_protocol": state["protocol"],
            "protocol": proposed.protocol(),
            "revision": str(revision.relative_to(root)),
            "optimizer_rng_and_bc_preserved": True,
            "selfplay_seat_weight": 0.5,
        }
        for name, child in children.items():
            target = root / name / "population-revisions" / index
            target.mkdir(parents=True, exist_ok=False)
            write_json(target / "previous-state.json", child)
            for filename in ("source.json", "source.tar.gz"):
                os.link(revision / filename, target / filename)
        previous_state = copy.deepcopy(state)
        try:
            for name, child in children.items():
                updated = {
                    **child,
                    "source": identity["source_sha256"],
                    "source_directory": f"population-revisions/{index}",
                }
                write_json(root / name / "state.json", updated)
            state.update(
                protocol=proposed.protocol(),
                source=identity["source_sha256"],
                population_history=[*state.get("population_history", []), transition],
            )
            write_json(root / "resolved-config.json", state["protocol"])
            write_json(root / "league.json", state)
        except BaseException:
            for name, child in children.items():
                write_json(root / name / "state.json", child)
            write_json(root / "resolved-config.json", previous_state["protocol"])
            write_json(root / "league.json", previous_state)
            raise
        write_json(revision / "transition.json", transition)
        return transition


@hydra.main(
    version_base=None, config_path="../../../../configs", config_name="learning_league_change"
)
def main(configuration: DictConfig) -> None:
    """Apply the explicitly requested self-play addition after integration qualification."""
    config = SelfplayChange.model_validate(
        OmegaConf.to_container(configuration.change, resolve=True)
    )
    print(orjson.dumps(change(config)).decode(), flush=True)


if __name__ == "__main__":
    main()
