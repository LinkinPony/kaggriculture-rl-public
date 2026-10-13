"""Standalone JSON worker for an isolated, extracted deployment package."""

import hashlib
import json
import resource
import sys
import time
from pathlib import Path
from typing import Any


def main() -> None:
    """Execute the real package entry and expose only qualification instrumentation."""
    package = Path(sys.argv[1]).resolve()
    mode = sys.argv[2]
    started = time.perf_counter()
    sys.path.append(str(package))
    namespace: dict[str, Any] = {} if mode == "raw" else {"__file__": str(package / "main.py")}
    exec(compile((package / "main.py").read_text(), "main.py", "exec"), namespace)
    entry = namespace["agent"]
    info = namespace["runtime_info"]
    import_seconds = time.perf_counter() - started
    import numpy as np
    import torch

    from kagg_revue.deployment import runtime

    for line in sys.stdin:
        request = json.loads(line)
        if request.get("finish"):
            result = {
                "runtime": info(),
                "import_seconds": import_seconds,
                "python_version": sys.version,
                "torch_version": torch.__version__,
                "numpy_version": np.__version__,
                "peak_rss_bytes": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024,
                "modules": sorted(name for name in sys.modules if name.startswith("kagg_revue")),
            }
            print(json.dumps(result), flush=True)
            return
        started = time.perf_counter()
        action = entry(request["observation"], request["configuration"])
        elapsed = time.perf_counter() - started
        session = runtime._SESSIONS[int(request["observation"]["player"])]
        print(
            json.dumps(
                {
                    "action": action,
                    "seconds": elapsed,
                    "features_sha256": hashlib.sha256(session.features.tobytes()).hexdigest(),
                    "program": session.program.tolist(),
                }
            ),
            flush=True,
        )


if __name__ == "__main__":
    main()
