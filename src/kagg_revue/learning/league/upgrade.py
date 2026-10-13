"""Publish qualified execution code at a joint checkpoint without changing the recipe."""

import fcntl
import os
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
from kagg_revue.learning.league.revision import stopped_state
from kagg_revue.learning.performance.artifacts import archive_source
from kagg_revue.learning.pretraining.config import Demonstrations
from kagg_revue.learning.recovery.archive import materialize
from kagg_revue.learning.recovery.cli import Recovery


class Upgrade(Recovery):
    """Require integration evidence for the exact source and stopped checkpoint."""

    qualification: Path
    qualification_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")


def upgrade(config: Upgrade) -> dict[str, Any]:
    """Archive the old identity and install only the authenticated implementation."""
    root = config.run
    with (root / "run.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        state = stopped_state(root)
        identity = artifacts.source_identity()
        if state["source"] == identity["source_sha256"]:
            raise ValueError("this execution source is already active")
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
            "protocol": state["protocol"],
        }
        if any(qualified.get(key) != value for key, value in expected.items()):
            raise ValueError("qualification must bind this checkpoint, source and unchanged recipe")
        children = {
            name: orjson.loads((root / name / "state.json").read_bytes()) for name in MEMBERS
        }
        for name, child in children.items():
            if child["source"] != state["source"] or child["native"] != identity["native_sha256"]:
                raise ValueError("league members must share the original source and native engine")
            recipe = League.model_validate(state["protocol"]).member(
                name, committed=Demonstrations.model_validate(child["protocol"]["demonstrations"])
            )
            for member in child["members"]:
                artifacts.member_path(recipe, child, member)
        Path("tmp").mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(prefix="league-upgrade-", dir="tmp") as temporary:
            materialize(root / "a", children["a"], Path(temporary))
        index = f"{len(state.get('runtime_history', [])) + 1:04d}"
        revision = root / "runtime-revisions" / index
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
            "protocol": state["protocol"],
            "revision": str(revision.relative_to(root)),
            "optimizer_rng_and_bc_preserved": True,
        }
        for name, child in children.items():
            target = root / name / "runtime-revisions" / index
            target.mkdir(parents=True, exist_ok=False)
            write_json(target / "previous-state.json", child)
            for filename in ("source.json", "source.tar.gz"):
                os.link(revision / filename, target / filename)
        try:
            for name, child in children.items():
                write_json(
                    root / name / "state.json",
                    {
                        **child,
                        "source": identity["source_sha256"],
                        "source_directory": f"runtime-revisions/{index}",
                    },
                )
            write_json(
                root / "league.json",
                {
                    **state,
                    "source": identity["source_sha256"],
                    "runtime_history": [*state.get("runtime_history", []), transition],
                },
            )
        except BaseException:
            for name, child in children.items():
                write_json(root / name / "state.json", child)
            write_json(root / "league.json", state)
            raise
        write_json(revision / "transition.json", transition)
        return transition


@hydra.main(version_base=None, config_path="../../../../configs", config_name="league_upgrade")
def main(configuration: DictConfig) -> None:
    """Apply execution changes only after full-size training and archived recovery pass."""
    config = Upgrade.model_validate(OmegaConf.to_container(configuration.upgrade, resolve=True))
    print(orjson.dumps(upgrade(config)).decode(), flush=True)


if __name__ == "__main__":
    main()
