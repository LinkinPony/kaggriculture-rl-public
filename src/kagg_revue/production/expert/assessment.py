"""Separate apprentice, search expert and original-policy complete-game evidence."""

from pathlib import Path
from typing import Any

import torch

from kagg_revue.artifacts.io import write_json
from kagg_revue.evaluation.neural import NeuralMatches
from kagg_revue.policy.spatial.model import Policy
from kagg_revue.production.config import Settings
from kagg_revue.production.evaluation.matches import ScriptMatches
from kagg_revue.production.expert.telemetry import panel_summary
from kagg_revue.production.expert.train import _comparison


class Assessment:
    """Shard populations across devices, keeping each physical match and both seats intact."""

    def __init__(self, settings: Settings, reference: Policy, rank: int) -> None:
        """Reuse one fixed actor graph per population across all three policy identities."""
        self.rank = rank
        self.policy = Policy.from_layout(reference.layout).to(next(reference.parameters()).device)
        self.policy.eval().requires_grad_(False)
        self.reference = reference
        self.matches = (
            ScriptMatches(settings, self.policy)
            if rank == 0
            else NeuralMatches(settings, self.policy, reference)
        )

    def run(self, student: Policy, teacher: Policy, seed: int, path: Path) -> dict[str, Any]:
        """Evaluate independent greedy student execution, with no expert assistance."""
        panels = {}
        for name, policy in (("student", student), ("expert", teacher), ("origin", self.reference)):
            self.policy.load_state_dict(policy.state_dict())
            panels[name] = self.matches.run(seed)
        record = {
            "population": "scripts" if self.rank == 0 else "neural",
            "seed_start": seed,
            **panels,
            "paired_to_expert": _comparison(panels["student"], panels["expert"]),
            "paired_to_origin": _comparison(panels["student"], panels["origin"]),
        }
        write_json(path, record)
        return {
            **{name: panel_summary(panel, opponents=True) for name, panel in panels.items()},
            **{
                name: record[name]
                for name in ("population", "seed_start", "paired_to_expert", "paired_to_origin")
            },
            "report": str(path),
            "physical_games": sum(
                panel["wins"] + panel["ties"] + panel["losses"] for panel in panels.values()
            ),
        }


def parameter_changes(student: Policy, checkpoint: Path) -> dict[str, Any]:
    """Audit the trained artifact once, distinguishing backbone learning from copied readouts."""
    from kagg_revue.policy.checkpoints import load_policy

    baseline, _ = load_policy(checkpoint, torch.device("cpu"))
    before = dict(baseline.named_parameters())
    groups: dict[str, dict[str, Any]] = {}
    for name, parameter in student.named_parameters():
        group = "encoder" if name.startswith("encoder.") else "decoder"
        record = groups.setdefault(group, {"changed_tensors": 0, "delta_squared": 0.0})
        difference = parameter.detach().cpu() - before[name].detach()
        record["changed_tensors"] += int(bool(torch.count_nonzero(difference)))
        record["delta_squared"] += float(difference.square().sum())
    return groups


def _confirmation_rank(rank: int, resolved: dict[str, Any]) -> None:
    from kagg_revue.policy.checkpoints import load_policy
    from kagg_revue.production.expert.config import ApprenticeSettings

    config = ApprenticeSettings.model_validate(resolved)
    p = config.production
    assert p.checkpoint is not None
    device = torch.device(p.devices[rank])
    torch.cuda.set_device(device)
    torch.set_num_threads(p.cpu_threads)
    student, _ = load_policy(p.checkpoint, torch.device("cpu"))
    teacher, _ = load_policy(config.teacher, torch.device("cpu"))
    reference, _ = load_policy(config.reference, torch.device("cpu"))
    assessor = Assessment(p, reference.to(device).eval().requires_grad_(False), rank)
    result = assessor.run(
        student.to(device).eval().requires_grad_(False),
        teacher.to(device).eval().requires_grad_(False),
        p.confirmation_seed,
        p.output_dir / ("scripts.json" if rank == 0 else "neural.json"),
    )
    write_json(p.output_dir / f"rank-{rank}.json", result)
    print(
        {key: value for key, value in result.items() if key not in {"student", "expert", "origin"}},
        flush=True,
    )


def main() -> None:
    """Resolve an isolated larger confirmation panel through the existing Hydra profile."""
    import json

    import hydra
    import torch.multiprocessing as mp
    from omegaconf import DictConfig, OmegaConf

    from kagg_revue.artifacts.io import digest
    from kagg_revue.production.artifacts import provenance
    from kagg_revue.production.expert.config import ApprenticeSettings

    @hydra.main(
        version_base=None, config_path="../../../../configs", config_name="production_apprentice"
    )
    def run(configuration: DictConfig) -> None:
        c = ApprenticeSettings.model_validate(OmegaConf.to_container(configuration, resolve=True))
        p = c.production
        assert p.checkpoint is not None
        source = provenance(p)
        if not source["clean"]:
            raise ValueError("apprentice confirmation requires a clean source revision")
        inputs = {
            role: {"path": str(path), "sha256": digest(path)}
            for role, path in (
                ("student", p.checkpoint),
                ("expert", c.teacher),
                ("origin", c.reference),
            )
        }
        write_json(p.output_dir / "source.json", source)
        write_json(p.output_dir / "resolved-config.json", c.model_dump(mode="json"))
        write_json(p.output_dir / "inputs.json", inputs)
        mp.spawn(_confirmation_rank, args=(c.model_dump(mode="json"),), nprocs=2, join=True)  # type: ignore[attr-defined, no-untyped-call]
        results = [
            json.loads((p.output_dir / f"rank-{rank}.json").read_text()) for rank in range(2)
        ]
        write_json(
            p.output_dir / "report.json",
            {
                "source_revision": source["revision"],
                "inputs": inputs,
                "seed_start": p.confirmation_seed,
                "results": results,
                "student_not_worse_than_expert": all(
                    r["paired_to_expert"]["wdl_gain"] >= 0 for r in results
                ),
                "deployment_budget_qualified": False,
            },
        )

    run()


if __name__ == "__main__":
    main()
