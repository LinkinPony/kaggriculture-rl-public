"""Fixed full-game controls for behavior-cloned policies before online training."""

from typing import Any

import torch

from kagg_revue.artifacts.io import write_json
from kagg_revue.evaluation.neural import NeuralMatches
from kagg_revue.learning.config import Experiment
from kagg_revue.learning.settings import RuntimeSettings
from kagg_revue.learning.state import load_member
from kagg_revue.policy.spatial.model import Policy


def controls(
    config: Experiment,
    settings: RuntimeSettings,
    state: dict[str, Any],
    actor: Policy,
    epoch: int,
) -> dict[str, Any]:
    """Measure cash and WDL against the same independent random roots every epoch."""
    source = config.demonstrations
    assert source is not None and source.control_games
    device = next(actor.parameters()).device
    runtime = settings.model_copy(update={"evaluation_games": source.control_games})
    panels = []
    actor.eval()
    for index, seed in enumerate(config.evaluation.anchor_seeds):
        name = f"anchors/seed-{seed}.pt"
        opponent, _ = load_member(config, state, name, device)
        opponent.eval()
        torch.manual_seed(source.behavior_seed + index)
        panel = NeuralMatches(runtime, actor, opponent, sample=True).run(source.behavior_seed)
        panel.update(opponent=name, opponent_sha256=state["members"][name])
        panels.append(panel)
    member = f"pretraining/shard-{state['pretraining']['cursor']:06d}.pt"
    result = {
        "epoch": epoch,
        "member": member,
        "checkpoint_sha256": state["members"][member],
        "sample": True,
        "temperature": settings.ppo.temperature,
        "panels": panels,
        "scope": "Fixed random controls diagnose autonomous BC behavior, not competitive strength.",
    }
    write_json(config.output_dir / "pretraining" / f"epoch-{epoch}-controls.json", result)
    return result
