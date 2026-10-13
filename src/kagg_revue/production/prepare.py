"""Streaming conversion of raw source replays to operating-plan BC shards."""

import json
from dataclasses import asdict, replace
from pathlib import Path

import numpy as np

from kagg_revue.artifacts.io import digest, write_json
from kagg_revue.native.features import Layout
from kagg_revue.policy.contracts import ContractLayout
from kagg_revue.production.config import Settings
from kagg_revue.production.contracts import propose_contracts
from kagg_revue.production.data import generate


def prepare(settings: Settings) -> Path:
    """Persist compact decision-boundary observations and auditable proposal labels."""
    if settings.bc.source_kind == "daily":
        from kagg_revue.production.replays import prepare as prepare_replays

        return prepare_replays(settings)
    source_path = generate(settings)
    directory = settings.bc.directory
    manifest_path = directory / "manifest.json"
    layout = ContractLayout.resolve(settings)
    layout_json = json.loads(json.dumps(asdict(layout)))
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text())
        stored = manifest["layout"]
        same_geometry = (
            replace(Layout(**stored["observation"]), width=0)
            == replace(layout.observation, width=0)
            and stored["board_size"] == layout.board_size
            and stored["interval"] == layout.interval
            and stored.get("late_start", 0) == layout.late_start
            and stored.get("late_interval", 0) == layout.late_interval
            and (stored.get("network", {}).get("architecture") == "work-v1") == layout.work
        )
        if not same_geometry or manifest["source_sha256"] != digest(source_path):
            raise ValueError("existing contract dataset does not match its source and layout")
        return manifest_path
    directory.mkdir(parents=True, exist_ok=True)
    source = json.loads(source_path.read_text())
    shards = []
    for index, shard in enumerate(source["shards"]):
        observations = np.load(settings.bc.source / shard["observations"], mmap_mode="r")
        raw = np.load(settings.bc.source / shard["actions"], mmap_mode="r")
        labels = propose_contracts(observations, raw, layout)
        observation_path = directory / f"shard-{index:04d}-observations.npy"
        label_path = directory / f"shard-{index:04d}-contracts.npy"
        np.save(observation_path, observations[list(layout.starts)])
        np.save(label_path, labels.astype(np.int16))
        shards.append(
            {
                "observations": observation_path.name,
                "actions": label_path.name,
                "games": shard["games"],
                "rows": layout.decisions * shard["games"],
                "observations_sha256": digest(observation_path),
                "actions_sha256": digest(label_path),
            }
        )
    write_json(
        manifest_path,
        {
            "schema": "work-program-demonstrations-v1"
            if layout.work
            else "spatial-contract-demonstrations-v1",
            "layout": layout_json,
            "source": str(source_path),
            "source_sha256": digest(source_path),
            "shards": shards,
            "label_kind": "noncausal ordered-work program"
            if layout.work
            else "noncausal operating-intent proposal",
        },
    )
    return manifest_path
