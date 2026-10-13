"""Supervise periodic replay acquisition independently of the interactive session."""

import fcntl
import multiprocessing
import os
import signal
import threading
import time
from datetime import UTC, datetime
from types import FrameType

import hydra
from omegaconf import DictConfig, OmegaConf

from kagg_revue.artifacts.io import write_json
from kagg_revue.datasets.watching.config import WatchSettings
from kagg_revue.datasets.watching.records import event, utc_now


def _cycle(config: WatchSettings) -> None:
    """Isolate network workers so the supervisor can recover from a hung request."""
    from kagg_revue.datasets.watching.collection import collect

    try:
        collect(config)
    except Exception as error:
        event(config.raw, {"event": "cycle_failed", "error_type": type(error).__name__})
        raise SystemExit(1) from None


def supervise(config: WatchSettings) -> None:
    """Run a single locked collector, with timeout recovery and graceful stopping."""
    config.raw.mkdir(parents=True, exist_ok=True)
    with (config.raw / "collector.lock").open("a+") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise SystemExit("a collector already holds this archive lock") from None
        stop = threading.Event()

        def stopping(signum: int, frame: FrameType | None) -> None:
            stop.set()

        signal.signal(signal.SIGTERM, stopping)
        signal.signal(signal.SIGINT, stopping)
        write_json(config.raw / "resolved-config.json", config.model_dump(mode="json"))
        status = {"pid": os.getpid(), "started_utc": utc_now(), "team_id": config.team_id}
        event(config.raw, {"event": "collector_started", **status})
        context = multiprocessing.get_context("spawn")
        exitcode = None
        while not stop.is_set():
            write_json(
                config.raw / "status.json",
                {**status, "state": "collecting", "updated_utc": utc_now()},
            )
            process = context.Process(target=_cycle, args=(config,))
            process.start()
            deadline = time.monotonic() + config.cycle_timeout_seconds
            while process.is_alive() and not stop.is_set() and time.monotonic() < deadline:
                process.join(timeout=1)
            if process.is_alive():
                process.terminate()
                process.join(timeout=5)
                if process.is_alive():
                    process.kill()
                    process.join()
                event(
                    config.raw, {"event": "cycle_interrupted" if stop.is_set() else "cycle_timeout"}
                )
            exitcode = process.exitcode
            process.close()
            if config.once or stop.is_set():
                break
            next_poll = datetime.fromtimestamp(time.time() + config.poll_seconds, UTC).isoformat()
            write_json(
                config.raw / "status.json",
                {
                    **status,
                    "state": "waiting",
                    "updated_utc": utc_now(),
                    "last_exitcode": exitcode,
                    "next_poll_utc": next_poll,
                },
            )
            stop.wait(config.poll_seconds)
        write_json(
            config.raw / "status.json",
            {**status, "state": "stopped", "updated_utc": utc_now(), "last_exitcode": exitcode},
        )
        event(config.raw, {"event": "collector_stopped"})
        if config.once and exitcode != 0:
            raise SystemExit(exitcode or 1)


@hydra.main(version_base=None, config_path="../../../../configs", config_name="replay_watch_mm_pq")
def main(configuration: DictConfig) -> None:
    """Resolve the persistent collection protocol through Hydra."""
    config = WatchSettings.model_validate(OmegaConf.to_container(configuration.watch, resolve=True))
    supervise(config)


if __name__ == "__main__":
    main()
