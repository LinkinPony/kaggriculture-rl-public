"""Parallel construction of provenance-bound replay shards."""

from __future__ import annotations

import csv
import hashlib
import io
import json
import re
import shutil
import tempfile
import zipfile
from collections import Counter
from collections.abc import Mapping, Sequence
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

import orjson

from kagg_revue.bc.data_config import BcDataSettings
from kagg_revue.bc.dataset import SourceManifest, sha256_file
from kagg_revue.bc.opening import scan_openings, select_diverse_openings
from kagg_revue.bc.replay import (
    ACTION_TARGET_CANONICALIZATION,
    EpisodeLocator,
    ShardResult,
    ShardTask,
    archive_identity,
    daily_episode_metadata,
    prepare_shard,
    source_fingerprint,
)
from kagg_revue.bc.report import build_analysis, write_analysis
from kagg_revue.core.backend import load_backend
from kagg_revue.core.provenance import source_identity
from kagg_revue.native import _revue_native as native

_ARCHIVE_PATTERN = re.compile(r"^kaggriculture-episodes-(\d{4}-\d{2}-\d{2})\.zip$")


def _resolve(root: Path, path: Path) -> Path:
    return path.resolve() if path.is_absolute() else (root / path).resolve()


def resolve_paths(settings: BcDataSettings, root: Path) -> BcDataSettings:
    """Resolve all operational paths relative to the repository checkout."""
    return settings.model_copy(
        update={
            "index_archive": _resolve(root, settings.index_archive),
            "source_archives": tuple(_resolve(root, path) for path in settings.source_archives),
            "output_dir": _resolve(root, settings.output_dir),
            "report_dir": _resolve(root, settings.report_dir),
        }
    )


def _require_within(path: Path, parent: Path, name: str) -> None:
    if not path.is_relative_to(parent.resolve()):
        raise ValueError(f"{name} must be under {parent.resolve()}")


def _index_rows(index_archive: Path) -> list[dict[str, object]]:
    with zipfile.ZipFile(index_archive) as archive:
        members = [info.filename for info in archive.infolist() if not info.is_dir()]
        if members != ["manifest.csv"]:
            raise ValueError("index archive must contain only manifest.csv")
        with archive.open("manifest.csv") as raw_stream:
            stream = io.TextIOWrapper(raw_stream, encoding="utf-8", newline="")
            rows = list(csv.DictReader(stream))
    parsed: list[dict[str, object]] = []
    for row in rows:
        try:
            parsed.append(
                {
                    "date": row["date"],
                    "daily_dataset_slug": row["daily_dataset_slug"],
                    "daily_dataset_url": row["daily_dataset_url"],
                    "episode_count": int(row["episode_count"]),
                    "total_bytes": int(row["total_bytes"]),
                    "top_avg_score": float(row["top_avg_score"]),
                    "median_avg_score": float(row["median_avg_score"]),
                }
            )
        except (KeyError, TypeError, ValueError) as error:
            raise ValueError("index manifest contains an invalid row") from error
    if not parsed:
        raise ValueError("index manifest is empty")
    dates = [str(row["date"]) for row in parsed]
    if dates != sorted(dates) or len(set(dates)) != len(dates):
        raise ValueError("index manifest dates must be unique and chronological")
    return parsed


def _archive_date(path: Path) -> str:
    matched = _ARCHIVE_PATTERN.fullmatch(path.name)
    if matched is None:
        raise ValueError(f"daily archive has an unexpected name: {path.name}")
    return matched.group(1)


def _source_inventory(
    settings: BcDataSettings,
) -> tuple[list[dict[str, object]], list[dict[str, object]], list[EpisodeLocator]]:
    rows = _index_rows(settings.index_archive)
    selected_rows = rows[-settings.days :]
    expected_dates = [str(row["date"]) for row in selected_rows]
    archive_by_date = {_archive_date(path): path for path in settings.source_archives}
    if sorted(archive_by_date) != expected_dates:
        raise ValueError(
            "daily archives are not the latest complete dates declared by the downloaded index"
        )

    identities: list[dict[str, object]] = []
    locators: list[EpisodeLocator] = []
    for row in selected_rows:
        date = str(row["date"])
        path = archive_by_date[date]
        identity = archive_identity(path)
        if identity["members"] != row["episode_count"]:
            raise ValueError(f"archive episode count differs from index: {path}")
        if identity["uncompressed_bytes"] != row["total_bytes"]:
            raise ValueError(f"archive byte count differs from index: {path}")
        identity["date"] = date
        identity["dataset_slug"] = row["daily_dataset_slug"]
        identity["dataset_url"] = row["daily_dataset_url"]
        identities.append(identity)
        episode_metadata = daily_episode_metadata(path)
        with zipfile.ZipFile(path) as archive:
            names = [
                info.filename
                for info in archive.infolist()
                if not info.is_dir() and info.filename.endswith(".json")
            ]
        names.sort(key=lambda name: int(Path(name).stem))
        for name in names:
            metadata = episode_metadata[Path(name).stem]
            if metadata["agent_count"] != settings.contract.agents:
                raise ValueError(f"daily episode agent count differs: {name}")
            locators.append(
                EpisodeLocator(
                    archive=path,
                    entry=name,
                    source_date=date,
                    create_time=str(metadata["create_time"]),
                    average_score=cast(float, metadata["average_score"]),
                    minimum_score=cast(float, metadata["minimum_score"]),
                )
            )
    episode_names = [locator.entry for locator in locators]
    if len(set(episode_names)) != len(episode_names):
        raise ValueError("episode IDs repeat across daily source archives")
    return selected_rows, identities, locators


