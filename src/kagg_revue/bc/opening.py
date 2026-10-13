"""Streaming discovery of structurally distinct replay openings."""

from __future__ import annotations

import hashlib
import re
import zipfile
from collections import Counter
from collections.abc import Mapping, Sequence
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from typing import IO, Any, cast

import orjson

from kagg_revue.bc.actions import ActionEncodingError, ReplayActionEncoder
from kagg_revue.bc.data_config import OpeningDiversitySettings, ReplayContract
from kagg_revue.bc.replay import EpisodeLocator
from kagg_revue.native import _revue_native as native

_STEPS_FIELD = re.compile(rb'"steps"\s*:\s*\[')
_READ_SIZE = 64 * 1024
_MAXIMUM_HEADER_BYTES = 4 * 1024 * 1024


@dataclass(frozen=True)
class OpeningCandidate:
    """One complete source replay represented by token-only seat prefixes."""

    locator: EpisodeLocator
    seat_turn_tokens: tuple[tuple[tuple[int, ...], ...], ...]


@dataclass(frozen=True)
class OpeningScanTask:
    """A bounded group of ZIP members scanned by one worker process."""

    locators: tuple[EpisodeLocator, ...]
    prefix_turns: int
    agents: int
    max_market_orders: int


@dataclass(frozen=True)
class OpeningScanResult:
    """Mergeable candidate and rejection records from one scan task."""

    candidates: tuple[OpeningCandidate, ...]
    rejected: tuple[Mapping[str, str], ...]


def _json_array_prefix(stream: IO[bytes], count: int) -> list[Any]:
    """Parse only the first values of the top-level ``steps`` array."""
    header = bytearray()
    tail = b""
    while True:
        chunk = stream.read(_READ_SIZE)
        if not chunk:
            raise ValueError("replay ended before its steps array")
        header.extend(chunk)
        matched = _STEPS_FIELD.search(header)
        if matched is not None:
            tail = bytes(header[matched.end() :])
            break
        if len(header) > _MAXIMUM_HEADER_BYTES:
            raise ValueError("replay header exceeds the bounded opening scanner")

    values: list[Any] = []
    current = bytearray()
    depth = 0
    in_string = False
    escaped = False
    started = False

    def consume(chunk: bytes) -> bool:
        nonlocal depth, escaped, in_string, started
        for byte in chunk:
            if not started:
                if byte in b" \t\r\n,":
                    continue
                if byte == ord("]"):
                    raise ValueError("replay steps ended before the requested opening")
                if byte != ord("["):
                    raise ValueError("replay step is not an agent array")
                started = True
                depth = 1
                current.append(byte)
                continue

            current.append(byte)
            if in_string:
                if escaped:
                    escaped = False
                elif byte == ord("\\"):
                    escaped = True
                elif byte == ord('"'):
                    in_string = False
                continue
            if byte == ord('"'):
                in_string = True
            elif byte in (ord("["), ord("{")):
                depth += 1
            elif byte in (ord("]"), ord("}")):
                depth -= 1
                if depth < 0:
                    raise ValueError("replay opening has unbalanced JSON containers")
                if depth == 0:
                    values.append(orjson.loads(current))
                    current.clear()
                    started = False
                    if len(values) == count:
                        return True
        return False

    if consume(tail):
        return values
    while chunk := stream.read(_READ_SIZE):
        if consume(chunk):
            return values
    raise ValueError("replay ended inside the requested opening")


