"""Compare the exact BC start and PPO snapshot in paired complete native games."""

import json
from pathlib import Path
from typing import Any

import hydra
import numpy as np
import torch
from omegaconf import DictConfig, OmegaConf
from pydantic import Field

from kagg_revue.artifacts.io import digest, write_json
from kagg_revue.configuration import FrozenSettings
from kagg_revue.evaluation.neural import NeuralMatches
from kagg_revue.learning.settings import RuntimeSettings
from kagg_revue.native import _revue_core
from kagg_revue.policy.checkpoints import load_policy


class Options(FrozenSettings):
    """Declare a fixed-size seed-paired duel before reading any outcomes."""

    snapshot: Path
    output: Path
    device: str = "cuda:1"
    seed: int = 9285100000
    sampling_seed: int = 92851001
    seeds: int = Field(default=64, gt=0)
    batch_games: int = Field(default=32, gt=0)


@hydra.main(version_base=None, config_path="../../../../configs", config_name="diagnosis_duel")
def main(config: DictConfig) -> None:
    """Retain all direct games, frozen identities and seed-cluster intervals."""
    options = Options.model_validate(OmegaConf.to_container(config.analysis, resolve=True))
    if options.batch_games % 2 or (2 * options.seeds) % options.batch_games:
        raise ValueError("duel batches must preserve complete mirrored seed pairs")
    options.output.mkdir(parents=True, exist_ok=True)
    write_json(options.output / "config.json", options.model_dump(mode="json"))
    snapshot = json.loads(options.snapshot.read_text())
    torch.set_num_threads(2)
    device = torch.device(options.device)
    if device.type == "cuda":
        torch.cuda.set_device(device)
        torch.cuda.set_per_process_memory_fraction(0.08, device)
    actors, payloads = {}, {}
    for name, source in snapshot["actors"].items():
        path = Path(source["path"])
        if digest(path) != source["sha256"]:
            raise ValueError("frozen actor changed")
        actors[name], payloads[name] = load_policy(path, device)
        actors[name].eval().requires_grad_(False)
    settings = RuntimeSettings.model_validate(payloads["ppo"]["settings"]).model_copy(
        update={
            "evaluation_games": options.batch_games,
            "workers": 4,
            "precision": "bf16",
            "bf16_reduced_precision_reduction": False,
        }
    )
    panel = NeuralMatches(settings, actors["ppo"], actors["bc"], sample=True)
    rows: list[dict[str, Any]] = []
    with (options.output / "games.jsonl").open("w") as stream:
        for offset in range(0, 2 * options.seeds, options.batch_games):
            torch.manual_seed(options.sampling_seed + offset)
            with torch.inference_mode():
                result = panel.run(options.seed + offset // 2)
            for row in result["games"]:
                row["sampling_seed"] = options.sampling_seed + offset
                stream.write(json.dumps(row) + "\n")
            stream.flush()
            rows.extend(result["games"])
            print(
                json.dumps({"games": len(rows), "seconds": result["timing"]["elapsed_seconds"]}),
                flush=True,
            )
    unchanged = all(
        torch.equal(tensor, payloads[name]["model"][key])
        for name, actor in actors.items()
        for key, tensor in actor.state_dict().items()
    )
    if not unchanged:
        raise ValueError("evaluation changed actor parameters")
    clustered = np.array(
        [
            [
                np.mean([(r["outcome"] + 1) / 2 for r in rows if r["seed"] == seed]),
                np.mean([r["cash"] - r["opponent_cash"] for r in rows if r["seed"] == seed]),
            ]
            for seed in range(options.seed, options.seed + options.seeds)
        ]
    )
    rng = np.random.default_rng(92851)
    sampled = clustered[rng.integers(options.seeds, size=(4096, options.seeds))].mean(1)
    write_json(
        options.output / "report.json",
        {
            "snapshot": snapshot,
            "configuration": options.model_dump(mode="json"),
            "native_sha256": digest(Path(_revue_core.__file__)),
            "weights_unchanged": unchanged,
            "games": len(rows),
            "wins": sum(r["outcome"] > 0 for r in rows),
            "ties": sum(r["outcome"] == 0 for r in rows),
            "losses": sum(r["outcome"] < 0 for r in rows),
            "score": float(clustered[:, 0].mean()),
            "mean_margin": float(clustered[:, 1].mean()),
            "score_ci95": np.quantile(sampled[:, 0], [0.025, 0.975]).tolist(),
            "margin_ci95": np.quantile(sampled[:, 1], [0.025, 0.975]).tolist(),
            "scope": "PPO against its exact BC start, T=1, full memory, paired environment seeds. "
            "This does not measure strength against external top competitors.",
        },
    )
    if panel.runtime.capture is not None:
        panel.runtime.capture.close()


if __name__ == "__main__":
    main()
