"""Share request pacing and Retry-After deadlines between replay workers."""

import json
import threading
import time
from pathlib import Path

from kagg_revue.artifacts.io import write_json


class RequestGate:
    """Pace request starts and persist a server cooldown across process restarts."""

    def __init__(self, raw: Path, interval: float, maximum_backoffs: int) -> None:
        """Restore any outstanding server-directed pause without resetting it."""
        self.path = raw / "rate-limit.json"
        self.interval = interval
        self.maximum_backoffs = maximum_backoffs
        self.lock = threading.Lock()
        self.next_request = 0.0
        self.backoffs = 0
        self.stopped = False
        self.paused_until = (
            float(json.loads(self.path.read_text())["retry_not_before"])
            if self.path.exists()
            else 0.0
        )

    def wait(self) -> bool:
        """Reserve one request start, allowing a worker to publish new cooldowns."""
        while True:
            with self.lock:
                if self.stopped:
                    return False
                now = time.time()
                delay = max(self.next_request, self.paused_until) - now
                if delay <= 0:
                    self.next_request = now + self.interval
                    return True
            time.sleep(min(delay, 30))

    def defer(self, seconds: int) -> None:
        """Stop new requests immediately when any worker receives HTTP 429."""
        with self.lock:
            self.backoffs += 1
            self.paused_until = max(self.paused_until, time.time() + seconds)
            self.stopped = self.backoffs > self.maximum_backoffs
            write_json(
                self.path,
                {
                    "retry_not_before": self.paused_until,
                    "retry_after": seconds,
                    "backoffs": self.backoffs,
                },
            )
