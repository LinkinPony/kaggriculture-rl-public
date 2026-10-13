"""Frozen controls and direct paired stopping decisions for a recovery challenger."""

import json
from pathlib import Path
from typing import Any

import numpy as np
import torch

from kagg_revue.artifacts.io import digest, write_json
from kagg_revue.policy.checkpoints import load_policy
from kagg_revue.policy.spatial.model import Policy
from kagg_revue.production.artifacts import provenance
from kagg_revue.production.config import Settings
from kagg_revue.production.evaluation import panel


def paired_change(baseline: dict[str, Any], candidate: dict[str, Any]) -> dict[str, int]:
    """Compare direct WDL only after confirming common seeds, seats and opponents."""
    before, after = baseline["games"], candidate["games"]
    keys = ("seed", "seat", "opponent")
    if len(before) != len(after) or any(
        any(left[key] != right[key] for key in keys)
        for left, right in zip(before, after, strict=True)
    ):
        raise ValueError("regression decisions require complete common-seed paired panels")
    differences = np.array(
        [right["outcome"] - left["outcome"] for left, right in zip(before, after, strict=True)]
    )
    better, worse = int((differences > 0).sum()), int((differences < 0).sum())
    return {
        "better": better,
        "same": int((differences == 0).sum()),
        "worse": worse,
        "net_regressions": worse - better,
    }


def preflight(settings: Settings) -> None:
    """Evaluate the frozen start and control before any recovery optimizer update."""
    config = settings.recovery_evaluation
    if config is None or settings.checkpoint is None:
        raise ValueError("preflight requires a recovery profile and an explicit checkpoint")
    source = provenance(settings)
    if not source["clean"]:
        raise ValueError("recovery evidence must bind a clean source revision")
    torch.set_num_threads(settings.cpu_threads)
    device = torch.device(settings.devices[0])
    torch.cuda.set_device(device)
    panels = {}
    for name, path in (("control", config.control_checkpoint), ("start", settings.checkpoint)):
        policy, _ = load_policy(path, device)
        for sampled in (False, True):
            label = f"{name}_{'sampled' if sampled else 'greedy'}"
            panels[label] = panel(settings, policy, settings.evaluation_seed, sample=sampled)
            print(
                json.dumps(
                    {
                        "phase": label,
                        **{k: panels[label][k] for k in ("wins", "ties", "losses", "mean_cash")},
                    }
                ),
                flush=True,
            )
        del policy
        torch.cuda.empty_cache()
    comparisons = {
        "greedy_vs_control": paired_change(panels["control_greedy"], panels["start_greedy"]),
        "sampled_vs_greedy": paired_change(panels["start_greedy"], panels["start_sampled"]),
        "sampled_vs_control": paired_change(panels["control_sampled"], panels["start_sampled"]),
    }
    passed = all(
        value["net_regressions"] <= config.maximum_net_regressions for value in comparisons.values()
    )
    write_json(
        settings.output_dir / "recovery" / "preflight.json",
        {
            "source": source,
            "checkpoint": {"path": str(settings.checkpoint), "sha256": digest(settings.checkpoint)},
            "control_checkpoint": {
                "path": str(config.control_checkpoint),
                "sha256": digest(config.control_checkpoint),
            },
            "seed_role": "selection",
            "held_out_confirmation_seed": settings.confirmation_seed,
            "panels": panels,
            "paired": comparisons,
            "passed": passed,
            "decision": "allow short recovery trial" if passed else "quarantine recovery start",
            "deployment_budget_qualified": False,
            "quality_promotion": False,
        },
    )
    if not passed:
        raise RuntimeError("fixed-temperature recovery start failed its direct paired preflight")


def validate_preflight(settings: Settings) -> None:
    """Reject training against a missing, failed or mismatched frozen preflight."""
    if settings.recovery_evaluation is None:
        return
    report = json.loads((settings.output_dir / "recovery" / "preflight.json").read_text())
    evaluated = report["source"]["profile"]
    evaluated["mode"] = settings.mode
    source = provenance(settings)
    if (
        not report["passed"]
        or not source["clean"]
        or source["revision"] != report["source"]["revision"]
        or source["native_sha256"] != report["source"]["native_sha256"]
        or source["historical_opponent"] != report["source"].get("historical_opponent")
        or evaluated != settings.model_dump(mode="json")
        or digest(Path(report["checkpoint"]["path"])) != report["checkpoint"]["sha256"]
        or digest(Path(report["control_checkpoint"]["path"]))
        != report["control_checkpoint"]["sha256"]
    ):
        raise ValueError("recovery profile or artifact identity differs from its passing preflight")


def check_regression(
    settings: Settings,
    policy: Policy,
    greedy: dict[str, Any],
    checkpoint: Path,
    update: int,
) -> bool:
    """Return a synchronized stop decision from frozen greedy and sampled controls."""
    config = settings.recovery_evaluation
    if config is None:
        return False
    path = settings.output_dir / "recovery" / "preflight.json"
    baseline = json.loads(path.read_text())["panels"]
    sampled = panel(settings, policy, settings.evaluation_seed, sample=True)
    comparisons = {
        "greedy_vs_start": paired_change(baseline["start_greedy"], greedy),
        "sampled_vs_start": paired_change(baseline["start_sampled"], sampled),
        "greedy_vs_control": paired_change(baseline["control_greedy"], greedy),
        "sampled_vs_control": paired_change(baseline["control_sampled"], sampled),
    }
    stop = any(
        value["net_regressions"] > config.maximum_net_regressions for value in comparisons.values()
    )
    record = {
        "update": update,
        "checkpoint": {"path": str(checkpoint), "sha256": digest(checkpoint)},
        "preflight_sha256": digest(path),
        "paired": comparisons,
        "panels": {"greedy": greedy, "sampled": sampled},
        "stop": stop,
        "quality_promotion": False,
        "deployment_budget_qualified": False,
    }
    write_json(settings.output_dir / "recovery" / f"update-{update:04d}.json", record)
    write_json(
        settings.output_dir / "recovery-status.json",
        {"update": update, "stopped_for_regression": stop, "paired": comparisons},
    )
    print(
        json.dumps(
            {"phase": "recovery_evaluation", "update": update, "stop": stop, "paired": comparisons}
        ),
        flush=True,
    )
    return stop