def source_inventory(
    settings: BcDataSettings,
) -> tuple[list[dict[str, object]], list[dict[str, object]], list[EpisodeLocator]]:
    """Validate downloaded latest-day archives and return their replay inventory."""
    return _source_inventory(settings)


def _tasks(
    locators: Sequence[EpisodeLocator],
    output_dir: Path,
    settings: BcDataSettings,
) -> list[ShardTask]:
    tasks: list[ShardTask] = []
    index = 0
    grouped: dict[Path, list[EpisodeLocator]] = {}
    for locator in locators:
        grouped.setdefault(locator.archive, []).append(locator)
    for archive in settings.source_archives:
        archive_episodes = grouped.pop(archive, [])
        for offset in range(0, len(archive_episodes), settings.episodes_per_shard):
            tasks.append(
                ShardTask(
                    index=index,
                    episodes=tuple(archive_episodes[offset : offset + settings.episodes_per_shard]),
                    output_path=output_dir / f"turn-{index:05d}.npz",
                    contract=settings.contract,
                    maximum_turns=(
                        None
                        if settings.opening_diversity is None
                        else settings.opening_diversity.training_turns
                    ),
                )
            )
            index += 1
    if grouped:
        raise ValueError("selected replay locator refers to an undeclared source archive")
    return tasks


def _run_tasks(tasks: Sequence[ShardTask], workers: int) -> list[ShardResult]:
    results: list[ShardResult] = []
    with ProcessPoolExecutor(max_workers=min(workers, len(tasks))) as executor:
        futures = {executor.submit(prepare_shard, task): task for task in tasks}
        for completed_index, future in enumerate(as_completed(futures), start=1):
            result = future.result()
            results.append(result)
            print(
                json.dumps(
                    {
                        "completed_shards": completed_index,
                        "total_shards": len(tasks),
                        "shard_index": result.index,
                        "accepted_sequences": len(result.sequences),
                        "rejected_episodes": len(result.rejected),
                    },
                    sort_keys=True,
                ),
                flush=True,
            )
    return sorted(results, key=lambda result: result.index)


def _counter(results: Sequence[ShardResult], field: str) -> Counter[Any]:
    values: Counter[Any] = Counter()
    for result in results:
        mapping = getattr(result, field)
        if not isinstance(mapping, Mapping):
            raise TypeError(f"shard result {field} must be a mapping")
        values.update(mapping)
    return values


def _write_json(path: Path, value: Mapping[str, object]) -> None:
    if path.exists():
        raise FileExistsError(f"refusing to overwrite artifact metadata: {path}")
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True), encoding="utf-8")
    temporary.replace(path)


def _raw_manifest(
    settings: BcDataSettings,
    index_rows: Sequence[Mapping[str, object]],
    identities: Sequence[Mapping[str, object]],
) -> tuple[Path, dict[str, object]]:
    parents = {path.parent for path in settings.source_archives}
    parents.add(settings.index_archive.parent)
    if len(parents) != 1:
        raise ValueError("index and daily archives must share one raw artifact directory")
    raw_dir = parents.pop()
    manifest_path = raw_dir / "manifest.json"
    manifest: dict[str, object] = {
        "schema_version": "kaggriculture-raw-archive-v1",
        "generated_at": datetime.now(UTC).isoformat(),
        "source_index": {
            "dataset_url": ("https://www.kaggle.com/datasets/kaggle/kaggriculture-episodes-index"),
            "archive": settings.index_archive.name,
            "sha256": sha256_file(settings.index_archive),
            "size_bytes": settings.index_archive.stat().st_size,
        },
        "selection": {
            "semantics": "latest complete UTC dates in the downloaded index",
            "days": settings.days,
            "dates": [row["date"] for row in index_rows],
        },
        "license": "CC0-1.0",
        "daily_archives": [
            {
                **dict(identity),
                "path": Path(str(identity["path"])).name,
            }
            for identity in identities
        ],
    }
    if manifest_path.exists():
        existing = json.loads(manifest_path.read_text(encoding="utf-8"))
        if not isinstance(existing, dict):
            raise ValueError("existing raw archive manifest is not a mapping")
        existing_index = existing.get("source_index")
        existing_archives = existing.get("daily_archives")
        if not isinstance(existing_index, Mapping) or not isinstance(existing_archives, list):
            raise ValueError("existing raw archive manifest has an invalid schema")
        new_archives = manifest["daily_archives"]
        if not isinstance(new_archives, list):
            raise TypeError("new raw archive records must be a list")
        expected_hashes = [str(row["sha256"]) for row in new_archives if isinstance(row, Mapping)]
        existing_hashes = [
            str(row.get("sha256")) for row in existing_archives if isinstance(row, Mapping)
        ]
        if (
            existing_index.get("sha256")
            != cast(Mapping[str, object], manifest["source_index"])["sha256"]
            or existing_hashes != expected_hashes
        ):
            raise ValueError("existing raw archive manifest identifies different sources")
        return manifest_path, cast(dict[str, object], existing)
    _write_json(manifest_path, manifest)
    return manifest_path, manifest


