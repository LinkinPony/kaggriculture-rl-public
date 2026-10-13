"""Paired full-game WDL screening of a narrowly defined opening intervention."""

import json
import multiprocessing
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Literal

import hydra
import numpy as np
import torch
from omegaconf import DictConfig, OmegaConf
from pydantic import Field

from kagg_revue.artifacts.io import digest, write_json
from kagg_revue.configuration import FrozenSettings
from kagg_revue.evaluation.comparison import paired_scores
from kagg_revue.evaluation.temperature.games import summary
from kagg_revue.learning.settings import RuntimeSettings
from kagg_revue.native import _revue_core as native
from kagg_revue.opponents.native_batch import create_native_opponent_session
from kagg_revue.opponents.portfolios.native import ASSET_SHA256, native_action
from kagg_revue.policy.checkpoints import load_policy
from kagg_revue.policy.spatial.model import Policy

_POLICY: Policy | None = None
_SETTINGS: dict[str, Any] = {}
_TEMPERATURE = 0
_ORIGINAL = [["BUY_PRODUCT", "WHEAT", 13], ["BUY_PRODUCT", "WHEAT", 5], ["SELL", "WHEAT", 13]]


class Screening(FrozenSettings):
    """Freeze the model and world panel before observing intervention outcomes."""

    checkpoint: Path
    output_dir: Path
    seed: int = Field(ge=0)
    seeds: int = Field(gt=0)
    other_seeds: int = Field(gt=0)
    opponents: tuple[str, ...]
    workers: int = Field(gt=0, le=16)
    temperature: Literal[0, 1] = 0


def initialize(checkpoint: str, temperature: int = 0) -> None:
    """Load one immutable CPU policy per worker, without touching training RNG."""
    global _POLICY, _SETTINGS, _TEMPERATURE
    torch.set_num_threads(1)
    torch.set_num_interop_threads(1)
    _POLICY, payload = load_policy(Path(checkpoint), torch.device("cpu"))
    _POLICY.eval()
    _SETTINGS = payload["settings"]
    _SETTINGS["turns"] = RuntimeSettings.model_validate(_SETTINGS).turns
    _TEMPERATURE = temperature


def play(job: tuple[int, int, str, bool, bool]) -> dict[str, Any]:
    """Change only the declared opening, then let both controllers react normally."""
    seed, seat, opponent, remove_trade, simplify = job
    sampling_seed = seed * 2 + seat
    torch.manual_seed(sampling_seed)
    assert _POLICY is not None
    layout = _POLICY.layout
    engine = native.Engine(seed, _SETTINGS["environment"])
    session = native.ContractSession(dict(engine.configuration), layout.observation.units)
    script = create_native_opponent_session(opponent, 10)
    features = np.empty((1, layout.observation.features), dtype=np.float16)
    inputs = torch.from_numpy(features)
    steps = torch.zeros(1, dtype=torch.long)
    routes, timeline = [], []
    opening_applied = False
    opening_requested = None
    started = time.perf_counter()
    with torch.inference_mode():
        for turn in range(int(_SETTINGS["turns"])):
            session.update(engine.observation(seat))
            session.observe_into(features)
            steps.fill_(turn)
            program, _ = _POLICY.act(inputs, steps, sample=_TEMPERATURE > 0)
            session.set_program(program.numpy(), 1, list(layout.observation.quantities))
            own = dict(session.program_action())
            other = native_action(script, engine, 1 - seat)
            if turn == 0:
                opening_requested = own["market"]
                if simplify and own["market"] == _ORIGINAL:
                    own["market"] = [["BUY_PRODUCT", "WHEAT", 5]]
                    opening_applied = True
                if remove_trade:
                    expected = [["BUY_PRODUCT", "WHEAT", 70], ["SELL", "WHEAT", 70]]
                    if opponent != "ahmed_v45" or other["market"] != expected:
                        raise ValueError("counterfactual requires the authenticated V45 opening")
                    other["market"] = []
            actions = [own, other] if seat == 0 else [other, own]
            routes.append(actions)
            engine.step(*actions)
            if turn < 24 or (turn + 1) % 24 == 0:
                timeline.append(
                    {
                        "turn": turn,
                        "own": engine.observation(seat),
                        "other_cash": engine.money(1 - seat),
                    }
                )
    if not engine.done:
        raise RuntimeError("opening screening did not finish the official game horizon")
    cash, other_cash = float(engine.money(seat)), float(engine.money(1 - seat))
    return {
        "seed": seed,
        "seat": seat,
        "opponent": opponent + ("/without_opening_trade" if remove_trade else ""),
        "simplify": simplify,
        "temperature": _TEMPERATURE,
        "sampling_seed": sampling_seed if _TEMPERATURE else None,
        "opening_applied": opening_applied,
        "opening_requested": opening_requested,
        "cash": cash,
        "opponent_cash": other_cash,
        "outcome": int(cash > other_cash) - int(cash < other_cash),
        "actions": routes,
        "timeline": timeline,
        "wall_seconds": time.perf_counter() - started,
    }


