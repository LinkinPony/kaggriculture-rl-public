"""Forward cancellation through supervised training stages without allowing a handoff."""

import signal
import subprocess
from types import FrameType
from typing import Any


class Supervisor:
    """Latch stop requests even when no child is active between stages."""

    def __init__(self) -> None:
        """Install temporary handlers before launching or preparing a stage."""
        self.cancelled = False
        self.child: subprocess.Popen[bytes] | None = None
        self.handlers = {
            number: signal.signal(number, self.stop)
            for number in (signal.SIGTERM, signal.SIGINT)
        }

    def stop(self, number: int, frame: FrameType | None) -> None:
        """Remember cancellation and forward it to the active process."""
        self.cancelled = True
        if self.child is not None and self.child.poll() is None:
            self.child.send_signal(number)

    def run(self, command: list[str], **kwargs: Any) -> int | None:
        """Wait for one child; return no exit code if the workflow was cancelled."""
        if self.cancelled:
            return None
        self.child = subprocess.Popen(command, stdin=subprocess.DEVNULL, **kwargs)
        try:
            if self.cancelled:
                self.child.terminate()
            result = self.child.wait()
            return None if self.cancelled else result
        finally:
            if self.child.poll() is None:
                self.child.terminate()
                self.child.wait()
            self.child = None

    def close(self) -> None:
        """Restore the caller's signal handlers after all children have exited."""
        for number, handler in self.handlers.items():
            signal.signal(number, handler)
