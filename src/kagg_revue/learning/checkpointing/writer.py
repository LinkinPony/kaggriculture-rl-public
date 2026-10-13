"""Overlap checkpoint serialization and storage with the next complete update."""

import json
import time
from concurrent.futures import Future, ThreadPoolExecutor
from dataclasses import asdict
from types import TracebackType
from typing import Any

import torch

from kagg_revue.artifacts.serialization import save
from kagg_revue.artifacts.snapshot import Snapshot, capture
from kagg_revue.learning.config import Experiment
from kagg_revue.learning.distributed import rank_world, rng_snapshot
from kagg_revue.learning.optimization.learner import Learner
from kagg_revue.learning.settings import RuntimeSettings
from kagg_revue.learning.storage.publication import publish as publish_storage
from kagg_revue.learning.storage.roles import checkpoint_due


class CheckpointWriter:
    """Keep at most one immutable snapshot; publish it before appending another update."""

    def __init__(
        self, config: Experiment, settings: RuntimeSettings, state: dict[str, Any], learner: Learner
    ) -> None:
        """Only rank zero owns the background writer; all ranks publish the same receipt."""
        self.config, self.settings, self.state, self.learner = config, settings, state, learner
        self.rank, self.world = rank_world()
        self.asynchronous = bool(config.execution and config.execution.async_checkpoint)
        self.pool = ThreadPoolExecutor(max_workers=1, thread_name_prefix="checkpoint")
        self.pending: Future[dict[str, Any]] | None = None
        self.update: int | None = None

    def __enter__(self) -> "CheckpointWriter":
        """Own the writer thread for this training session."""
        return self

    def __exit__(
        self,
        kind: type[BaseException] | None,
        error: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        """Join outstanding I/O even on training failure; never publish a failed write."""
        self.pool.shutdown(wait=True)

    def record(self, update: int, metrics: dict[str, Any]) -> None:
        """Append metrics only after the previous checkpoint's ledger has been published."""
        if self.update is not None:
            raise RuntimeError("finish the previous checkpoint before appending update metrics")
        self.state["records"].append(metrics)
        if checkpoint_due(self.config, update):
            self.submit()
        # The next PFSP draw must see a newly scheduled pool member.
        if (
            not self.asynchronous
            or update % self.config.population.snapshot_interval == 0
            or update == self.config.updates
        ):
            self.finish()

    def submit(self) -> None:
        """Freeze weights, optimizer, PFSP and both rank RNGs at the current update boundary."""
        if self.update is not None:
            raise RuntimeError("checkpoint queue is bounded to one snapshot")
        state, learner = self.state, self.learner
        if not state["records"] or state["records"][-1]["update"] <= state["completed_update"]:
            return
        self.update = state["records"][-1]["update"]
        rng = rng_snapshot(learner.device)
        if self.rank == 0:
            submitted = time.time()
            started = time.perf_counter()
            payload = {
                "layout": asdict(learner.policy.layout),
                "model": learner.policy.state_dict(),
                "settings": self.settings.model_dump(mode="json"),
                "update": self.update,
                "critic": learner.critic.state_dict(),
                "actor_optimizer": learner.actor_optimizer.state_dict(),
                "critic_optimizer": learner.critic_optimizer.state_dict(),
                "rng": rng,
                **({"pfsp": state["pfsp"]} if "pfsp" in state else {}),
                "lineage": {
                    "run_id": state["run_id"],
                    "kind": "reinforcement_learning",
                    "root_sha256": state["members"]["initial.pt"],
                    "parent_sha256": state["members"][state["latest"]],
                },
            }
            snapshot = capture(payload, learner.device)
            self.pending = self.pool.submit(
                self._write, self.update, snapshot, submitted, time.perf_counter() - started
            )

    def _write(
        self, update: int, snapshot: Snapshot, submitted: float, snapshot_seconds: float
    ) -> dict[str, Any]:
        started = time.perf_counter()
        payload = snapshot.wait()
        copy_wait = time.perf_counter() - started
        checksum = save(payload, self.config.output_dir / f"checkpoints/update-{update:06d}.pt")
        return {
            "update": update,
            "sha256": checksum,
            "submitted_at": submitted,
            "finished_at": time.time(),
            "snapshot_seconds": snapshot_seconds,
            "copy_wait_seconds": copy_wait,
            "background_seconds": time.perf_counter() - started,
        }

    def finish(self) -> None:
        """Commit one complete archive on every rank before live PFSP/records advance again."""
        if self.update is None:
            return
        messages: list[Any] = [None]
        if self.rank == 0:
            assert self.pending is not None
            try:
                messages[0] = {"receipt": self.pending.result()}
            except BaseException as error:
                messages[0] = {"error": f"{type(error).__name__}: {error}"}
        if self.world > 1:
            torch.distributed.broadcast_object_list(messages, src=0)
        message = messages[0]
        if "error" in message:
            raise RuntimeError(f"background checkpoint failed: {message['error']}")
        receipt = message["receipt"]
        state, update = self.state, self.update
        if state["records"][-1]["update"] != update:
            raise RuntimeError("live ledger advanced beyond its immutable checkpoint snapshot")
        previous = state["completed_update"]
        name = f"checkpoints/update-{update:06d}.pt"
        state["members"][name] = receipt["sha256"]
        state.update(completed_update=update, latest=name)
        if update % self.config.population.snapshot_interval == 0:
            from kagg_revue.learning.matchmaking.pool import snapshot

            snapshot(self.config, state, name)
        publish_storage(self.config, state)
        if self.rank == 0:
            with (self.config.output_dir / "metrics.jsonl").open("a") as stream:
                for row in state["records"][previous:update]:
                    stream.write(json.dumps(row) + "\n")
            receipt["published_at"] = time.time()
            with (self.config.output_dir / "checkpoint-timing.jsonl").open("a") as stream:
                stream.write(json.dumps(receipt) + "\n")
        self.pending, self.update = None, None

    def flush(self) -> None:
        """Commit the pending snapshot, then save any later update on graceful shutdown."""
        self.finish()
        self.submit()
        self.finish()
