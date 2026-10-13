"""Verify sequence arrays against complete raw and official reference trajectories."""

import hashlib
import json
import multiprocessing
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import Any

import hydra
import numpy as np
import orjson
from omegaconf import DictConfig, OmegaConf

from kagg_revue.artifacts.io import digest, write_json
from kagg_revue.datasets.daily import audit_episode
from kagg_revue.datasets.demonstrations.canonical import canonicalize
from kagg_revue.datasets.demonstrations.encoding import encode, quantity_columns
from kagg_revue.datasets.sequences.prepare import Preparation
from kagg_revue.datasets.sequences.reporting import summarize
from kagg_revue.datasets.sequences.sources import read_replay
from kagg_revue.native import _revue_core as native
from kagg_revue.policy.contracts import ContractLayout


def verify_episode(job: tuple[dict[str, Any], dict[str, Any]]) -> dict[str, Any]:
    """Rebuild all frames and labels; independently replay both official seats."""
    stored, record = job
    config = Preparation.model_validate(stored)
    task = record["task"]
    raw = read_replay(task)
    if hashlib.sha256(raw).hexdigest() != record["episodes"][0]["raw_sha256"]:
        raise ValueError("source replay differs from encoded sequence provenance")
    replay = orjson.loads(raw)
    if (
        native.Engine(0, config.environment).configuration
        != native.Engine(0, replay["configuration"]).configuration
    ):
        raise ValueError("source episode uses a different game configuration")
    layout = ContractLayout.resolve(config.geometry())
    seats = [s["seat"] for s in task["seats"]]
    # Native feature and official audits below must replay the official actions.
    labelled = canonicalize(replay, seats)[0] if config.canonical_market else replay
    observations, actions, eligible, _ = encode(labelled, layout)
    columns = quantity_columns(layout)
    actions[..., columns] = np.clip(actions[..., columns], 1, 100) - 1
    for key, expected in (
        ("observations", observations),
        ("actions", actions),
        ("eligible", eligible),
    ):
        actual = np.load(config.output / record[key], mmap_mode="r")
        if not np.array_equal(actual, expected[:, seats]) or not np.isfinite(actual).all():
            raise ValueError(f"encoded sequence differs: {task['episode_id']} {key}")
    native_rows = 0
    legacy_rows = 0
    if config.agronomy:
        prefixes = [[state["action"] for state in pair] for pair in replay["steps"][1:]]
        for turn in (0, 23, 24, 191, 383, 575, 718):
            if turn >= layout.observation.turns:
                continue
            batch = native.SelfPlayBatch(
                config.environment,
                [task["seed"]],
                [0],
                32,
                1,
                list(layout.observation.quantities),
            )
            batch.replay_prefixes([prefixes[:turn]])
            packed = np.empty((2, layout.observation.features), np.float16)
            batch.observe_selfplay_into(packed)
            if not np.array_equal(packed, observations[turn]):
                raise ValueError("native engine and seat-visible agronomy features differ")
            native_rows += 2
        current = json.loads((config.output / "manifest.json").read_text())
        if "feature_migration" in current:
            source = Path(current["feature_migration"]["source"])
            previous = json.loads(source.read_text())
            old = next(r for r in previous["shards"] if r["task"] == task)
            old_array = np.load(source.parent / old["observations"], mmap_mode="r")
        else:
            legacy = config.model_copy(update={"agronomy": config.derived, "derived": False})
            old_observations, old_actions, old_eligible, _ = encode(
                labelled, ContractLayout.resolve(legacy.geometry())
            )
            old_actions[..., columns] = np.clip(old_actions[..., columns], 1, 100) - 1
            if not np.array_equal(old_actions, actions) or not np.array_equal(
                old_eligible, eligible
            ):
                raise ValueError("agronomy features changed supervision")
            old_array = old_observations[:, seats]
        support = layout.observation.support_features
        prefix = old_array.shape[-1] - support
        if not np.array_equal(old_array[..., :prefix], observations[:, seats, :prefix]) or not (
            np.array_equal(old_array[..., -support:], observations[:, seats, -support:])
        ):
            raise ValueError("legacy observation fields changed during feature migration")
        legacy_rows = record["rows"]
    official = audit_episode(
        (
            task["path"],
            str(task["episode_id"]),
            "1.32.7",
            "data/external/kaggriculture-reference-1.32.7",
        )
    )
    if not official["matched"]:
        raise ValueError(f"official full episode mismatch: {official}")
    return {
        "episode_id": task["episode_id"],
        "date": task["date"],
        "array_rows_checked": record["rows"],
        "native_feature_rows_checked": native_rows,
        "legacy_rows_identical": legacy_rows,
        "official": official,
    }


