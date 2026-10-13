"""Index replay restart candidates without creating imitation action targets."""

import hashlib
import json
import zipfile
from collections import Counter
from pathlib import Path
from typing import Any

import hydra
import orjson
from omegaconf import DictConfig, OmegaConf
from pydantic import model_validator

from kagg_revue.artifacts.io import digest, write_json
from kagg_revue.configuration import FrozenSettings


class Index(FrozenSettings):
    """Persistent source references and a separate generated coverage report."""

    archive: Path
    output_dir: Path
    report_dir: Path
    module_version: str = "1.32.7"
    additional_steps: tuple[int, ...] = ()

    @model_validator(mode="after")
    def validate_paths(self) -> "Index":
        """Keep source data reusable and analysis products out of that directory."""
        for path, prefix in (
            (self.archive, ("data", "external")),
            (self.output_dir, ("data", "external")),
            (self.report_dir, ("outputs",)),
        ):
            if path.is_absolute() or ".." in path.parts or path.parts[: len(prefix)] != prefix:
                raise ValueError("state indexes use data/external; analysis reports use outputs")
        return self


def partition(seed: int) -> str:
    """Group both seats and duplicate environment seeds in a stable 80/10/10 split."""
    key = hashlib.sha256(f"replay-state-v1:{seed}".encode()).digest()
    bucket = int.from_bytes(key[:8], "big") % 10
    return "train" if bucket < 8 else "selection" if bucket == 8 else "confirmation"


def describe(observation: dict[str, Any], seat: int) -> dict[str, int | float]:
    """Measure state coverage using recorded state only, with no future outcomes."""
    farm = observation["farms"][seat]
    private = observation["private"]
    tiles = [tile for row in farm["tiles"] for tile in row if isinstance(tile, dict)]
    return {
        "cash": farm["money"],
        "units": 1 + len(farm["hands"]),
        "plants": sum(tile.get("kind") == "PLANT" for tile in tiles),
        "animals": sum(bool(tile.get("animal")) for tile in tiles),
        "positive_yield_tiles": sum(tile.get("yield_units", 0) > 0 for tile in tiles),
        "shed_items": sum(private["shed"].values()),
        "carried_items": sum(sum(inventory.values()) for inventory in private["inventories"]),
        "seeds": sum(private["seeds"].values()),
    }


def run(config: Index) -> None:
    """Build immutable references to every noninitial, nonterminal day boundary.

    These are restart candidates, not trusted engine snapshots. A future
    training loader must replay the exact official prefix, reconstruct public
    history, and check the resulting state before collecting any policy data.
    """
    target = config.output_dir / "candidates.jsonl"
    if target.exists() or (config.output_dir / "manifest.json").exists():
        raise FileExistsError("a source state index is immutable; choose a new destination")
    config.output_dir.mkdir(parents=True, exist_ok=True)
    archive_sha = digest(config.archive)
    episodes: list[dict[str, Any]] = []
    counts: Counter[str] = Counter()
    names: dict[str, Counter[str]] = {
        split: Counter() for split in ("train", "selection", "confirmation")
    }
    temporary = Path("tmp") / f"{config.output_dir.name}.jsonl.partial"
    temporary.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(config.archive) as archive, temporary.open("x") as output:
        for member in sorted(archive.namelist()):
            if not member.endswith(".json"):
                continue
            raw = archive.read(member)
            replay = orjson.loads(raw)
            configuration = replay["configuration"]
            if (
                replay["module_version"] != config.module_version
                or replay["name"] != "kaggriculture"
                or replay["statuses"] != ["DONE", "DONE"]
                or len(replay["steps"]) != configuration["episodeSteps"]
            ):
                raise ValueError(f"incomplete or incompatible replay: {member}")
            seed = int(replay["info"]["seed"])
            split = partition(seed)
            counts[f"{split}_episodes"] += 1
            names[split].update(replay["info"]["TeamNames"])
            identity = {
                "member": member,
                "sha256": hashlib.sha256(raw).hexdigest(),
                "seed": seed,
                "split": split,
                "configuration": configuration,
                "display_names": replay["info"]["TeamNames"],
            }
            episodes.append(identity)
            if any(
                step <= 0 or step >= len(replay["steps"]) - 1 for step in config.additional_steps
            ):
                raise ValueError("extra restart boundaries must be positive and nonterminal")
            boundaries = sorted(
                set(
                    range(
                        configuration["turnsPerDay"],
                        len(replay["steps"]) - 1,
                        configuration["turnsPerDay"],
                    )
                )
                | set(config.additional_steps)
            )
            for step in boundaries:
                seats = [
                    describe(state["observation"], seat)
                    for seat, state in enumerate(replay["steps"][step])
                ]
                row = {"member": member, "seed": seed, "split": split, "step": step, "seats": seats}
                output.write(json.dumps(row, separators=(",", ":")) + "\n")
                counts[f"{split}_states"] += 1
                for seat in seats:
                    counts[f"{split}_seat_states"] += 1
                    for feature in ("plants", "animals", "positive_yield_tiles", "shed_items"):
                        counts[f"{split}_seats_with_{feature}"] += seat[feature] > 0
    temporary.replace(target)
    write_json(
        config.output_dir / "manifest.json",
        {
            "schema": "replay-restart-candidates-v1",
            "archive": str(config.archive),
            "archive_sha256": archive_sha,
            "module_version": config.module_version,
            "additional_steps": config.additional_steps,
            "index": target.name,
            "index_sha256": digest(target),
            "partition": "SHA256(replay-state-v1:seed), first eight bytes modulo ten; 0-7/8/9",
            "episodes": episodes,
            "action_labels": False,
            "native_restart_verified": False,
        },
    )
    report = {
        "configuration": config.model_dump(mode="json"),
        "counts": counts,
        "display_name_counts": names,
        "index_sha256": digest(target),
        "scope": "Recorded state coverage only; names do not identify policy versions; "
        "positive yield does not imply harvest legality; not used for training",
    }
    write_json(config.report_dir / "coverage.json", report)
    print(json.dumps({"counts": counts, "report_dir": str(config.report_dir)}), flush=True)


@hydra.main(
    version_base=None,
    config_path=str(Path(__file__).resolve().parents[3] / "configs"),
    config_name="replay_states",
)
def main(configuration: DictConfig) -> None:
    """Resolve immutable source index controls with Hydra."""
    run(Index.model_validate(OmegaConf.to_container(configuration.index, resolve=True)))


if __name__ == "__main__":
    main()
