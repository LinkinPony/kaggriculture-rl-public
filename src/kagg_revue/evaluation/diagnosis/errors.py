"""Classify teacher-forced BC errors by whether they change the executed plan."""

import json
import time
from collections import Counter
from pathlib import Path
from typing import Any

import hydra
import numpy as np
import torch
from omegaconf import DictConfig, OmegaConf
from pydantic import Field

from kagg_revue.artifacts.io import digest, write_json
from kagg_revue.configuration import FrozenSettings
from kagg_revue.evaluation.diagnosis.imitation import arrays
from kagg_revue.evaluation.diagnosis.statistics import MARKET_NAMES, UNIT_NAMES
from kagg_revue.policy.checkpoints import load_policy
from kagg_revue.policy.memory.policy import MemoryPolicy

MOVES = {1: (0, -1), 2: (0, 1), 3: (1, 0), 4: (-1, 0)}


class Options(FrozenSettings):
    """One frozen actor scored on the validation seats of one dataset."""

    output: Path
    actor: Path
    manifest: Path
    split: str = "val"
    device: str = "cuda:0"
    chunk_turns: int = Field(default=48, ge=1)
    memory_fraction: float = Field(default=0.06, gt=0, le=0.2)
    trajectories: int = Field(default=0, ge=0, description="0 scores every trajectory")


def _unit_name(op: int) -> str:
    if op == 0:
        return "PASS"
    if op in MOVES:
        return "MOVE"
    if 5 <= op < 17:
        return "PICKUP"
    if op == 17:
        return "DROP"
    if 18 <= op < 30:
        return "PLACE"
    return UNIT_NAMES.get(op, str(op))


@torch.inference_mode()
def teacher_forced(
    actor: MemoryPolicy, data: dict[str, np.ndarray[Any, Any]], seat: int, options: Options
) -> tuple[np.ndarray[Any, Any], np.ndarray[Any, Any], np.ndarray[Any, Any], np.ndarray[Any, Any]]:
    """Return argmax predictions, labels, credited fields and observations of one seat."""
    device = next(actor.parameters()).device
    state = actor.memory.temporal.empty(1, device)
    predictions, credited = [], []
    turns = len(data["observations"])
    for start in range(0, turns, options.chunk_turns):
        stop = min(start + options.chunk_turns, turns)
        obs = torch.from_numpy(np.array(data["observations"][start:stop, seat : seat + 1])).to(
            device
        )
        chosen = torch.from_numpy(
            np.array(data["actions"][start:stop, seat : seat + 1], dtype=np.int64)
        ).to(device)
        eligible = torch.from_numpy(np.array(data["eligible"][start:stop, seat])).to(device)
        steps = torch.arange(start, stop, device=device)
        with torch.autocast(device.type, dtype=torch.bfloat16, enabled=device.type == "cuda"):
            _, logits, state = actor.sequence(obs, steps, state, chosen)
        fields = actor.field_weights(chosen[:, 0], steps, obs[:, 0]) * eligible[:, None]
        predictions.append(logits[:, 0].float().argmax(-1).cpu().numpy())
        credited.append((fields > 0).cpu().numpy())
    labels = np.array(data["actions"][:, seat], dtype=np.int64)
    observations = np.array(data["observations"][:, seat])
    return np.concatenate(predictions), labels, np.concatenate(credited), observations


def _positions(observations: np.ndarray[Any, Any], actor: MemoryPolicy) -> np.ndarray[Any, Any]:
    base = actor.layout.observation
    units = observations[
        :, base.board_features : base.board_features + base.units * base.unit_features
    ].reshape(len(observations), base.units, base.unit_features)
    size = actor.layout.board_size
    xy = np.rint(units[..., 2:4].astype(np.float32) * (size - 1)).astype(np.int64)
    present = units[..., 0] > 0
    return np.where(present[..., None], xy, -1)


def _destination(
    labels: np.ndarray[Any, Any], xy: np.ndarray[Any, Any], turn: int, unit: int, size: int
) -> tuple[int, int] | None:
    """Follow the teacher's own later moves to the tile of its next on-tile choice."""
    day = turn // 24
    for later in range(turn, min(len(labels), (day + 1) * 24)):
        if xy[later, unit, 0] < 0:
            return None
        target = int(labels[later, 8 * unit])
        here = 1 + int(xy[later, unit, 0]) + size * int(xy[later, unit, 1])
        if target == 0 or target == here:
            return int(xy[later, unit, 0]), int(xy[later, unit, 1])
    return None