def verify(
    config: Preparation,
    output: Path = Path("outputs/analysis/gtrxl-20260916/data-verification.json"),
) -> dict[str, Any]:
    """Authenticate every array and audit deterministic samples from each source date."""
    path = config.output / "manifest.json"
    manifest = json.loads(path.read_text())
    seeds: dict[int, str] = {}
    episodes = set()
    files = 0
    for record in manifest["shards"]:
        task = record["task"]
        if (
            task["episode_id"] in episodes
            or seeds.setdefault(task["seed"], task["split"]) != task["split"]
        ):
            raise ValueError("duplicate episode or seed leakage between partitions")
        episodes.add(task["episode_id"])
        for key, expected in record["hashes"].items():
            if digest(config.output / record[key]) != expected:
                raise ValueError("sequence array authentication failed")
            files += 1
    selected = []
    for date in sorted({r["source_date"] for r in manifest["shards"]}):
        rows = [r for r in manifest["shards"] if r["source_date"] == date]
        rows.sort(
            key=lambda r: hashlib.sha256(f"gtrxl-audit:{r['task']['episode_id']}".encode()).digest()
        )
        selected.extend(rows[:3])
    for name in config.teachers:
        if not any(name == s["name"] for r in selected for s in r["task"]["seats"]):
            candidates = [
                r for r in manifest["shards"] if any(s["name"] == name for s in r["task"]["seats"])
            ]
            if not candidates:
                raise ValueError(f"requested teacher has no retained complete trajectory: {name}")
            selected.append(min(candidates, key=lambda r: r["task"]["episode_id"]))
    for split in manifest["coverage"]:
        if not any(r["split"] == split for r in selected):
            selected.append(next(r for r in manifest["shards"] if r["split"] == split))
    submissions = {
        s["submission_id"]
        for r in manifest["shards"]
        for s in r["task"]["seats"]
        if "submission_id" in s
    }
    for submission in sorted(submissions):
        if not any(
            s.get("submission_id") == submission for r in selected for s in r["task"]["seats"]
        ):
            selected.append(
                next(
                    r
                    for r in manifest["shards"]
                    if any(s.get("submission_id") == submission for s in r["task"]["seats"])
                )
            )
    with ProcessPoolExecutor(
        max_workers=6, mp_context=multiprocessing.get_context("spawn")
    ) as pool:
        results = list(
            pool.map(verify_episode, [(config.model_dump(mode="json"), r) for r in selected])
        )
    report = {
        "manifest_sha256": digest(path),
        "authenticated_arrays": files,
        "episodes": len(episodes),
        "unique_world_seeds": len(seeds),
        "coverage": manifest["coverage"],
        "checked_episodes": results,
        "checked_array_rows": sum(r["array_rows_checked"] for r in results),
        "official_observations": sum(r["official"]["checked_observations"] for r in results),
        "summary": summarize(config.output, manifest, ContractLayout.resolve(config.geometry())),
    }
    write_json(output, report)
    return report


@hydra.main(version_base=None, config_path="../../../../configs", config_name="sequences_20260916")
def main(configuration: DictConfig) -> None:
    """Run the full dataset authentication and bounded independent replay audit."""
    config = Preparation.model_validate(OmegaConf.to_container(configuration.data, resolve=True))
    options = {"output": Path(configuration.report)} if configuration.get("report") else {}
    result = verify(config, **options)
    print(
        json.dumps({key: value for key, value in result.items() if key != "checked_episodes"}),
        flush=True,
    )


if __name__ == "__main__":
    main()
