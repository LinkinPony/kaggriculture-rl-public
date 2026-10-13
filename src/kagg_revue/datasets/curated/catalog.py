"""Select demonstrated seats without ranking actions or opening strategies."""

import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any

import numpy as np
from pydantic import Field

from kagg_revue.configuration import FrozenSettings
from kagg_revue.learning.config import default_environment
from kagg_revue.policy.settings import GeometrySettings, ModelSettings


class Preparation(FrozenSettings):
    """Frozen raw-data selection and ordinary BC sampling controls."""

    output_dir: Path
    tasks: Path
    trajectories: Path
    public_manifest: Path
    minimum_public_score: float = 2800
    excluded_names: tuple[str, ...] = ("Unknown Mother-Goose",)
    partition: str = "episode-seed"
    partition_seed: int = 62001
    workers: int = Field(default=8, gt=0)
    episodes_per_shard: int = Field(default=32, gt=0)
    exposure_power: float = Field(default=0.5, ge=0, le=1)
    minimum_weight: float = Field(default=0.5, gt=0)
    maximum_weight: float = Field(default=2.0, gt=0)
    environment: dict[str, int | float] = Field(default_factory=default_environment)

    def geometry(self) -> GeometrySettings:
        """Keep the current causal native interface and exact small quantities."""
        return GeometrySettings(
            unit_limit=32,
            width=128,
            decision_interval=1,
            quantity_max=128,
            quantity_extra=(256, 512, 1024, 4096, 10000, 1000000),
            environment=self.environment,
            model=ModelSettings(architecture="grounded-v2", time_prior=False, critic_depth=2),
        )


def catalog(config: Preparation) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Keep daily seats and qualified public versions, excluding our own policy."""
    public = json.loads(config.public_manifest.read_text())
    scores = {row["id"]: float(row["publicScore"]) for row in public["submissions"]}
    qualified = {key for key, score in scores.items() if score >= config.minimum_public_score}
    traces = {
        (row["episode_id"], row["seat"]): row
        for line in config.trajectories.read_text().splitlines()
        if (row := json.loads(line))
    }
    selected: list[dict[str, Any]] = []
    rejected: Counter[str] = Counter()
    seen: set[int] = set()
    for raw in json.loads(config.tasks.read_text()):
        episode_id = raw["episode_id"]
        if episode_id in seen:
            raise ValueError("duplicate replay in the source catalog")
        seen.add(episode_id)
        seats = []
        for seat in (0, 1):
            row = traces[(episode_id, seat)]
            submission = row["submission_id"]
            reason = (
                "own_policy"
                if row["name"] in config.excluded_names
                else "unqualified_public_version"
                if (
                    (raw["source"] == "public_only" and submission not in qualified)
                    or (submission in scores and submission not in qualified)
                )
                else None
            )
            if reason:
                rejected[reason] += 1
                continue
            if not row["native_first_four_exact"] or row["version"] != "1.32.7":
                raise ValueError("unverified replay cannot enter demonstrations")
            seats.append({"seat": seat, "name": row["name"], "submission_id": submission})
        if not seats:
            continue
        seed = traces[(episode_id, 0)]["seed"]
        bucket = int.from_bytes(
            hashlib.sha256(f"{config.partition_seed}:{seed}".encode()).digest()[:8], "big"
        )
        split = (
            "train"
            if bucket % 10000 < 9000
            else ("selection" if bucket % 10000 < 9500 else "confirmation")
        )
        selected.append({**raw, "seed": seed, "split": split, "seats": seats})
    # Fit exposure only on training trajectories. Names identify source families,
    # never a strategy, latent action class, win/loss target, or independent version.
    counts = Counter(
        seat["name"] for task in selected if task["split"] == "train" for seat in task["seats"]
    )
    reference = float(np.mean(list(counts.values())))
    weights = {
        name: float(
            np.clip(
                (reference / count) ** config.exposure_power,
                config.minimum_weight,
                config.maximum_weight,
            )
        )
        for name, count in counts.items()
    }
    for task in selected:
        for seat in task["seats"]:
            seat["weight"] = weights.get(seat["name"], 1.0) if task["split"] == "train" else 1.0
    return selected, {
        "qualified_public_submissions": sorted(qualified),
        "rejected_seats": dict(rejected),
        "training_family_trajectories": dict(counts),
        "training_family_weights": weights,
        "sampling": "Within shuffled mixed-source shards, fixed row count, replacement; "
        "clipped inverse-square-root teacher trajectory frequency. Held-out rows unchanged.",
    }