def classify(
    predictions: np.ndarray[Any, Any],
    labels: np.ndarray[Any, Any],
    credited: np.ndarray[Any, Any],
    xy: np.ndarray[Any, Any],
    units: int,
    size: int,
) -> dict[str, Counter[str]]:
    """Separate path-equivalent moves from choices that change the teacher's plan."""
    result: dict[str, Counter[str]] = {
        "target": Counter(),
        "target_by_slot": Counter(),
        "target_by_hour": Counter(),
        "operation": Counter(),
        "market": Counter(),
        "market_by_slot": Counter(),
        "market_by_hour": Counter(),
        "quantity": Counter(),
    }
    work = 8 * units
    for turn in range(len(labels)):
        hour = turn % 24
        for unit in range(units):
            column = 8 * unit
            if not credited[turn, column]:
                continue
            x, y = int(xy[turn, unit, 0]), int(xy[turn, unit, 1])
            here = 1 + x + size * y
            teacher, guess = int(labels[turn, column]), int(predictions[turn, column])
            slot = "farmer" if unit == 0 else f"hand{min(unit, 9)}"
            result["target_by_slot"][f"{slot}/n"] += 1
            result["target_by_hour"][f"{hour:02d}/n"] += 1
            kind_t = "pass" if teacher == 0 else ("work" if teacher == here else "move")
            kind_g = "pass" if guess == 0 else ("work" if guess == here else "move")
            if teacher == guess:
                result["target"]["correct"] += 1
            else:
                result["target_by_slot"][f"{slot}/wrong"] += 1
                result["target_by_hour"][f"{hour:02d}/wrong"] += 1
                label = f"{kind_t}->{kind_g}"
                if kind_t == "move" and kind_g == "move":
                    goal = _destination(labels, xy, turn, unit, size)
                    gx, gy = (guess - 1) % size, (guess - 1) // size
                    if goal is not None and abs(gx - goal[0]) + abs(gy - goal[1]) < abs(
                        x - goal[0]
                    ) + abs(y - goal[1]):
                        label += ":equivalent"
                    else:
                        label += ":different"
                result["target"][label] += 1
            if teacher == here and guess == here and credited[turn, column + 1]:
                t_op, g_op = int(labels[turn, column + 1]), int(predictions[turn, column + 1])
                if t_op == g_op:
                    result["operation"]["correct"] += 1
                else:
                    result["operation"][f"{_unit_name(t_op)}->{_unit_name(g_op)}"] += 1
        for order in range(10):
            column = work + 2 * order
            if not credited[turn, column]:
                continue
            teacher, guess = int(labels[turn, column]), int(predictions[turn, column])
            result["market_by_slot"][f"{order}/n"] += 1
            result["market_by_hour"][f"{hour:02d}/n"] += 1
            if teacher == guess:
                result["market"]["correct"] += 1
                if credited[turn, column + 1]:
                    delta = int(predictions[turn, column + 1]) - int(labels[turn, column + 1])
                    bucket = "exact" if delta == 0 else ("low" if delta < 0 else "high")
                    result["quantity"][f"{MARKET_NAMES[teacher]}/{bucket}"] += 1
            else:
                result["market_by_slot"][f"{order}/wrong"] += 1
                result["market_by_hour"][f"{hour:02d}/wrong"] += 1
                result["market"][f"{MARKET_NAMES[teacher]}->{MARKET_NAMES[guess]}"] += 1
    return result


@hydra.main(version_base=None, config_path="../../../../configs", config_name="diagnosis_errors")
def main(config: DictConfig) -> None:
    """Score the configured split once and publish additive error counters."""
    options = Options.model_validate(OmegaConf.to_container(config.analysis, resolve=True))
    options.output.mkdir(parents=True, exist_ok=True)
    manifest = json.loads(options.manifest.read_text())
    device = torch.device(options.device)
    if device.type == "cuda":
        torch.cuda.set_device(device)
        torch.cuda.set_per_process_memory_fraction(options.memory_fraction, device)
    actor, _ = load_policy(options.actor, device)
    assert isinstance(actor, MemoryPolicy)
    actor.eval()
    units, size = actor.layout.observation.units, actor.layout.board_size
    totals: dict[str, Counter[str]] = {}
    started, scored = time.monotonic(), 0
    for shard in manifest["shards"]:
        if shard["split"] != options.split:
            continue
        data = arrays(options.manifest.parent, shard)
        for index, _ in enumerate(shard["task"]["seats"]):
            predictions, labels, credited, observations = teacher_forced(
                actor, data, index, options
            )
            counts = classify(
                predictions, labels, credited, _positions(observations, actor), units, size
            )
            for key, counter in counts.items():
                totals.setdefault(key, Counter()).update(counter)
            scored += 1
            if options.trajectories and scored >= options.trajectories:
                break
        if options.trajectories and scored >= options.trajectories:
            break
    report = {
        "actor": str(options.actor),
        "actor_sha256": digest(options.actor),
        "manifest": str(options.manifest),
        "trajectories": scored,
        "seconds": time.monotonic() - started,
        "counts": {key: dict(counter.most_common()) for key, counter in totals.items()},
    }
    write_json(options.output / "errors.json", report)
    print(json.dumps({"trajectories": scored, "seconds": report["seconds"]}))


if __name__ == "__main__":
    main()
