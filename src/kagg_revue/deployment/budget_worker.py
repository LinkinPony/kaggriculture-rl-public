"""Cold CPU worker using the pinned official Agent loader and action timer."""

import hashlib
import importlib
import json
import os
import resource
import runpy
import sys
from pathlib import Path
from typing import Any


def main() -> None:
    """Account imports and first inference inside the official first-action timer."""
    package, framework = Path(sys.argv[1]), Path(sys.argv[2])
    os.sched_setaffinity(0, {int(sys.argv[4])})
    helpers = runpy.run_path(str(Path(__file__).parents[1] / "native" / "framework.py"))
    core = helpers["load_framework"](framework, sys.argv[3])
    agent_module = importlib.import_module("kaggle_environments.agent")
    actor: Any = None
    cold = "torch" not in sys.modules
    if not cold:
        raise ValueError("framework setup preloaded PyTorch before the official timer")
    for line in sys.stdin:
        request = json.loads(line)
        if request.get("finish"):
            runtime = importlib.import_module("kagg_revue.deployment.runtime")
            torch = importlib.import_module("torch")
            print(
                json.dumps(
                    {
                        "cold_torch_import": cold,
                        "cpu_affinity": sorted(os.sched_getaffinity(0)),
                        "peak_rss_bytes": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024,
                        "torch_version": torch.__version__,
                        "python_version": sys.version,
                        "runtime": runtime.runtime_info(),
                        "modules": sorted(
                            name for name in sys.modules if name.startswith("kagg_revue")
                        ),
                    }
                ),
                flush=True,
            )
            return
        if actor is None:
            environment = core.make(
                "kaggriculture", configuration=request["configuration"], debug=False
            )
            actor = agent_module.Agent(str(package / "main.py"), environment)
        action, log = actor.act(core.structify(request["observation"]))
        result: dict[str, Any] = {"log": log}
        if isinstance(action, BaseException):
            result["error"] = {"type": type(action).__name__, "message": str(action)}
        else:
            runtime = importlib.import_module("kagg_revue.deployment.runtime")
            session = runtime._SESSIONS[int(request["observation"]["player"])]
            result.update(
                {
                    "action": action,
                    "features_sha256": hashlib.sha256(session.features.tobytes()).hexdigest(),
                    "program": session.program.tolist(),
                }
            )
        print(json.dumps(result), flush=True)


if __name__ == "__main__":
    main()
