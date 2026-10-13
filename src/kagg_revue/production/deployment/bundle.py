"""Package an immutable entity actor with multi-ABI native observation execution."""

import json
import shutil
import subprocess
from pathlib import Path
from typing import Any

import hydra
import torch
from omegaconf import DictConfig, OmegaConf
from pydantic import BaseModel, ConfigDict
from torch import Tensor, nn

from kagg_revue.artifacts.io import digest, write_json
from kagg_revue.policy.checkpoints import load_policy
from kagg_revue.policy.spatial.model import Policy
from kagg_revue.submission.config import NativeBuildSettings
from kagg_revue.submission.package import _archive, _build_native, _file_rows


class Settings(BaseModel):
    """Resolved export identity and deployment resources."""

    model_config = ConfigDict(extra="forbid", frozen=True)
    checkpoint: Path
    output_dir: Path
    cpu_threads: int
    native: NativeBuildSettings


class GreedyActor(nn.Module):
    """Trace only conditional greedy choices; behavior probabilities stay in training."""

    def __init__(self, policy: Policy) -> None:
        """Retain the single trained model implementation."""
        super().__init__()
        self.policy = policy

    def forward(self, observations: Tensor, steps: Tensor) -> Tensor:
        """Return deterministic choices with their causal predecessor conditioning."""
        return self.policy.act(observations, steps, sample=False)[0]


def build(settings: Settings) -> dict[str, Any]:
    """Build from clean source and preserve the training checkpoint provenance."""
    root = Path(__file__).resolve().parents[4]
    revision = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    if subprocess.check_output(["git", "status", "--porcelain"], text=True):
        raise ValueError("submission export requires a clean source revision")
    output = settings.output_dir
    if output.is_absolute() or ".." in output.parts or output.parts[0] != "outputs":
        raise ValueError("submission results must remain under outputs")
    output.mkdir(parents=True, exist_ok=False)
    package = output / "package"
    package.mkdir()
    sources = [
        "kagg_revue/__init__.py",
        "kagg_revue/native/__init__.py",
        "kagg_revue/production/__init__.py",
        "kagg_revue/production/deployment/__init__.py",
        "kagg_revue/production/deployment/agent.py",
    ]
    for name in sources:
        target = package / "src" / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(root / "src" / name, target)
    entry = (
        "from pathlib import Path\nimport sys\n"
        "_root = Path(__file__).resolve().parent if '__file__' in globals() "
        "else Path(sys.path[-1]).resolve()\n"
        "sys.path.insert(0, str(_root / 'src'))\n"
        "from kagg_revue.production.deployment.agent import agent as _agent, runtime_info\n"
        "def agent(observation, configuration):\n"
        "    return _agent(observation, configuration)\n"
    )
    (package / "main.py").write_text(entry)
    torch.set_num_threads(settings.cpu_threads)
    policy, checkpoint = load_policy(settings.checkpoint, torch.device("cpu"))
    policy.eval()
    actor_path = package / "actor.pt"
    example = torch.zeros((1, policy.layout.observation.features), dtype=torch.float16)
    step = torch.zeros(1, dtype=torch.long)
    with torch.inference_mode():
        traced = torch.jit.trace(GreedyActor(policy).eval(), (example, step))  # type: ignore[no-untyped-call]
        torch.jit.freeze(traced).save(str(actor_path))
    binaries = [
        _build_native(
            root,
            package,
            interpreter,
            settings.native.compiler,
            settings.native.patchelf,
            settings.native.max_glibc,
            settings.native.jobs,
        )
        for interpreter in settings.native.interpreters
    ]
    profile = {
        "actor_path": "actor.pt",
        "actor_sha256": digest(actor_path),
        "cpu_threads": settings.cpu_threads,
        "unit_limit": policy.layout.observation.units,
        "observation_features": policy.layout.observation.features,
        "factors": policy.layout.factors,
        "interval": policy.layout.interval,
        "decision_turns": policy.layout.starts,
        "program_capacity": policy.layout.capacity if policy.layout.work else 0,
        "quantities": policy.layout.observation.quantities,
        "resolved_environment": checkpoint["settings"]["environment"],
        "time_prior": policy.layout.network.time_prior,
        "prior_scale": policy.layout.network.prior_scale,
        "native_binaries": binaries,
    }
    write_json(package / "agent_profile.json", profile)
    manifest = {
        "schema_version": "entity-policy-kaggle-submission-v1",
        "source_commit": revision,
        "worktree_dirty": False,
        "probe_scaffold": False,
        "checkpoint": {
            "path": str(settings.checkpoint),
            "sha256": digest(settings.checkpoint),
            "update": checkpoint.get("migration_update", checkpoint.get("update")),
            "migration_update": checkpoint.get("migration_update"),
        },
        "training_source": checkpoint.get("provenance"),
        "actor_artifact": {
            "archive_path": "actor.pt",
            "sha256": digest(actor_path),
            "size_bytes": actor_path.stat().st_size,
            "dtype": "float32",
        },
        "native_binaries": binaries,
        "agent_profile": profile,
        "files": _file_rows(package),
    }
    write_json(package / "manifest.json", manifest)
    archive = output / "submission.tar.gz"
    _archive(package, archive)
    if archive.stat().st_size >= 100_000_000:
        raise ValueError("submission exceeds the competition archive limit")
    report = {
        **manifest,
        "resolved_configuration": settings.model_dump(mode="json"),
        "archive": {
            "path": str(archive),
            "sha256": digest(archive),
            "size_bytes": archive.stat().st_size,
        },
    }
    write_json(output / "build-report.json", report)
    shutil.copyfile(
        root / "src/kagg_revue/submission/kaggle_validate.py", output / "kaggle-validation.py"
    )
    return report


@hydra.main(
    version_base=None, config_path="../../../../configs", config_name="production_submission"
)
def main(configuration: DictConfig) -> None:
    """Resolve the frozen artifact once and construct a reviewable submission."""
    settings = Settings.model_validate(OmegaConf.to_container(configuration, resolve=True))
    result = build(settings)
    print(json.dumps(result["archive"], indent=2))


if __name__ == "__main__":
    main()
