"""Compare a frozen independent standalone script with the authenticated neural reference."""

import hashlib
import json
import multiprocessing
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
from typing import Any

import hydra
import numpy as np
import orjson
import torch
from omegaconf import DictConfig, OmegaConf
from pydantic import BaseModel, ConfigDict, Field

from kagg_revue.artifacts.io import digest, write_json
from kagg_revue.native.features import Layout
from kagg_revue.opponents.research.arena import summarize
from kagg_revue.opponents.research.qualification import _agent


class Panel(BaseModel):
    """Freeze source and actor identities before independent paired-seat neural games."""

    model_config = ConfigDict(extra="forbid", frozen=True)
    source: Path
    reference: Path
    output: Path
    seeds: tuple[int, ...]
    workers: int = Field(default=16, ge=1, le=16)


def play(config: Panel, seed: int, seat: int, fingerprint: str) -> dict[str, Any]:
    """Run the standalone source using only real official observations."""
    from kagg_revue.native import _revue_core as native

    if digest(config.source) != fingerprint:
        raise ValueError("independent source changed during neural evaluation")
    torch.set_num_threads(1)
    metadata = json.loads((config.reference / "manifest.json").read_text())
    if digest(config.reference / "actor.pt") != metadata["actor_sha256"]:
        raise ValueError("neural reference hash mismatch")
    actor = torch.jit.load(str(config.reference / "actor.pt"), map_location="cpu").eval()  # type: ignore[no-untyped-call]
    layout = Layout(**metadata["layout"]["observation"])
    environment = metadata["settings"]["environment"]
    engine = native.Engine(seed, environment)
    contract = native.ContractSession(environment, layout.units)
    script = _agent(config.source, "none")
    features = np.empty((1, layout.features), dtype=np.float16)
    inputs = torch.from_numpy(features)
    steps = torch.zeros(1, dtype=torch.long)
    torch.manual_seed(2 * seed + 1 - seat)
    actions_hash = hashlib.sha256()
    with torch.inference_mode():
        for step in range(719):
            contract.update(dict(engine.observation(1 - seat)))
            contract.observe_into(features)
            steps.fill_(step)
            program = actor(inputs, steps).numpy()
            contract.set_program(program, 1, list(layout.quantities))
            neural_action = dict(contract.program_action())
            action = script(dict(engine.observation(seat)), dict(engine.configuration))
            actions = [action, neural_action] if seat == 0 else [neural_action, action]
            actions_hash.update(orjson.dumps(actions, option=orjson.OPT_SORT_KEYS))
            actions_hash.update(b"\0")
            engine.step(*actions)
    if not engine.done:
        raise RuntimeError("neural comparison did not finish")
    own, other = float(engine.money(seat)), float(engine.money(1 - seat))
    return {
        "variant": "enterprise_p1",
        "opponent": f"neural_u{metadata['update']}",
        "seed": seed,
        "seat": seat,
        "cash": own,
        "opponent_cash": other,
        "margin": own - other,
        "outcome": int(own > other) - int(own < other),
        "action_sha256": actions_hash.hexdigest(),
    }


def run(config: Panel) -> None:
    """Retain every complete match and summarize only the declared fixed panel."""
    if not config.output.resolve().is_relative_to((Path.cwd() / "outputs").resolve()):
        raise ValueError("neural research results must remain under outputs")
    config.output.mkdir(parents=True, exist_ok=False)
    fingerprint = digest(config.source)
    write_json(
        config.output / "protocol.json",
        {
            "configuration": config.model_dump(mode="json"),
            "source_sha256": fingerprint,
            "runner_sha256": digest(Path(__file__)),
            "reference": json.loads((config.reference / "manifest.json").read_text()),
            "sampling": "CPU FP32 T=1, torch RNG seed=2*world+neural_seat",
        },
    )
    jobs = [(seed, seat) for seed in config.seeds for seat in (0, 1)]
    rows = []
    with ProcessPoolExecutor(
        max_workers=config.workers,
        mp_context=multiprocessing.get_context("spawn"),
        max_tasks_per_child=1,
    ) as pool:
        futures = {
            pool.submit(play, config, seed, seat, fingerprint): i
            for i, (seed, seat) in enumerate(jobs)
        }
        for future in as_completed(futures):
            row = future.result()
            rows.append(row)
            write_json(config.output / "games" / f"{futures[future]:04d}.json", row)
            print(f"completed {len(rows)}/{len(jobs)}", flush=True)
    write_json(config.output / "summary.json", summarize(rows))


@hydra.main(version_base=None, config_path="../../../../configs", config_name="enterprise_neural")
def main(configuration: DictConfig) -> None:
    """Evaluate an independent frozen script against the declared reference model."""
    run(Panel.model_validate(OmegaConf.to_container(configuration.panel, resolve=True)))


if __name__ == "__main__":
    main()
