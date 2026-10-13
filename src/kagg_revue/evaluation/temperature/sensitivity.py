"""Measure sampling-stream sensitivity without selecting a favorable deployment seed."""

import json
import multiprocessing
from collections import Counter
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
from typing import Any

import hydra
import numpy as np
import torch
from omegaconf import DictConfig, OmegaConf

from kagg_revue.artifacts.io import write_json
from kagg_revue.evaluation.temperature.cli import Comparison
from kagg_revue.evaluation.temperature.games import initialize, play, summary
from kagg_revue.evaluation.temperature.replays import observation
from kagg_revue.native import _revue_core as native
from kagg_revue.policy.checkpoints import load_policy


def opening_distributions(
    config: Comparison, directory: Path, draws: int, seed: int
) -> list[dict[str, Any]]:
    """Hold observed states fixed and vary only the sampling RNG for diagnostic actions."""
    torch.set_num_threads(1)
    profile = json.loads((config.package / "agent_profile.json").read_text())
    actor = torch.jit.load(  # type: ignore[no-untyped-call]
        str(config.package / "actor.pt"), map_location="cpu"
    ).eval()
    result = []
    for episode, turn in [(107807755, 0), (107807755, 4), (107808764, 4)]:
        replay = json.loads((directory / f"{episode}-replay.json").read_text())
        session = native.ContractSession(replay["configuration"], profile["unit_limit"])
        for t in range(turn + 1):
            session.update(observation(replay, t, 1))
        features = np.empty((1, profile["observation_features"]), dtype=np.float16)
        session.observe_into(features)
        inputs, step = torch.from_numpy(features), torch.tensor([turn])
        counts: Counter[str] = Counter()
        with torch.inference_mode():
            for stream in range(seed, seed + draws):
                torch.manual_seed(stream)
                selected = actor(inputs, step).numpy()
                session.set_program(selected, 1, profile["quantities"])
                action: Any = session.program_action()
                decision = action if turn == 0 else action["hands"][3]
                counts[json.dumps(decision, sort_keys=True)] += 1
        result.append(
            {
                "episode": episode,
                "turn": turn,
                "decision": "whole action" if turn == 0 else "fourth hired hand",
                "draws": draws,
                "seed_start": seed,
                "counts": [{"action": json.loads(k), "count": v} for k, v in counts.most_common()],
            }
        )
    return result


@hydra.main(
    version_base=None,
    config_path=str(Path(__file__).resolve().parents[4] / "configs"),
    config_name="evaluation_temperature",
)
def main(configuration: DictConfig) -> None:
    """Vary sixteen sampling streams across both seats on one fixed script matchup."""
    config = Comparison.model_validate(
        OmegaConf.to_container(configuration.comparison, resolve=True)
    )
    settings = configuration.sensitivity
    torch.set_num_threads(1)
    profile = json.loads((config.package / "agent_profile.json").read_text())
    policy, payload = load_policy(config.checkpoint, torch.device("cpu"))
    runtime = payload["settings"]
    del policy, payload
    path = config.output_dir / "sampling-sensitivity-games.jsonl"
    if path.exists():
        raise ValueError("sampling sensitivity output already exists")
    records = []
    with (
        ProcessPoolExecutor(
            max_workers=int(settings.workers),
            mp_context=multiprocessing.get_context("spawn"),
            initializer=initialize,
            initargs=({1: str(config.package / "actor.pt")}, runtime, profile),
        ) as pool,
        path.open("w") as stream,
    ):
        futures = [
            pool.submit(
                play,
                (config.seed, seat, str(settings.opponent), 1),
                int(settings.seed) + 2 * index + seat,
            )
            for index in range(int(settings.streams))
            for seat in (0, 1)
        ]
        for future in as_completed(futures):
            row = future.result()
            records.append(row)
            stream.write(json.dumps(row) + "\n")
            stream.flush()
            print(json.dumps({"seed_sensitivity_completed": len(records)}), flush=True)
    distributions = opening_distributions(
        config, Path(configuration.replays.directory), int(settings.draws), int(settings.seed)
    )
    write_json(
        config.output_dir / "sampling-sensitivity.json",
        {
            "configuration": OmegaConf.to_container(settings, resolve=True),
            "environment_seed": config.seed,
            "summary": summary(records),
            "cash_min": min(r["cash"] for r in records),
            "cash_max": max(r["cash"] for r in records),
            "cash_std": float(np.std([r["cash"] for r in records])),
            "unique_openings": len({r["opening_programs_sha256"] for r in records}),
            "opening_distributions": distributions,
            "scope": "One fixed environment seed and opponent, both seats. Measures stream "
            "sensitivity, not population win rate. No favorable seed is selected.",
        },
    )


if __name__ == "__main__":
    main()
