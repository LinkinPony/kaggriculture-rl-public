"""Exercise full-size training, a graceful stop, and exact own-run recovery in isolation."""

import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

import hydra
import torch
from omegaconf import DictConfig, OmegaConf

from kagg_revue.artifacts.io import digest, write_json
from kagg_revue.learning import state as artifacts
from kagg_revue.learning.execution import Execution
from kagg_revue.learning.performance.artifacts import qualification_copy
from kagg_revue.learning.performance.verification import inference
from kagg_revue.learning.recovery.cli import BOOTSTRAP


def _training(
    directory: Path, log: Path, stop_update: int | None, *, archived: bool = False
) -> dict[str, Any]:
    command = (
        [
            sys.executable,
            "-u",
            "-m",
            "kagg_revue.learning.recovery.cli",
            f"recovery.run={directory}",
        ]
        if archived
        else [sys.executable, "-u", "-c", BOOTSTRAP, str(directory / "state.json")]
    )
    with log.open("w") as stream:
        process = subprocess.Popen(
            command,
            stdin=subprocess.DEVNULL,
            stdout=stream,
            stderr=subprocess.STDOUT,
        )
        sent = False
        deadline = time.monotonic() + 1800
        try:
            while process.poll() is None:
                progress = directory / "learning-progress.json"
                if stop_update is not None and progress.exists() and not sent:
                    live = json.loads(progress.read_text())
                    if live.get("update", 0) >= stop_update:
                        process.send_signal(signal.SIGTERM)
                        sent = True
                if time.monotonic() > deadline:
                    raise TimeoutError(f"qualification exceeded 30 minutes; inspect {log}")
                time.sleep(0.2)
            if process.returncode:
                raise RuntimeError(f"qualification training failed; inspect {log}")
        finally:
            if process.poll() is None:
                process.terminate()
                process.wait(timeout=120)
    status: dict[str, Any] = json.loads((directory / "run-status.json").read_text())
    if (stop_update is not None) != (status["status"] == "stopped"):
        raise RuntimeError("qualification did not honor the requested update-boundary stop")
    return status


def qualify(options: dict[str, Any]) -> None:
    """Keep all test descendants outside the production run and authenticate every saved state."""
    execution = Execution.model_validate(options["execution"])
    source, destination = Path(options["run"]), Path(options["output_dir"])
    report = Path(options["report"])
    original = json.loads((source / "state.json").read_text())
    source_state_hash = digest(source / "state.json")
    identity = artifacts.source_identity()
    inference_result = inference(source)
    torch.cuda.empty_cache()
    config = qualification_copy(source, destination, execution, int(options["updates"]))
    os.environ.setdefault("TORCHINDUCTOR_COMPILE_THREADS", "8")
    status = _training(
        destination, destination / "qualification-stop.log", original["completed_update"] + 3
    )
    stopped = artifacts.restore(config.model_copy(update={"resume": True}))
    checkpoint = artifacts.member_path(config, stopped, stopped["latest"])
    payload = torch.load(checkpoint, map_location="cpu", weights_only=False)
    workers = payload["rng"]["workers"]
    if len(workers) != len(execution.devices):
        raise RuntimeError("checkpoint omitted worker random streams")
    if torch.equal(workers[0]["cuda"], workers[1]["cuda"]):
        raise RuntimeError("distinct GPU workers unexpectedly share one random stream")
    required = {"model", "critic", "actor_optimizer", "critic_optimizer", "rng", "lineage"}
    if not required <= payload.keys():
        raise RuntimeError("checkpoint omitted required optimizer or lineage state")
    stop_hash = digest(checkpoint)
    print(json.dumps({"phase": "stopped", **status, "checkpoint_sha256": stop_hash}), flush=True)
    final_status = _training(destination, destination / "qualification-resume.log", None)
    final = artifacts.restore(config.model_copy(update={"resume": True}))
    records = final["records"][original["completed_update"] :]
    if [row["update"] for row in records] != list(
        range(original["completed_update"] + 1, config.updates + 1)
    ):
        raise RuntimeError("resumed update ledger skipped or duplicated an update")
    previous_hash = original["members"][original["latest"]]
    for update in range(original["completed_update"] + 1, config.updates + 1):
        name = artifacts.budget_member(final, update)
        if name not in final["members"]:
            continue
        saved = torch.load(destination / name, map_location="cpu", weights_only=False)
        if saved["lineage"]["parent_sha256"] != previous_hash:
            raise RuntimeError("resume broke the optimizer checkpoint parent chain")
        previous_hash = final["members"][name]
    if digest(source / "state.json") != source_state_hash:
        raise RuntimeError("qualification modified its production source ledger")
    if artifacts.source_identity()["source_sha256"] != identity["source_sha256"]:
        raise RuntimeError("implementation changed while qualification was running")
    write_json(
        report,
        {
            "passed": final_status["status"] == "complete",
            "run_id": original["run_id"],
            "completed_update": original["completed_update"],
            "checkpoint_sha256": original["members"][original["latest"]],
            "source_sha256": identity["source_sha256"],
            "execution": execution.model_dump(mode="json"),
            "qualification_run": str(destination),
            "stopped_update": stopped["completed_update"],
            "stopped_checkpoint_sha256": stop_hash,
            "final_update": final["completed_update"],
            "distinct_rank_rngs": True,
            "full_optimizer_state": True,
            "authenticated_parent_chain": True,
            "source_run_unchanged": True,
            "compiled_inference": inference_result,
            "update_numbers": [row["update"] for row in records],
            "records": records,
        },
    )
    print(json.dumps({"phase": "passed", "report": str(report)}), flush=True)


@hydra.main(
    version_base=None,
    config_path=str(Path(__file__).resolve().parents[4] / "configs"),
    config_name="learning_execution_qualification",
)
def main(configuration: DictConfig) -> None:
    """Resolve a bounded, isolated end-to-end execution qualification."""
    options = OmegaConf.to_container(configuration.qualification, resolve=True)
    assert isinstance(options, dict)
    qualify(options)  # type: ignore[arg-type]


if __name__ == "__main__":
    main()