def run(config: Screening) -> None:
    """Archive the declaration, every full trajectory, and paired WDL results."""
    if not config.output_dir.resolve().is_relative_to((Path.cwd() / "outputs").resolve()):
        raise ValueError("evaluation artifacts must remain under outputs")
    if len(set(config.opponents)) != len(config.opponents) or not config.opponents:
        raise ValueError("opponents must be nonempty and unique")
    identities = {name: ASSET_SHA256[name] for name in config.opponents}
    config.output_dir.mkdir(parents=True, exist_ok=False)
    source = Path(__file__)
    (config.output_dir / "runner.py").write_bytes(source.read_bytes())
    write_json(
        config.output_dir / "protocol.json",
        {
            "configuration": config.model_dump(mode="json"),
            "checkpoint_sha256": digest(config.checkpoint),
            "runner_sha256": digest(source),
            "native_sha256": digest(Path(native.__file__)),
            "opponent_asset_sha256": identities,
            "torch_version": torch.__version__,
            "inference": "CPU FP32, batch one; paired worlds and both seats; "
            "sampling seed = 2 * world + seat, reset for each game",
            "scope": "Exploratory full-game WDL screening; no deployment or training changes.",
        },
    )
    jobs = [
        (seed, seat, opponent, remove_trade, simplify)
        for opponent in config.opponents
        for seed in range(
            config.seed,
            config.seed + (config.seeds if opponent == "ahmed_v45" else config.other_seeds),
        )
        for seat in (0, 1)
        for remove_trade in ((False, True) if opponent == "ahmed_v45" else (False,))
        for simplify in (False, True)
    ]
    records = []
    with ProcessPoolExecutor(
        max_workers=config.workers,
        mp_context=multiprocessing.get_context("spawn"),
        initializer=initialize,
        initargs=(str(config.checkpoint), config.temperature),
    ) as pool:
        futures = {pool.submit(play, job): index for index, job in enumerate(jobs)}
        for future in as_completed(futures):
            row = future.result()
            write_json(config.output_dir / "games" / f"{futures[future]:04d}.json", row)
            records.append({k: v for k, v in row.items() if k not in ("actions", "timeline")})
            progress = {"completed": len(records), "total": len(jobs)}
            write_json(config.output_dir / "progress.json", progress)
            print(json.dumps(progress), flush=True)
    strata = {}
    for opponent in sorted({row["opponent"] for row in records}):
        groups = {
            mode: [
                row for row in records if row["opponent"] == opponent and row["simplify"] == mode
            ]
            for mode in (False, True)
        }
        strata[opponent] = {
            "baseline": summary(groups[False]),
            "single_feed": summary(groups[True]),
            "paired": paired_scores({"games": groups[False]}, {"games": groups[True]}),
        }
    write_json(config.output_dir / "report.json", {"opponents": strata, "games": records})
    print(json.dumps(strata), flush=True)


@hydra.main(
    version_base=None,
    config_path=str(Path(__file__).resolve().parents[3] / "configs"),
    config_name="evaluation_trades",
)
def main(configuration: DictConfig) -> None:
    """Resolve a declared local opening experiment independently of live training."""
    run(Screening.model_validate(OmegaConf.to_container(configuration.screening, resolve=True)))


if __name__ == "__main__":
    main()
