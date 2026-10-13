"""Build a portable sampled policy package without legacy workflow dependencies."""

import json
import shutil
import tarfile
from pathlib import Path
from typing import Any

import hydra
import torch
from omegaconf import DictConfig, OmegaConf

from kagg_revue.artifacts.archive import _archive, _file_rows
from kagg_revue.artifacts.io import digest, write_json
from kagg_revue.deployment.actor import freeze
from kagg_revue.deployment.config import Deployment
from kagg_revue.deployment.provenance import load_run
from kagg_revue.learning.state import load_member, source_identity
from kagg_revue.native.compilation import _build_native

ENTRY = """\
from pathlib import Path
import sys

_root = Path(__file__).resolve().parent if '__file__' in globals() else Path(sys.path[-1]).resolve()
sys.path.insert(0, str(_root / 'src'))
from kagg_revue.deployment.runtime import agent as _agent, runtime_info

def agent(observation, configuration):
    return _agent(observation, configuration)
"""
LIQUIDATING_ENTRY = """\
from pathlib import Path
import sys

_root = Path(__file__).resolve().parent if '__file__' in globals() else Path(sys.path[-1]).resolve()
sys.path.insert(0, str(_root / 'src'))
from kagg_revue.deployment.runtime import agent as _agent, runtime_info
from kagg_revue.deployment.liquidation import liquidate as _liquidate

def agent(observation, configuration):
    action = _agent(observation, configuration)
    try:
        return _liquidate(observation, configuration, action)
    except Exception:
        return action
"""


def build(
    config: Deployment,
    *,
    snapshot: Path | None = None,
    submission_info: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Bind a new-root checkpoint, source archive, sampled actor and each native ABI."""
    root = Path.cwd().resolve()
    if snapshot is None:
        experiment, state = load_run(config.run)
        policy, payload = load_member(experiment, state, config.member, torch.device("cpu"))
    else:
        from kagg_revue.deployment.snapshots import load

        experiment, state, policy, payload = load(config.run, config.member, snapshot)
    root_kind = state["initialization"]
    layout = policy.layout
    if layout.network.architecture not in {"grounded-v1", "grounded-v2"} or layout.capacity != 1:
        raise ValueError("this runtime supports grounded single-turn models")
    config.output_dir.mkdir(parents=True, exist_ok=False)
    package = config.output_dir / "package"
    package.mkdir()
    identity = source_identity()
    write_json(config.output_dir / "source.json", identity)
    with tarfile.open(config.output_dir / "source.tar.gz", "w:gz") as archive:
        for name in identity["files"]:
            archive.add(name, arcname=name, recursive=False)
    modules = [
        "kagg_revue/__init__.py",
        "kagg_revue/native/__init__.py",
        "kagg_revue/deployment/__init__.py",
        "kagg_revue/deployment/runtime.py",
    ]
    if config.liquidation:
        modules.append("kagg_revue/deployment/liquidation.py")
    for name in modules:
        destination = package / "src" / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(root / "src" / name, destination)
    (package / "main.py").write_text(LIQUIDATING_ENTRY if config.liquidation else ENTRY)
    torch.set_num_threads(config.cpu_threads)
    freeze(policy, package / "actor.pt", temperature=config.temperature)
    binaries = [
        _build_native(
            root,
            package.resolve(),
            interpreter,
            config.native.compiler,
            config.native.patchelf,
            config.native.max_glibc,
            config.native.jobs,
            deployment=True,
        )
        for interpreter in config.native.interpreters
    ]
    if source_identity() != identity:
        raise ValueError("source or training native binary changed during package construction")
    profile = {
        "schema": f"{root_kind}-root-grounded-deployment-v1",
        "actor_sha256": digest(package / "actor.pt"),
        "feature_version": layout.observation.version,
        "native_binaries": binaries,
        "observation_features": layout.observation.features,
        "unit_limit": layout.observation.units,
        "quantities": layout.observation.quantities,
        "environment": experiment.environment,
        "cpu_threads": config.cpu_threads,
        "sampling_seed": config.sampling_seed,
        "precision": "fp32",
        "memory": {
            "turns": layout.network.memory_turns,
            "tokens": layout.network.memory_tokens,
            "width": layout.network.memory_width,
            "layers": layout.network.memory_layers,
            "heads": layout.network.heads,
        },
        "temperature": config.temperature,
        "sampling": (
            "conditional_gumbel_batch_one" if config.temperature > 0 else "conditional_argmax"
        ),
    }
    if config.liquidation:
        profile["final_turn_liquidation"] = True
    write_json(package / "agent_profile.json", profile)
    if submission_info is not None:
        write_json(package / "submission-info.json", submission_info)
        (package / "submission-info.txt").write_text(
            submission_info["description"]
            + "\n\n"
            + json.dumps(submission_info, indent=2, ensure_ascii=False)
            + "\n"
        )
    manifest = {
        "schema_version": f"{root_kind}-root-grounded-submission-v1",
        "source_sha256": identity["source_sha256"],
        "source_archive_sha256": digest(config.output_dir / "source.tar.gz"),
        "torch_export_version": torch.__version__,
        "training_run": str(config.run),
        "run_id": state["run_id"],
        "initialization": root_kind,
        "input_weights": state["input_weights"],
        "checkpoint_member": config.member,
        "checkpoint_sha256": state["members"][config.member],
        "lineage": payload["lineage"],
        "actor_artifact": {
            "archive_path": "actor.pt",
            "sha256": profile["actor_sha256"],
            "size_bytes": (package / "actor.pt").stat().st_size,
        },
        "native_binaries": binaries,
        "files": _file_rows(package),
        "scope": "Locally built candidate from an authenticated policy root; "
        "official archive runtime qualification is a separate requirement.",
    }
    write_json(package / "manifest.json", manifest)
    destination = config.output_dir / "submission.tar.gz"
    _archive(package, destination)
    report = {
        **manifest,
        "configuration": config.model_dump(mode="json"),
        "archive": {
            "path": str(destination),
            "sha256": digest(destination),
            "size_bytes": destination.stat().st_size,
        },
    }
    write_json(config.output_dir / "build-report.json", report)
    return report


@hydra.main(
    version_base=None,
    config_path=str(Path(__file__).resolve().parents[3] / "configs"),
    config_name="deployment_bundle",
)
def main(configuration: DictConfig) -> None:
    """Construct a local reviewable archive from explicitly registered new weights."""
    config = Deployment.model_validate(
        OmegaConf.to_container(configuration.deployment, resolve=True)
    )
    print(json.dumps(build(config)["archive"]), flush=True)


if __name__ == "__main__":
    main()
