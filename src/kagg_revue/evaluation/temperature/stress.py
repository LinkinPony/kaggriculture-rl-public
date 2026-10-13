"""Bounded legal opening perturbations to distinguish budget thresholds from win exploits."""

import json
from copy import deepcopy
from pathlib import Path
from typing import Any

import hydra
import numpy as np
import torch
from omegaconf import DictConfig, OmegaConf

from kagg_revue.artifacts.io import digest, write_json
from kagg_revue.evaluation.temperature.cli import Comparison
from kagg_revue.native import _revue_core as native


def play_prefix(
    replay: dict[str, Any], profile: dict[str, Any], quantity: int, actor: Any = None
) -> dict[str, Any]:
    """Alter one opposing trade quantity and execute only the first two real turns."""
    engine = native.Engine(replay["info"]["seed"], replay["configuration"])
    session = native.ContractSession(replay["configuration"], profile["unit_limit"])
    features = np.empty((1, profile["observation_features"]), dtype=np.float16)
    torch.manual_seed(profile["sampling_seed"] + 1)
    own_actions = []
    trade_profit = 0.0
    for turn in range(2):
        opponent = deepcopy(replay["steps"][turn + 1][0]["action"])
        if turn == 0:
            if quantity:
                opponent["market"][0][2] = quantity
            else:
                opponent["market"] = opponent["market"][2:]
        own = replay["steps"][turn + 1][1]["action"]
        if actor is not None:
            session.update(engine.observation(1))
            session.observe_into(features)
            with torch.inference_mode():
                program = actor(torch.from_numpy(features), torch.tensor([turn])).numpy()
            session.set_program(program, 1, profile["quantities"])
            own = session.program_action()
        own_actions.append(own)
        trace = engine.step_with_trace(opponent, own)
        if turn == 0 and quantity:
            sales = [r for r in trace["market_trace"] if r["player"] == 0 and r["slot_index"] == 1]
            trade_profit = float(sales[0]["money_after"]) - 3000 if sales else 0.0
    observed = engine.observation(1)
    return {
        "opponent_wheat_quantity": quantity,
        "own_sheep": observed["private"]["shed"]["SHEEP"],
        "own_cash": engine.money(1),
        "opponent_cash": engine.money(0),
        "opponent_first_turn_roundtrip_profit": trade_profit,
        "own_first_two_actions_unchanged": own_actions
        == [replay["steps"][t + 1][1]["action"] for t in range(2)],
        "own_actions": own_actions,
    }


@hydra.main(
    version_base=None,
    config_path=str(Path(__file__).resolve().parents[4] / "configs"),
    config_name="evaluation_temperature",
)
def main(configuration: DictConfig) -> None:
    """Save fixed-prefix screening and selected reactive two-turn neural checks."""
    config = Comparison.model_validate(
        OmegaConf.to_container(configuration.comparison, resolve=True)
    )
    settings = configuration.stress
    torch.set_num_threads(1)
    path = Path(configuration.replays.directory) / f"{settings.episode}-replay.json"
    replay = json.loads(path.read_text())
    profile = json.loads((config.package / "agent_profile.json").read_text())
    actor_path = config.package / "actor.pt"
    if digest(actor_path) != profile["actor_sha256"]:
        raise ValueError("opening stress actor differs from the submission")
    actor = torch.jit.load(str(actor_path), map_location="cpu").eval()  # type: ignore[no-untyped-call]
    fixed = [play_prefix(replay, profile, q) for q in range(int(settings.maximum_quantity) + 1)]
    reactive = [play_prefix(replay, profile, int(q), actor) for q in settings.neural_quantities]
    result = {
        "configuration": OmegaConf.to_container(settings, resolve=True),
        "actor_sha256": digest(actor_path),
        "replay_sha256": digest(path),
        "seed": replay["info"]["seed"],
        "seat": 1,
        "fixed_prefix": fixed,
        "reactive_actor": reactive,
        "scope": "Legal two-turn perturbations of the observed opponent opening. Fixed-prefix "
        "screening holds our requests constant; reactive checks re-evaluate the submitted actor "
        "after settlement. No complete-game exploit win rate is measured.",
    }
    write_json(Path(settings.output_dir) / "report.json", result)
    print(json.dumps({"reactive": reactive}, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
