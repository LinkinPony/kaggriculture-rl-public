"""Record passive training health through a requested number of committed updates."""

import json
import math
import os
import shutil
import time
from pathlib import Path
from typing import Any

import hydra
from omegaconf import DictConfig, OmegaConf
from pydantic import Field

from kagg_revue.artifacts.io import digest, write_json
from kagg_revue.configuration import FrozenSettings
from kagg_revue.evaluation.checkpoints.supervisor import health


class Tracking(FrozenSettings):
    """Observe a workflow without changing its training or stopping its processes."""

    run: Path
    workflow: Path
    output: Path
    target_update: int = Field(gt=0)
    interval_seconds: float = Field(default=10.0, gt=0, le=60)
    stale_seconds: float = Field(default=240.0, gt=0)
    minimum_free_mib: int = Field(default=8192, ge=0)


def check_metrics(row: dict[str, Any], protocol: dict[str, Any]) -> None:
    """Reject nonfinite learning diagnostics, changed rewards, rates or rank counts."""
    if row["physical_games"] != protocol["games"]:
        raise ValueError("physical game count differs from the frozen protocol")
    workers = row["workers"]
    world = len(protocol["execution"]["devices"])
    if len(workers) != world or {w["rank"] for w in workers} != set(range(world)):
        raise ValueError("metrics do not cover every training rank")
    update = row["update"]
    warmup = protocol.get("learning_rate_warmup_updates", 0)
    scale = min(update / warmup, 1.0) if warmup else 1.0
    for worker in workers:
        if not set(worker["reward_values"]).issubset({-1.0, 0.0, 1.0}):
            raise ValueError("terminal reward differs from pure WDL")
        optimization = worker["optimization"]
        for key, value in optimization.items():
            if isinstance(value, (int, float)) and not math.isfinite(value):
                raise ValueError(f"nonfinite optimization diagnostic: {key}")
        for key in ("actor_learning_rate", "critic_learning_rate"):
            if not math.isclose(optimization[key], protocol[key] * scale, rel_tol=1e-6):
                raise ValueError(f"warmup learning rate differs: {key}")
        if optimization["reference_kl_weight"] != protocol.get("reference_kl_weight", 0.0):
            raise ValueError("reference KL weight changed")
        if optimization["critic_steps"] <= 0 or optimization["actor_steps"] < 0:
            raise ValueError("optimizer did not advance")


def track(config: Tracking) -> None:
    """Append health observations and preserve the requested final checkpoint."""
    config.output.mkdir(parents=True, exist_ok=True)
    write_json(config.output / "tracking-config.json", config.model_dump(mode="json"))
    started = time.time()
    reported: tuple[str, int] | None = None
    verified = 0
    record: dict[str, Any] = {}
    try:
        with (config.output / "health.jsonl").open("a") as stream:
            while True:
                workflow = json.loads((config.workflow / "status.json").read_text())
                os.kill(workflow["pid"], 0)
                if workflow["status"] not in {"running", "attached"}:
                    raise RuntimeError(f"workflow is {workflow['status']}")
                record = {"time": time.time(), "stage": workflow["stage"]}
                status = config.run / "run-status.json"
                if status.exists():
                    identity = json.loads(status.read_text())
                    record.update(health(config.run, identity["pid"]))
                    if record["training_update"] and (
                        record["training_heartbeat_age"] > config.stale_seconds
                    ):
                        raise RuntimeError("training heartbeat is stale")
                    if min(gpu[1] for gpu in record["gpus"]) < config.minimum_free_mib:
                        raise RuntimeError("GPU free memory is below the monitoring threshold")
                elif time.time() - started > 900:
                    raise RuntimeError("RL bootstrap has not completed within 15 minutes")
                stream.write(json.dumps(record) + "\n")
                stream.flush()
                state = json.loads((config.run / "state.json").read_text())
                rows = [r for r in state["records"] if r["update"] <= config.target_update]
                for row in rows:
                    if row["update"] > verified:
                        if row["update"] != verified + 1:
                            raise ValueError("committed update sequence has a gap")
                        check_metrics(row, state["protocol"])
                        verified = row["update"]
                current = (record["stage"], record.get("training_update", 0))
                summary = {
                    **record,
                    "verified_update": verified,
                    "checkpoint_update": state["completed_update"],
                    "target_update": config.target_update,
                }
                write_json(config.output / "status.json", {"status": "monitoring", **summary})
                if current != reported:
                    print(json.dumps(summary), flush=True)
                    reported = current
                if verified >= config.target_update:
                    name = f"checkpoints/update-{config.target_update:06d}.pt"
                    target = config.output / Path(name).name
                    shutil.copy2(config.run / name, target)
                    if digest(target) != state["members"][name]:
                        raise ValueError("preserved checkpoint differs from the committed ledger")
                    write_json(config.output / "updates.json", rows)
                    completion = {
                        "status": "complete",
                        "started_at": started,
                        **summary,
                        "checkpoint": str(target),
                        "checkpoint_sha256": state["members"][name],
                        "run_id": state["run_id"],
                    }
                    write_json(config.output / "completion.json", completion)
                    write_json(config.output / "status.json", completion)
                    print(json.dumps({"status": "complete", **summary}), flush=True)
                    return
                time.sleep(config.interval_seconds)
    except BaseException as error:
        alert = {
            "status": "failed",
            "time": time.time(),
            "error": f"{type(error).__name__}: {error}",
            "verified_update": verified,
            "last_health": record,
        }
        write_json(config.output / "alert.json", alert)
        write_json(config.output / "status.json", alert)
        raise


@hydra.main(
    version_base=None, config_path="../../../configs", config_name="monitor_s100901_first20"
)
def main(configuration: DictConfig) -> None:
    """Run a passive bounded observer from a Hydra configuration."""
    track(Tracking.model_validate(OmegaConf.to_container(configuration.tracking, resolve=True)))


if __name__ == "__main__":
    main()