def ensure_raw_manifest(
    settings: BcDataSettings,
    index_rows: Sequence[Mapping[str, object]],
    identities: Sequence[Mapping[str, object]],
) -> tuple[Path, dict[str, object]]:
    """Create or authenticate the reusable raw-archive provenance manifest."""
    return _raw_manifest(settings, index_rows, identities)


def _dataset_manifest(
    *,
    settings: BcDataSettings,
    results: Sequence[ShardResult],
    identities: Sequence[Mapping[str, object]],
    raw_manifest_path: Path,
    opening_selection_path: Path | None,
    root: Path,
) -> dict[str, object]:
    backend = load_backend(root)
    actor = cast(Mapping[str, Any], backend.actor_encoder_spec())
    codec = cast(Mapping[str, Any], backend.action_codec_spec())
    control = cast(Mapping[str, Any], native.official_action_control_spec())
    economic = cast(
        Mapping[str, Any],
        native.gpu_policy_state_spec(
            settings.contract.board_size,
            settings.contract.unit_limit,
        ),
    )
    keys = tuple(str(key) for key in codec["keys"])
    unit_tokens = int(codec["unit_tokens"])
    shards = [dict(result.shard) for result in results if result.shard is not None]
    sequences = [row for result in results for row in result.sequences]
    rejected = [row for result in results for row in result.rejected]
    source = source_identity(root)
    base: dict[str, object] = {
        "schema_version": "turn-behavior-dataset-v5",
        "source_commit": source["commit"],
        "worktree_dirty": source["worktree_dirty"],
        "source_tree_sha256": source["source_tree_sha256"],
        "native_backend": backend.identity,
        "actor_encoder_version": str(actor["version"]),
        "action_codec_version": str(codec["version"]),
        "action_target_canonicalization": ACTION_TARGET_CANONICALIZATION,
        "control_spec": str(control["version"]),
        "board_shape": [
            2,
            int(actor["board_channels"]),
            settings.contract.board_size,
            settings.contract.board_size,
        ],
        "unit_shape": [2, settings.contract.unit_limit, int(actor["unit_feat"])],
        "global_features": int(actor["global_feat"]),
        "economic_state_version": int(economic["version"]),
        "economic_state_features": int(economic["width"]),
        "unit_limit": settings.contract.unit_limit,
        "unit_candidate_keys": list(keys[:unit_tokens]),
        "market_candidate_keys": list(keys[unit_tokens:]),
        "source_replay_contract": settings.contract.model_dump(mode="json"),
        "source_archive_fingerprint": source_fingerprint(list(identities)),
        "raw_archive_manifest": {
            "path": str(raw_manifest_path),
            "sha256": sha256_file(raw_manifest_path),
        },
        "opening_selection": (
            None
            if opening_selection_path is None
            else {
                "path": opening_selection_path.name,
                "sha256": sha256_file(opening_selection_path),
            }
        ),
        "cleaning": {
            "alignment": "observation steps[t] -> action steps[t+1]",
            "accepted_episodes": len(sequences) // settings.contract.agents,
            "rejected_episodes": len(rejected),
            "canonical_repairs": dict(sorted(_counter(results, "repairs").items())),
        },
        "policy_labels": sorted({str(row["agent_name"]) for row in sequences}),
        "shards": shards,
    }
    identity_payload = orjson.dumps(base, option=orjson.OPT_SORT_KEYS)
    base["dataset_id"] = hashlib.sha256(identity_payload).hexdigest()
    base["generated_at"] = datetime.now(UTC).isoformat()
    SourceManifest.model_validate(base)
    return base