def _mapping(value: Any, field: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{field} must be a mapping")
    return cast(Mapping[str, Any], value)


def _scan_member(
    archive: zipfile.ZipFile,
    locator: EpisodeLocator,
    task: OpeningScanTask,
    codec: ReplayActionEncoder,
) -> OpeningCandidate:
    with archive.open(locator.entry) as stream:
        steps = _json_array_prefix(stream, task.prefix_turns + 1)
    seat_tokens: list[list[tuple[int, ...]]] = [[] for _ in range(task.agents)]
    for turn, raw_step in enumerate(steps[1:], start=1):
        if not isinstance(raw_step, list) or len(raw_step) != task.agents:
            raise ValueError(f"steps[{turn}] has the wrong agent count")
        for seat, raw_state in enumerate(raw_step):
            state = _mapping(raw_state, f"steps[{turn}][{seat}]")
            action = _mapping(state.get("action"), f"steps[{turn}][{seat}].action")
            hands = action.get("hands")
            if not isinstance(hands, list):
                raise ValueError(f"steps[{turn}][{seat}].action.hands must be a list")
            encoded = codec.encode(action, 1 + len(hands), task.max_market_orders)
            seat_tokens[seat].append(tuple(encoded.tokens))
    return OpeningCandidate(
        locator=locator,
        seat_turn_tokens=tuple(tuple(turns) for turns in seat_tokens),
    )


def _scan_task(task: OpeningScanTask) -> OpeningScanResult:
    candidates: list[OpeningCandidate] = []
    rejected: list[Mapping[str, str]] = []
    codec = ReplayActionEncoder(cast(Mapping[str, Any], native.action_codec_spec()))
    by_archive: dict[Path, list[EpisodeLocator]] = {}
    for locator in task.locators:
        by_archive.setdefault(locator.archive, []).append(locator)
    for archive_path, locators in by_archive.items():
        with zipfile.ZipFile(archive_path) as archive:
            for locator in locators:
                try:
                    candidates.append(_scan_member(archive, locator, task, codec))
                except (
                    ActionEncodingError,
                    KeyError,
                    TypeError,
                    ValueError,
                    zipfile.BadZipFile,
                ) as error:
                    rejected.append(
                        {
                            "archive": archive_path.name,
                            "entry": locator.entry,
                            "reason": "opening_scan_failed",
                            "detail": f"{type(error).__name__}: {error}",
                        }
                    )
    return OpeningScanResult(tuple(candidates), tuple(rejected))


def scan_openings(
    locators: Sequence[EpisodeLocator],
    settings: OpeningDiversitySettings,
    contract: ReplayContract,
    workers: int,
) -> OpeningScanResult:
    """Scan bounded replay prefixes in parallel without inflating full JSON members."""
    group_size = 16
    tasks = [
        OpeningScanTask(
            locators=tuple(locators[start : start + group_size]),
            prefix_turns=settings.prefix_turns,
            agents=contract.agents,
            max_market_orders=contract.max_market_orders,
        )
        for start in range(0, len(locators), group_size)
    ]
    candidates: list[OpeningCandidate] = []
    rejected: list[Mapping[str, str]] = []
    with ProcessPoolExecutor(max_workers=min(workers, len(tasks))) as executor:
        futures = [executor.submit(_scan_task, task) for task in tasks]
        for completed, future in enumerate(as_completed(futures), start=1):
            result = future.result()
            candidates.extend(result.candidates)
            rejected.extend(result.rejected)
            if completed == len(tasks) or completed % 16 == 0:
                print(
                    orjson.dumps(
                        {
                            "opening_scan_groups": completed,
                            "total_groups": len(tasks),
                            "candidates": len(candidates),
                            "rejected": len(rejected),
                        },
                        option=orjson.OPT_SORT_KEYS,
                    ).decode(),
                    flush=True,
                )
    candidates.sort(
        key=lambda candidate: (
            candidate.locator.source_date,
            int(Path(candidate.locator.entry).stem),
        )
    )
    rejected.sort(key=lambda row: (row["archive"], int(Path(row["entry"]).stem)))
    return OpeningScanResult(tuple(candidates), tuple(rejected))


def _prefix_digest(turns: Sequence[Sequence[int]], horizon: int) -> str:
    payload = orjson.dumps(turns[:horizon])
    return hashlib.sha256(payload).hexdigest()


def _candidate_features(
    candidate: OpeningCandidate,
    horizons: Sequence[int],
) -> tuple[tuple[tuple[int, str], ...], str, tuple[str, ...]]:
    features: list[tuple[int, str]] = []
    full: list[str] = []
    for seat_turns in candidate.seat_turn_tokens:
        seat_hashes = [_prefix_digest(seat_turns, horizon) for horizon in horizons]
        features.extend(zip(horizons, seat_hashes, strict=True))
        full.append(seat_hashes[-1])
    paired = hashlib.sha256("\0".join(sorted(full)).encode()).hexdigest()
    return tuple(features), paired, tuple(full)


def select_diverse_openings(
    scan: OpeningScanResult,
    settings: OpeningDiversitySettings,
) -> tuple[tuple[EpisodeLocator, ...], dict[str, object]]:
    """Greedily cover empirical prefix clusters without favoring named actions."""
    decorated: list[
        tuple[OpeningCandidate, tuple[tuple[int, str], ...], str, tuple[str, ...], bytes]
    ] = []
    source_counts: Counter[tuple[int, str]] = Counter()
    for candidate in scan.candidates:
        features, paired, full = _candidate_features(candidate, settings.horizons)
        tie = hashlib.sha256(
            f"{settings.seed}:{candidate.locator.source_date}:{candidate.locator.entry}".encode()
        ).digest()
        decorated.append((candidate, features, paired, full, tie))
        source_counts.update(features)

    selected: list[
        tuple[OpeningCandidate, tuple[tuple[int, str], ...], str, tuple[str, ...], bytes]
    ] = []
    selected_counts: Counter[tuple[int, str]] = Counter()
    exact_counts: Counter[str] = Counter()
    remaining = decorated
    while remaining and len(selected) < settings.maximum_episodes:
        eligible = [
            row
            for row in remaining
            if exact_counts[row[2]] < settings.maximum_identical_prefixes
        ]
        if not eligible:
            break

        def priority(
            row: tuple[
                OpeningCandidate,
                tuple[tuple[int, str], ...],
                str,
                tuple[str, ...],
                bytes,
            ],
        ) -> tuple[int, int, float, bytes]:
            counts = [selected_counts[feature] for feature in row[1]]
            rarity = sum(1.0 / source_counts[feature] for feature in row[1])
            return (sum(value == 0 for value in counts), -sum(counts), rarity, row[4])

        chosen = max(eligible, key=priority)
        selected.append(chosen)
        selected_counts.update(chosen[1])
        exact_counts[chosen[2]] += 1
        remaining = [row for row in remaining if row is not chosen]

    records = [
        {
            "archive": row[0].locator.archive.name,
            "entry": row[0].locator.entry,
            "source_date": row[0].locator.source_date,
            "paired_prefix_sha256": row[2],
            "seat_prefix_sha256": list(row[3]),
        }
        for row in selected
    ]
    coverage: list[dict[str, object]] = []
    for horizon in settings.horizons:
        source = Counter(
            feature for row in decorated for feature in row[1] if feature[0] == horizon
        )
        selected_coverage = Counter(
            feature for row in selected for feature in row[1] if feature[0] == horizon
        )
        coverage.append(
            {
                "horizon": horizon,
                "source_unique_prefixes": len(source),
                "selected_unique_prefixes": len(selected_coverage),
                "selected_maximum_cluster": max(selected_coverage.values(), default=0),
            }
        )
    stable: dict[str, object] = {
        "schema_version": "opening-diversity-selection-v1",
        "semantics": (
            "greedy multi-horizon coverage of recorded token-only prefixes; "
            "quantities, scores, agent names, and named target actions are ignored"
        ),
        "settings": settings.model_dump(mode="json"),
        "source_candidates": len(scan.candidates) + len(scan.rejected),
        "scanned_candidates": len(scan.candidates),
        "scan_rejected": list(scan.rejected),
        "selected_episodes": len(selected),
        "coverage": coverage,
        "episodes": records,
    }
    stable["selection_id"] = hashlib.sha256(
        orjson.dumps(stable, option=orjson.OPT_SORT_KEYS)
    ).hexdigest()
    return tuple(row[0].locator for row in selected), stable


__all__ = [
    "OpeningCandidate",
    "OpeningScanResult",
    "scan_openings",
    "select_diverse_openings",
]
