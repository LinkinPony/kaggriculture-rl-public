"""Authenticated official prefixes and immutable native restart banks."""

import hashlib
import json
import time
import zipfile
from pathlib import Path
from typing import Any

import numpy as np
import orjson
from pydantic import Field, model_validator

from kagg_revue.artifacts.io import digest
from kagg_revue.configuration import FrozenSettings
from kagg_revue.datasets.observations import ReplayObservations, difference
from kagg_revue.datasets.states import partition
from kagg_revue.native import _revue_core as native


class RestartSource(FrozenSettings):
    """Bind an immutable source index, with state-only eligibility controls."""

    manifest: Path
    manifest_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    maximum_episodes: int = Field(default=128, gt=0)
    maximum_cash_gap: float = Field(default=0.2, ge=0)

    @model_validator(mode="after")
    def validate_source_path(self) -> "RestartSource":
        """Disallow run artifacts and path escapes as restart sources."""
        if (
            self.manifest.is_absolute()
            or ".." in self.manifest.parts
            or self.manifest.parts[:2] != ("data", "external")
        ):
            raise ValueError("restart sources belong under data/external")
        return self


class RestartBank:
    """Replay source prefixes once, check official features, and fork clean states."""

    def __init__(
        self,
        source: RestartSource,
        *,
        split: str,
        environment: dict[str, int | float],
        units: int,
        quantities: tuple[int, ...],
        workers: int,
        features: int,
        starts: tuple[int, ...],
    ) -> None:
        """Authenticate every source role before opening or caching raw replay data."""
        if split not in {"train", "selection", "confirmation"}:
            raise ValueError("unknown restart partition")
        if digest(source.manifest) != source.manifest_sha256:
            raise ValueError("restart manifest hash changed")
        manifest = json.loads(source.manifest.read_text())
        archive = Path(manifest["archive"])
        index = source.manifest.parent / manifest["index"]
        if (
            manifest["schema"] != "replay-restart-candidates-v1"
            or archive.is_absolute()
            or ".." in archive.parts
            or archive.parts[:2] != ("data", "external")
            or not index.resolve().is_relative_to(source.manifest.parent.resolve())
            or digest(archive) != manifest["archive_sha256"]
            or digest(index) != manifest["index_sha256"]
        ):
            raise ValueError("restart source identity differs from its manifest")
        records = [json.loads(line) for line in index.read_text().splitlines()]
        if any(partition(row["seed"]) != row["split"] for row in records):
            raise ValueError("restart index crosses its declared seed partitions")
        self.source, self.split = source, split
        self.environment, self.units, self.quantities = environment, units, quantities
        self.workers, self.features, self.starts = workers, features, starts
        self.configuration = dict(native.Engine(0, environment).configuration)
        self.archive = archive
        self.version = manifest["module_version"]
        self.episodes = {entry["member"]: entry for entry in manifest["episodes"]}
        if any(
            row["member"] not in self.episodes
            or row["seed"] != self.episodes[row["member"]]["seed"]
            or row["split"] != self.episodes[row["member"]]["split"]
            for row in records
        ):
            raise ValueError("restart index and replay identities disagree")
        eligible = sorted(
            (key for key, value in self.episodes.items() if value["split"] == split),
            key=lambda key: hashlib.sha256(key.encode()).digest(),
        )
        selected = set(eligible[: source.maximum_episodes])
        self.rows: dict[int, list[dict[str, Any]]] = {}
        for step in starts:
            self.rows[step] = [
                row
                for row in records
                if row["step"] == step and row["member"] in selected and self._eligible(row)
            ]
            if not self.rows[step]:
                raise ValueError(f"restart partition {split} has no eligible states at {step}")
        self.loaded: dict[str, tuple[list[Any], dict[int, tuple[list[Any], Any]]]] = {}
        self.banks: dict[int, Any] = {}

    def _eligible(self, row: dict[str, Any]) -> bool:
        seats = row["seats"]
        gap = abs(seats[0]["cash"] - seats[1]["cash"])
        scale = max(3000, seats[0]["cash"], seats[1]["cash"])
        return bool(
            gap <= self.source.maximum_cash_gap * scale
            and max(seat["units"] for seat in seats) <= self.units
        )

    def _load(self, member: str) -> tuple[list[Any], dict[int, tuple[list[Any], Any]]]:
        if member in self.loaded:
            return self.loaded[member]
        identity = self.episodes[member]
        if identity["split"] != self.split or partition(identity["seed"]) != self.split:
            raise ValueError("replay crossed a source partition")
        with zipfile.ZipFile(self.archive) as archive:
            raw = archive.read(member)
        if hashlib.sha256(raw).hexdigest() != identity["sha256"]:
            raise ValueError("replay content hash changed")
        replay = orjson.loads(raw)
        if (
            replay["info"]["seed"] != identity["seed"]
            or replay["module_version"] != self.version
            or dict(native.Engine(0, replay["configuration"]).configuration) != self.configuration
        ):
            raise ValueError("restart replay uses a different seed, version or game configuration")
        sessions = [native.ContractSession(self.environment, self.units) for _ in range(2)]
        sequences = [ReplayObservations() for _ in range(2)]
        boundaries: dict[int, tuple[list[Any], Any]] = {}
        for step, states in enumerate(replay["steps"][: max(self.starts) + 1]):
            observations = []
            for seat, session in enumerate(sessions):
                observation = sequences[seat].update(states[seat]["observation"], step)
                observations.append(observation)
                session.update(observation)
            if step in self.starts:
                packed = np.empty((2, self.features), np.float16)
                for seat, session in enumerate(sessions):
                    session.observe_into(packed[seat : seat + 1])
                boundaries[step] = (observations, packed)
        actions = [[state["action"] for state in pair] for pair in replay["steps"][1:]]
        self.loaded[member] = actions, boundaries
        return actions, boundaries

    def _prepare(self, step: int) -> None:
        """Check every root at one cut, including inventory order and actor features."""
        rows = self.rows[step]
        if step not in self.banks:
            loaded = [self._load(row["member"]) for row in rows]
            bank = native.SelfPlayBatch(
                self.environment,
                [row["seed"] for row in rows],
                [0] * len(rows),
                self.units,
                self.workers,
                list(self.quantities),
            )
            bank.replay_prefixes([actions[:step] for actions, _ in loaded])
            packed = np.empty((2 * len(rows), self.features), np.float16)
            bank.observe_selfplay_into(packed)
            fields = ("step", "player", "day", "hour", "farms", "private", "market", "town")
            for lane, (_, boundaries) in enumerate(loaded):
                expected, features = boundaries[step]
                for seat in range(2):
                    actual = bank.observation(lane, seat)
                    mismatch = difference(
                        {key: actual[key] for key in fields},
                        {key: expected[seat][key] for key in fields},
                    )
                    if mismatch:
                        raise ValueError(
                            f"restart state mismatch: {rows[lane]['member']}:{step}:{seat}: "
                            f"{mismatch}"
                        )
                np.testing.assert_array_equal(
                    packed[2 * lane : 2 * lane + 2],
                    features,
                    err_msg=f"restart features: {rows[lane]['member']}:{step}",
                )
            self.banks[step] = bank

    def prepare(self) -> dict[str, Any]:
        """Qualify all declared cuts before the first policy update consumes data."""
        started = time.perf_counter()
        for step in self.starts:
            self._prepare(step)
        return {
            "source_manifest_sha256": self.source.manifest_sha256,
            "split": self.split,
            "verified_roots_by_start": {str(step): len(self.rows[step]) for step in self.starts},
            "inventory_order": "recovered causally from consecutive private inventory key sets",
            "preparation_seconds": time.perf_counter() - started,
        }

    def sample(
        self, step: int, count: int, seed: int, *, replace: bool = True
    ) -> tuple[Any, dict[str, Any]]:
        """Fork verified states; no original action after the boundary is consumed."""
        started = time.perf_counter()
        self._prepare(step)
        rows = self.rows[step]
        indices = np.random.default_rng(seed).choice(len(rows), size=count, replace=replace)
        selected = [rows[index] for index in indices]
        return self.banks[step].fork(indices), {
            "split": self.split,
            "start_step": step,
            "sampling_seed": seed,
            "source_manifest_sha256": self.source.manifest_sha256,
            "verified_source_states": len(rows),
            "members": [row["member"] for row in selected],
            "environment_seeds": [row["seed"] for row in selected],
            "initial_cash": [[seat["cash"] for seat in row["seats"]] for row in selected],
            "preparation_seconds": time.perf_counter() - started,
            "official_prefix_actions_in_ppo": 0,
        }
