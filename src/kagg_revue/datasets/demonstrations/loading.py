"""Authenticated bounded-memory batches from prepared daily demonstrations."""

import json
from collections.abc import Iterator
from pathlib import Path
from typing import Any, Literal

import numpy as np
import torch

from kagg_revue.artifacts.io import digest
from kagg_revue.datasets.exclusions import validate_manifest
from kagg_revue.native import _revue_core as native
from kagg_revue.native.features import Layout
from kagg_revue.policy.contracts import ContractLayout, NetworkShape


class Dataset:
    """Bind exact geometry, source partitions and every encoded array by hash."""

    def __init__(
        self,
        manifest: Path,
        sha256: str,
        layout: ContractLayout,
        environment: dict[str, int | float],
        reserved: tuple[tuple[int, int], ...],
    ) -> None:
        """Reject altered data, source seed leakage and incompatible feature ABIs."""
        if digest(manifest) != sha256:
            raise ValueError("demonstration manifest hash differs from the declared source")
        self.directory = manifest.parent.resolve()
        self.manifest: dict[str, Any] = json.loads(manifest.read_text())
        if self.manifest["schema"] != "grounded-daily-demonstrations-v1":
            raise ValueError("unsupported demonstration schema")
        validate_manifest(self.manifest)
        stored = self.manifest["layout"]
        encoded = ContractLayout(
            Layout(**stored["observation"]),
            stored["board_size"],
            stored["interval"],
            NetworkShape(**stored["network"]),
            stored["late_start"],
            stored["late_interval"],
        )
        if not layout.same_interface(encoded) or native.Engine(0, environment).configuration != (
            native.Engine(0, self.manifest["configuration"]["environment"]).configuration
        ):
            raise ValueError("demonstration geometry differs from the fresh policy")
        self.layout = layout
        self.shards: list[dict[str, Any]] = self.manifest["shards"]
        seeds: dict[int, str] = {}
        episodes: set[str] = set()
        dates: dict[str, set[str]] = {
            "train": set(),
            "val": set(),
            "selection": set(),
            "confirmation": set(),
        }
        for shard in self.shards:
            if self.manifest.get("sampling_weights_required") and "sampling_weights" not in shard:
                raise ValueError("curated shard lacks required exposure weights")
            if self.manifest.get("row_selection_required") and "row_selection" not in shard:
                raise ValueError("a filtered dataset shard lacks its required selection mask")
            dates[shard["split"]].add(shard["source_date"])
            for episode in shard["episodes"]:
                seed = episode["seed"]
                episode_id = str(episode.get("episode_id", seed))
                if (
                    seeds.setdefault(seed, shard["split"]) != shard["split"]
                    or episode_id in episodes
                    or any(start <= seed < stop for start, stop in reserved)
                ):
                    raise ValueError("demonstration seeds overlap episodes or online seed roles")
                episodes.add(episode_id)
            for name, expected in shard["hashes"].items():
                path = self.path(shard[name])
                if digest(path) != expected:
                    raise ValueError(f"demonstration shard hash differs: {path.name}")
        if dates["val"] and (dates["selection"] or dates["confirmation"]):
            raise ValueError("train/val demonstrations cannot also contain legacy held-out splits")
        validation = dates["val"] or dates["selection"]
        if not dates["train"] or not validation:
            raise ValueError("demonstrations require training and validation partitions")
        if self.manifest["configuration"].get("partition", "dates") == "dates" and max(
            dates["train"]
        ) >= min(validation):
            raise ValueError("selection dates must follow complete training dates")

    def path(self, name: str) -> Path:
        """Resolve only files inside the authenticated source directory."""
        path = (self.directory / name).resolve()
        if not path.is_relative_to(self.directory):
            raise ValueError("demonstration array escapes its dataset")
        return path

    def resolve_split(self, split: str) -> str:
        """Let existing BC validation callers read explicitly named val partitions."""
        if split == "selection" and any(shard["split"] == "val" for shard in self.shards):
            return "val"
        return split

    def partition(self, split: Literal["train", "val", "selection", "confirmation"]) -> list[int]:
        """Return stable global shard indices for one complete date partition."""
        name = self.resolve_split(split)
        return [i for i, shard in enumerate(self.shards) if shard["split"] == name]

    def batches(
        self,
        shard: int,
        batch_rows: int,
        device: torch.device,
        seed: tuple[int, ...] | None,
        *,
        rank: int = 0,
        world: int = 1,
    ) -> Iterator[tuple[torch.Tensor, torch.Tensor, torch.Tensor, int]]:
        """Shuffle within one shard and pad only the final batch for fixed graph shapes."""
        if batch_rows % world or not 0 <= rank < world:
            raise ValueError("demonstration batches must divide across valid ranks")
        record = self.shards[shard]
        arrays = {
            key: np.load(self.path(record[key]), mmap_mode="r")
            for key in ("observations", "actions", "origins", "quantity_coverage")
        }
        rows = record["rows"]
        expected = {
            "observations": (rows, self.layout.observation.features),
            "actions": (rows, self.layout.factors),
            "origins": (rows, 2),
            "quantity_coverage": (rows,),
        }
        if any(arrays[key].shape != shape for key, shape in expected.items()):
            raise ValueError("demonstration array dimensions disagree with the manifest")
        eligible = np.asarray(arrays["quantity_coverage"]).copy()
        if "row_selection" in record:
            selection = np.load(self.path(record["row_selection"]), mmap_mode="r")
            if selection.shape != (rows,) or selection.dtype != np.bool_:
                raise ValueError("demonstration row-selection dimensions differ")
            eligible &= selection
        indices = np.flatnonzero(eligible)
        if seed is not None:
            generator = np.random.default_rng(seed)
            if "sampling_weights" in record and record["split"] == "train":
                weights = np.load(self.path(record["sampling_weights"]), mmap_mode="r")
                if (
                    weights.shape != (rows,)
                    or not np.isfinite(weights).all()
                    or (weights <= 0).any()
                ):
                    raise ValueError("invalid demonstration sampling weights")
                probabilities = np.asarray(weights[indices], dtype=np.float64)
                probabilities /= probabilities.sum()
                indices = generator.choice(
                    indices, size=len(indices), replace=True, p=probabilities
                )
            else:
                generator.shuffle(indices)
        for start in range(0, len(indices), batch_rows):
            selected = indices[start : start + batch_rows]
            count = len(selected)
            if count < batch_rows:
                selected = np.resize(selected, batch_rows)
            local = batch_rows // world
            selected = selected[rank * local : (rank + 1) * local]
            observations = torch.from_numpy(arrays["observations"][selected]).to(device)
            actions = torch.from_numpy(arrays["actions"][selected].astype(np.int64)).to(device)
            steps = torch.from_numpy(arrays["origins"][selected, 0].astype(np.int64)).to(device)
            yield observations, actions, steps, count
