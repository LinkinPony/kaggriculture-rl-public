"""Compare preserved native binaries in separate processes on complete raw replays."""

import hashlib
import importlib.util
import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

import hydra
import orjson
from omegaconf import DictConfig


def encode(options: DictConfig) -> None:
    """Load exactly one native binary, then hash original features and engine states."""
    library = Path(options.engine).resolve()
    name = "kagg_revue.native._revue_core"
    spec = importlib.util.spec_from_file_location(name, library)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)

    from kagg_revue.artifacts.io import digest, write_json
    from kagg_revue.datasets.demonstrations.encoding import encode as encode_replay
    from kagg_revue.datasets.sequences.prepare import Preparation
    from kagg_revue.datasets.sequences.sources import read_replay
    from kagg_revue.policy.contracts import ContractLayout

    manifest = json.loads(Path(options.manifest).read_text())
    settings = dict(manifest["configuration"])
    settings.pop("partition", None)
    settings.pop("split_mapping", None)
    settings["agronomy"] = bool(options.get("agronomy", False))
    settings["derived"] = False
    config = Preparation.model_validate(settings)
    layout = ContractLayout.resolve(config.geometry())
    selected = json.loads(Path(options.audit).read_text())["checked_episodes"]
    records = {row["task"]["episode_id"]: row for row in manifest["shards"]}
    results = []
    encoding_seconds = 0.0
    for selected_row in selected:
        task = records[selected_row["episode_id"]]["task"]
        raw = read_replay(task)
        replay = orjson.loads(raw)
        started = time.perf_counter()
        observations, actions, eligible, _ = encode_replay(replay, layout)
        encoding_seconds += time.perf_counter() - started
        engine = module.Engine(task["seed"], config.environment)
        trajectory = hashlib.sha256()
        for pair in replay["steps"]:
            trajectory.update(
                orjson.dumps(
                    [engine.observation(seat) for seat in (0, 1)],
                    option=orjson.OPT_SORT_KEYS,
                )
            )
            # Replay actions on step i were applied to the state at step i - 1.
            if pair is not replay["steps"][-1]:
                next_pair = replay["steps"][engine.step_index + 1]
                engine.step(*(state["action"] or {} for state in next_pair))
        results.append(
            {
                "episode_id": task["episode_id"],
                "raw_sha256": hashlib.sha256(raw).hexdigest(),
                "observations": hashlib.sha256(observations.tobytes()).hexdigest(),
                "actions": hashlib.sha256(actions.tobytes()).hexdigest(),
                "eligible": hashlib.sha256(eligible.tobytes()).hexdigest(),
                "engine_trajectory": trajectory.hexdigest(),
                "checked_observations": 2 * len(replay["steps"]),
            }
        )
    write_json(
        Path(options.output),
        {
            "native_sha256": digest(library),
            "episodes": results,
            "encoding_seconds": encoding_seconds,
        },
    )


def compare(options: DictConfig) -> None:
    """Require equality of v2 features, labels, masks and full native game trajectories."""
    from kagg_revue.artifacts.io import digest, write_json
    from kagg_revue.native import _revue_core as native

    source = Path(options.source_run)
    state = json.loads((source / "state.json").read_text())
    original = source / state["native_artifact"]
    assert digest(original) == state["native"]
    target = Path(native.__file__)
    output = Path(options.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    results: list[dict[str, Any]] = []
    for role, library in (("source", original), ("target", target)):
        report = output.with_name(f"native-{role}.json")
        subprocess.run(
            [
                sys.executable,
                "-m",
                __spec__.name if __spec__ is not None else __name__,
                "audit.mode=encode",
                f"audit.engine={library}",
                f"audit.output={report}",
                f"audit.manifest={options.manifest}",
                f"audit.audit={options.audit}",
                f"+audit.agronomy={str(bool(options.get('agronomy', False))).lower()}",
            ],
            check=True,
        )
        results.append(json.loads(report.read_text()))
    if results[0]["episodes"] != results[1]["episodes"]:
        raise ValueError("historical native features, labels or full rule trajectories differ")
    write_json(
        output,
        {
            "passed": True,
            "source_native_sha256": results[0]["native_sha256"],
            "target_native_sha256": results[1]["native_sha256"],
            "legacy_version": "grounded-production-context-v4"
            if options.get("agronomy", False)
            else "grounded-production-context-v2",
            "target_version": native.parallel_spec()[
                "derived_version" if options.get("derived_target", False) else "agronomy_version"
            ],
            "checked_observations": sum(
                row["checked_observations"] for row in results[0]["episodes"]
            ),
            "matched_engine_trajectories": True,
            "matched_features_actions_masks": True,
            "episodes": results[0]["episodes"],
            "manifest_sha256": digest(Path(options.manifest)),
            "source_state_sha256": digest(source / "state.json"),
        },
    )
    print(json.dumps({"passed": True, "report": str(output)}), flush=True)


@hydra.main(
    version_base=None, config_path="../../../../configs", config_name="native_history_audit"
)
def main(configuration: DictConfig) -> None:
    """Run a binary-isolated comparison before allowing cross-version historical imports."""
    options = configuration.audit
    (encode if options.mode == "encode" else compare)(options)


if __name__ == "__main__":
    main()
