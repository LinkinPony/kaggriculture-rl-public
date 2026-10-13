"""Independent complete-game confirmation of a frozen state-branch student."""

import json
from pathlib import Path
from typing import Any

import hydra
import torch
import torch.multiprocessing as mp
from omegaconf import DictConfig, OmegaConf

from kagg_revue.artifacts.io import digest, write_json
from kagg_revue.policy.checkpoints import load_policy
from kagg_revue.production.artifacts import provenance
from kagg_revue.production.branching.config import BranchSettings
from kagg_revue.production.branching.evidence import StudentAssessment


def _rank(rank: int, resolved: dict[str, Any]) -> None:
    c = BranchSettings.model_validate(resolved)
    p = c.production
    assert p.checkpoint is not None
    device = torch.device(p.devices[rank])
    torch.cuda.set_device(device)
    torch.set_num_threads(p.cpu_threads)
    student, saved = load_policy(p.checkpoint, torch.device("cpu"))
    initial_path = Path(saved["branch_configuration"]["production"]["checkpoint"])
    initial, _ = load_policy(initial_path, torch.device("cpu"))
    reference, _ = load_policy(c.reference, torch.device("cpu"))
    expert, _ = load_policy(c.continuation, torch.device("cpu"))
    assessor = StudentAssessment(p, reference.to(device).eval().requires_grad_(False), rank)
    result = assessor.run_student(
        student.to(device).eval().requires_grad_(False),
        initial.to(device).eval().requires_grad_(False),
        expert.to(device).eval().requires_grad_(False),
        p.confirmation_seed,
        p.output_dir / ("scripts.json" if rank == 0 else "neural.json"),
    )
    write_json(p.output_dir / f"rank-{rank}.json", result)
    print(
        {
            "population": result["population"],
            "paired_to_initial": result["paired_to_initial"],
            "student": {k: result["student"][k] for k in ("wins", "ties", "losses")},
        },
        flush=True,
    )


@hydra.main(
    version_base=None, config_path="../../../../configs", config_name="production_branching"
)
def main(configuration: DictConfig) -> None:
    """Bind the frozen candidate, exact opponent identities and disjoint confirmation seeds."""
    c = BranchSettings.model_validate(OmegaConf.to_container(configuration, resolve=True))
    p = c.production
    assert p.checkpoint is not None
    source = provenance(p)
    if not source["clean"]:
        raise ValueError("state-branch confirmation requires clean source")
    _, saved = load_policy(p.checkpoint, torch.device("cpu"))
    initial = Path(saved["branch_configuration"]["production"]["checkpoint"])
    inputs = {
        name: {"path": str(path), "sha256": digest(path)}
        for name, path in (
            ("student", p.checkpoint),
            ("initial", initial),
            ("expert", c.continuation),
            ("reference", c.reference),
        )
    }
    del saved
    write_json(p.output_dir / "source.json", source)
    write_json(p.output_dir / "resolved-config.json", c.model_dump(mode="json"))
    write_json(p.output_dir / "inputs.json", inputs)
    mp.spawn(_rank, args=(c.model_dump(mode="json"),), nprocs=len(p.devices), join=True)  # type: ignore[attr-defined, no-untyped-call]
    results = [
        json.loads((p.output_dir / f"rank-{rank}.json").read_text())
        for rank in range(len(p.devices))
    ]
    write_json(
        p.output_dir / "report.json",
        {
            "inputs": inputs,
            "source_revision": source["revision"],
            "seed_start": p.confirmation_seed,
            "results": results,
            "deployment_budget_qualified": False,
            "incumbent_changed": False,
        },
    )


if __name__ == "__main__":
    main()
