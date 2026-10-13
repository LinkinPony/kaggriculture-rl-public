"""Focused comparison with the frozen official Python interpreter, outside training."""

import json
import time
from pathlib import Path

import numpy as np
import torch

from kagg_revue.artifacts.io import digest, write_json
from kagg_revue.native import _revue_native
from kagg_revue.native.reference import Record, load_reference
from kagg_revue.policy.checkpoints import load_policy
from kagg_revue.production.config import Settings


def audit(settings: Settings) -> None:
    """Check both seats over a full season without running heavy reference panels."""
    if settings.checkpoint is None:
        raise ValueError("reference audit requires an explicit checkpoint")
    torch.set_num_threads(settings.cpu_threads)
    policy, _ = load_policy(settings.checkpoint, torch.device("cpu"))
    policy.eval()
    reference_dir = Path("data/external/kaggriculture-reference-1.32.7")
    official = load_reference(reference_dir)
    results = []
    for seat in (0, 1):
        seed = settings.evaluation_seed
        batch = _revue_native.ParallelBatch(
            settings.environment,
            [seed],
            [seat],
            ["pass"],
            [None],
            [],
            settings.unit_limit,
            1,
            list(settings.quantities),
        )
        engine = _revue_native.Engine(seed, settings.environment)
        session = _revue_native.ContractSession(settings.environment, settings.unit_limit)
        state = [
            Record(observation=Record(player=player, step=0), status="ACTIVE", action={})
            for player in (0, 1)
        ]
        env = Record(configuration=Record(**settings.environment, seed=seed), info={}, done=False)
        official.interpreter(state, env)
        features = np.empty((1, policy.layout.observation.features), dtype=np.float16)
        contract = np.zeros((1, policy.layout.factors), dtype=np.int64)
        maximum = total = overage = 0.0
        boundaries = {turn: decision for decision, turn in enumerate(policy.layout.starts)}
        for turn in range(settings.turns):
            started = time.perf_counter()
            if policy.layout.work:
                session.update(engine.observation(seat))
            if turn in boundaries:
                if policy.layout.work:
                    session.observe_into(features)
                else:
                    batch.observe_into(features)
                with torch.no_grad():
                    actions, _ = policy.act(
                        torch.from_numpy(features),
                        torch.tensor([boundaries[turn]]),
                        sample=False,
                    )
                contract[:] = actions.numpy()
                if policy.layout.work:
                    session.set_program(
                        contract, policy.layout.capacity, list(policy.layout.observation.quantities)
                    )
            action = (
                session.program_action()
                if policy.layout.work
                else batch.contract_action(0, contract)
            )
            seconds = time.perf_counter() - started
            maximum = max(maximum, seconds)
            total += seconds
            overage += max(0.0, seconds - 1.0)
            for player in (0, 1):
                state[player].action = action if player == seat else {}
                state[player].observation.step = turn
            official.interpreter(state, env)
            if policy.layout.work:
                engine.step(action if seat == 0 else {}, action if seat == 1 else {})
                expected = engine.observation(seat)
            else:
                batch.advance(contract, 1)
                expected = batch.observation(0)
            observed = state[seat].observation
            for field in ("farms", "private", "market", "town", "day", "hour"):
                if observed[field] != expected[field]:
                    raise AssertionError(
                        f"official interpreter mismatch at seat {seat}, turn {turn}, {field}"
                    )
        results.append(
            {
                "seat": seat,
                "seed": seed,
                "transitions": engine.step_index if policy.layout.work else batch.transitions,
                "cash": [[engine.money(seat), engine.money(1 - seat)]]
                if policy.layout.work
                else batch.cash().tolist(),
                "max_actor_seconds": maximum,
                "total_actor_seconds": total,
                "overage_used_seconds": overage,
            }
        )
    write_json(
        settings.output_dir / "reference-parity.json",
        {
            "official_interpreter": json.loads((reference_dir / "manifest.json").read_text()),
            "checkpoint_sha256": digest(settings.checkpoint),
            "games": results,
            "cpu_reason": "focused reference semantics and per-agent timing smoke",
            "full_kaggle_submission_qualified": False,
        },
    )
    print(json.dumps(results), flush=True)
