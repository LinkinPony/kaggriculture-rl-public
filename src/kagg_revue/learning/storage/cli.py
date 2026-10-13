"""Explicit stopped-run migration and checkpoint cleanup with Hydra configuration."""

import fcntl
import json
from contextlib import ExitStack
from pathlib import Path
from typing import Literal

import hydra
from omegaconf import DictConfig, OmegaConf
from pydantic import model_validator

from kagg_revue.configuration import FrozenSettings
from kagg_revue.learning.storage import cleanup
from kagg_revue.learning.storage.artifacts import resolve
from kagg_revue.learning.storage.migration import migrate


class Storage(FrozenSettings):
    """Bind destructive cleanup to an explicit nonempty list of protected experiments."""

    action: Literal["migrate", "plan", "apply"] = "plan"
    runs: tuple[Path, ...]
    report: Path

    @model_validator(mode="after")
    def validate_paths(self) -> "Storage":
        """Restrict the operation and its audit records to repository output directories."""
        if not self.runs or len(set(self.runs)) != len(self.runs):
            raise ValueError("specify distinct retained runs")
        for path in (*self.runs, self.report):
            if path.is_absolute() or ".." in path.parts or path.parts[:1] != ("outputs",):
                raise ValueError("storage operations require repository-owned outputs paths")
        if any(path.parts[:2] != ("outputs", "learning") for path in self.runs):
            raise ValueError("retained runs must be learning experiments")
        return self


def run(config: Storage) -> None:
    """Hold exclusive training and recovery locks through migration or exact deletion."""
    config.report.mkdir(parents=True, exist_ok=True)
    with ExitStack() as stack:
        for directory in sorted(config.runs):
            for name in ("recovery.lock", "run.lock"):
                stream = stack.enter_context((directory / name).open("a"))
                fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        if config.action == "migrate":
            shared: dict[str, tuple[Path, str]] = {}
            for revisions in Path("outputs/learning").glob("*/storage-revisions"):
                # Only already migrated runs participate; no unrelated weights are loaded.
                ledger = revisions.parent / "state.json"
                state = json.loads(ledger.read_text())
                if not state.get("storage_history"):
                    continue
                for member, record in state.get("inference_artifacts", {}).items():
                    shared[record["source_sha256"]] = (
                        resolve(ledger.parent, state, member),
                        record["sha256"],
                    )
            for directory in config.runs:
                print(json.dumps(migrate(directory, shared)), flush=True)
            return
        planned = cleanup.plan(config.runs, config.report)
        result = cleanup.apply(planned, config.report) if config.action == "apply" else planned
        print(json.dumps({key: value for key, value in result.items() if key != "candidates"}))


@hydra.main(
    version_base=None,
    config_path=str(Path(__file__).resolve().parents[4] / "configs"),
    config_name="learning_storage",
)
def main(configuration: DictConfig) -> None:
    """Resolve an explicit storage action; default to a non-destructive plan."""
    run(Storage.model_validate(OmegaConf.to_container(configuration.storage, resolve=True)))


if __name__ == "__main__":
    main()
