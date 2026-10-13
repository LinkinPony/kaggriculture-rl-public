"""Frozen-checkpoint implementation regression on complete paired matches."""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path
from types import MethodType
from typing import cast

import torch
from torch import Tensor

from kagg_revue.bc.dataset import sha256_file
from kagg_revue.core.backend import load_backend
from kagg_revue.core.provenance import source_identity
from kagg_revue.policy.transformer import EncoderBlock
from kagg_revue.rl.effects.checkpoint import load_checkpoint
from kagg_revue.rl.effects.evaluate import _panel
from kagg_revue.rl.effects.evaluation_cli import load_settings, repository_root
from kagg_revue.rl.effects.population import effect_opponent_identities
from kagg_revue.rl.effects.runtime import native_contract


def _reference_root(
    block: EncoderBlock,
    inputs: Tensor,
    valid: Tensor,
    *,
    positions: Tensor | None = None,
) -> Tensor:
    """Exercise the shared full-output block for implementation comparisons."""
    return cast(Tensor, block(inputs, valid, causal=False, positions=positions))[:, :1]


def main() -> None:
    """Record or compare a frozen model without claiming warm-start eligibility."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--baseline", type=Path)
    parser.add_argument("--full-state-reference", action="store_true")
    arguments, overrides = parser.parse_known_args()
    root = repository_root()
    settings = load_settings(overrides).effect_policy_evaluation
    settings = settings.model_copy(
        update={"checkpoint": arguments.checkpoint, "output_dir": arguments.output},
    )
    output = arguments.output
    output.mkdir(parents=True, exist_ok=False)
    source = source_identity(root)
    if source["worktree_dirty"]:
        raise RuntimeError("implementation regression requires a clean source revision")
    device = torch.device(settings.device)
    if device.type == "cuda":
        torch.cuda.set_device(device)
    torch.set_num_threads(settings.cpu_workers)
    backend = load_backend(root)
    contract = native_contract(backend, settings.environment)
    model, _metadata = load_checkpoint(arguments.checkpoint, contract, device)
    model.eval()
    if arguments.full_state_reference:
        block = model.effects.state_encoder.blocks[-1]
        block.forward_root = MethodType(_reference_root, block)  # type: ignore[assignment]
    identities = effect_opponent_identities(
        backend,
        root,
        {opponent: 1.0 for opponent in settings.opponents},
        settings.public_agent_manifest,
    )
    panel, games = _panel(
        "selection",
        tuple(
            range(
                settings.selection_seed_start,
                settings.selection_seed_start + settings.selection_seed_count,
            )
        ),
        settings,
        backend,
        model,
        contract,
        device,
    )
    report = {
        "generated_at": datetime.now(UTC).isoformat(),
        "source": source,
        "full_state_reference": arguments.full_state_reference,
        "resolved_config": settings.model_dump(mode="json"),
        "checkpoint_sha256": sha256_file(arguments.checkpoint),
        "opponents": identities,
        "native_backend": backend.identity,
        "selection": panel,
        "reserved_confirmation_seeds": list(
            range(
                settings.confirmation_seed_start,
                settings.confirmation_seed_start + settings.confirmation_seed_count,
            )
        ),
        "deployment_authority": False,
        "games": games,
    }
    if arguments.baseline is not None:
        baseline = json.loads(arguments.baseline.read_text(encoding="utf-8"))
        for key in ("checkpoint_sha256", "opponents"):
            if baseline[key] != report[key]:
                raise ValueError(f"implementation regression changed {key}")
        previous = {
            (row["opponent_id"], row["seed"], row["candidate_seat"]): row
            for row in baseline["games"]
        }
        if len(previous) != len(games):
            raise ValueError("implementation regression changed its game count")
        differences = [
            (row, previous[(row["opponent_id"], row["seed"], row["candidate_seat"])])
            for row in games
        ]
        report["comparison"] = {
            "wdl_better": sum(row["outcome"] > old["outcome"] for row, old in differences),
            "wdl_worse": sum(row["outcome"] < old["outcome"] for row, old in differences),
            "cash_changed": sum(
                row["terminal_cash"] != old["terminal_cash"] for row, old in differences
            ),
            "baseline_sha256": sha256_file(arguments.baseline),
        }
    (output / "regression.json").write_text(json.dumps(report, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
