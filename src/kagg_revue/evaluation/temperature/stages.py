"""Locate opening concentration across BC epochs and a frozen PPO checkpoint."""

import json
from collections import Counter
from pathlib import Path
from typing import Any

import hydra
import numpy as np
import torch
from omegaconf import DictConfig

from kagg_revue.artifacts.io import digest, write_json
from kagg_revue.evaluation.temperature.replays import observation
from kagg_revue.native import _revue_core as native
from kagg_revue.policy.checkpoints import load_policy


@hydra.main(version_base=None, config_path="../../../../configs", config_name="coverage_stages")
def main(config: DictConfig) -> None:
    """Hold observation and CPU batch size fixed while comparing learned priors."""
    torch.set_num_threads(1)
    profile = json.loads((Path(config.package) / "agent_profile.json").read_text())
    replay = json.loads(Path(config.replay).read_text())
    results = []
    for stage, checkpoint in config.checkpoints.items():
        policy, payload = load_policy(Path(checkpoint), torch.device("cpu"))
        del payload
        policy.eval()
        states = []
        for seat, turn in [(0, 0), (1, 0), (1, 1), (1, 4)]:
            session = native.ContractSession(replay["configuration"], profile["unit_limit"])
            for step in range(turn + 1):
                session.update(observation(replay, step, seat))
            features = np.empty((1, profile["observation_features"]), dtype=np.float16)
            session.observe_into(features)
            inputs, turns = torch.from_numpy(features), torch.tensor([turn])
            counts: Counter[str] = Counter()
            with torch.inference_mode():
                greedy = policy.act(inputs, turns, sample=False)[0].numpy()
                session.set_program(greedy, 1, profile["quantities"])
                greedy_action = session.program_action()
                for seed in range(int(config.seed), int(config.seed) + int(config.draws)):
                    torch.manual_seed(seed)
                    program = policy.act(inputs, turns, sample=True)[0].numpy()
                    session.set_program(program, 1, profile["quantities"])
                    action: Any = session.program_action()
                    counts[json.dumps(action, sort_keys=True)] += 1
            states.append(
                {
                    "seat": seat,
                    "turn": turn,
                    "draws": int(config.draws),
                    "unique_actions": len(counts),
                    "mode_fraction": max(counts.values()) / config.draws,
                    "greedy": greedy_action,
                    "counts": [{"action": json.loads(a), "n": n} for a, n in counts.most_common()],
                }
            )
        results.append(
            {
                "stage": stage,
                "checkpoint": str(checkpoint),
                "sha256": digest(Path(checkpoint)),
                "states": states,
            }
        )
        print(
            json.dumps(
                {
                    "stage": stage,
                    "states": [
                        {k: s[k] for k in ("seat", "turn", "unique_actions", "mode_fraction")}
                        for s in states
                    ],
                }
            ),
            flush=True,
        )
        write_json(
            Path(config.output),
            {
                "results": results,
                "scope": "CPU FP32 batch-one eager sampling on identical recorded observations. "
                "Later states are diagnostic, not counterfactual trajectories or win rates.",
                "sampling_seed_start": int(config.seed),
                "draws_per_state": int(config.draws),
            },
        )


if __name__ == "__main__":
    main()