def prepare_dataset(settings: BcDataSettings, repository_root: Path) -> dict[str, object]:
    """Build one immutable compact dataset and its evidence report."""
    root = repository_root.resolve()
    settings = resolve_paths(settings, root)
    data_root = (root / "data" / "external").resolve()
    output_root = (root / "outputs").resolve()
    temporary_root = (root / "tmp").resolve()
    _require_within(settings.output_dir, data_root, "compact dataset")
    _require_within(settings.report_dir, output_root, "analysis report")
    for source_path in (settings.index_archive, *settings.source_archives):
        _require_within(source_path, data_root, "source archive")
        if not source_path.is_file():
            raise FileNotFoundError(f"source archive does not exist: {source_path}")
    if settings.output_dir.exists():
        raise FileExistsError(f"compact dataset already exists: {settings.output_dir}")
    if settings.report_dir.exists():
        raise FileExistsError(f"analysis report already exists: {settings.report_dir}")

    temporary_root.mkdir(parents=True, exist_ok=True)
    staging_root = Path(tempfile.mkdtemp(prefix="bc-data-prepare-", dir=temporary_root)).resolve()
    staging_dataset = staging_root / "compact"
    staging_dataset.mkdir()
    moved = False
    try:
        index_rows, identities, locators = _source_inventory(settings)
        raw_manifest_path, _ = _raw_manifest(settings, index_rows, identities)
        opening_selection_path: Path | None = None
        if settings.opening_diversity is not None:
            scan = scan_openings(
                locators,
                settings.opening_diversity,
                settings.contract,
                settings.workers,
            )
            scan_rejection_fraction = len(scan.rejected) / max(
                1,
                len(scan.candidates) + len(scan.rejected),
            )
            if scan_rejection_fraction > settings.maximum_rejection_fraction:
                raise RuntimeError(
                    "opening scan rejection fraction exceeds the configured data-quality "
                    f"boundary: {scan_rejection_fraction:.3%}"
                )
            selected, opening_selection = select_diverse_openings(
                scan,
                settings.opening_diversity,
            )
            if len(selected) < 3:
                raise RuntimeError("opening selection produced fewer than three episodes")
            locators = list(selected)
            opening_selection_path = staging_dataset / "opening-selection.json"
            _write_json(opening_selection_path, opening_selection)
        tasks = _tasks(locators, staging_dataset, settings)
        results = _run_tasks(tasks, settings.workers)
        sequences = [row for result in results for row in result.sequences]
        rejected = [row for result in results for row in result.rejected]
        accepted_episodes = len(sequences) // settings.contract.agents
        considered = accepted_episodes + len(rejected)
        rejection_fraction = len(rejected) / max(1, considered)
        if rejection_fraction > settings.maximum_rejection_fraction:
            raise RuntimeError(
                "replay rejection fraction exceeds the configured data-quality boundary: "
                f"{rejection_fraction:.3%}"
            )

        manifest = _dataset_manifest(
            settings=settings,
            results=results,
            identities=identities,
            raw_manifest_path=raw_manifest_path,
            opening_selection_path=opening_selection_path,
            root=root,
        )
        _write_json(staging_dataset / "manifest.json", manifest)
        settings.output_dir.parent.mkdir(parents=True, exist_ok=True)
        staging_dataset.replace(settings.output_dir)
        moved = True

        action_counts = cast(Counter[int], _counter(results, "action_counts"))
        codec = cast(Mapping[str, Any], native.action_codec_spec())
        source = source_identity(root)
        analysis = build_analysis(
            dataset_dir=settings.output_dir,
            dataset_id=str(manifest["dataset_id"]),
            source=source,
            source_archives=identities,
            index_rows=index_rows,
            sequences=sequences,
            rejected=rejected,
            action_keys=tuple(str(key) for key in codec["keys"]),
            action_counts=action_counts,
            repairs=cast(Counter[str], _counter(results, "repairs")),
            unit_histogram=cast(Counter[int], _counter(results, "unit_histogram")),
            market_histogram=cast(Counter[int], _counter(results, "market_histogram")),
            decision_histogram=cast(Counter[int], _counter(results, "decision_histogram")),
            quantity_histogram=cast(Counter[int], _counter(results, "quantity_histogram")),
        )
        write_analysis(analysis, settings.report_dir)
        _write_json(
            settings.report_dir / "resolved-settings.json",
            {"bc_data": settings.model_dump(mode="json")},
        )
        return {
            "dataset_dir": str(settings.output_dir),
            "dataset_id": manifest["dataset_id"],
            "manifest_sha256": sha256_file(settings.output_dir / "manifest.json"),
            "accepted_episodes": accepted_episodes,
            "rejected_episodes": len(rejected),
            "source_episodes_considered": len(locators),
            "report_dir": str(settings.report_dir),
        }
    finally:
        if moved or staging_root.is_relative_to(temporary_root):
            shutil.rmtree(staging_root, ignore_errors=True)


__all__ = ["prepare_dataset", "resolve_paths"]
