"""Official full-game checks for the existing C++ opponent implementations."""

import hashlib
import json
import time
from pathlib import Path
from typing import Any

import numpy as np
import torch

from kagg_revue.bc.actions import ReplayActionEncoder
from kagg_revue.learning import state as artifacts
from kagg_revue.learning.adapter import runtime_settings
from kagg_revue.learning.collection.prefetch import ScriptPrefetch
from kagg_revue.learning.collection.public import create_public_batch, records
from kagg_revue.learning.config import Experiment
from kagg_revue.native import _revue_core as core
from kagg_revue.native import _revue_native as native
from kagg_revue.native.comparison import MirrorReference
from kagg_revue.opponents.native_batch import create_native_opponent_session
from kagg_revue.opponents.public import PublicAgentRuntime
from kagg_revue.policy.inference import ActorRuntime


def official(config: Experiment, state: dict[str, Any], options: dict[str, Any]) -> dict[str, Any]:
    """Compare native batches, original scripts and official state on complete games."""
    assert config.script_population is not None
    count, start = int(options["official_games"]), int(options["official_seed"])
    names = config.script_population.agents
    if count <= 0 or count % (2 * len(names)):
        raise ValueError("official qualification must balance every script and both seats")
    jobs: list[tuple[int, int, str]] = [
        (start + i // 2, i % 2, names[(i // 2) % len(names)]) for i in range(count)
    ]
    settings = runtime_settings(config)
    if config.population.sampled_counts:
        settings = settings.model_copy(update={"script_population": config.script_population})
    batch = create_public_batch(settings, jobs)
    engines = [native.Engine(seed, config.environment) for seed, _, _ in jobs]
    reference = MirrorReference(
        Path(options["reference_directory"]), config.environment, [seed for seed, _, _ in jobs]
    )
    selected = records(config.script_population)
    opponents = [
        PublicAgentRuntime(selected[name], Path.cwd(), engine.configuration)
        for engine, (_, _, name) in zip(engines, jobs, strict=True)
    ]
    maximum = int(config.environment["maxMarketOrdersPerTurn"])
    native_opponents = [create_native_opponent_session(name, maximum) for _, _, name in jobs]
    encoder = ReplayActionEncoder(native.action_codec_spec())
    device = torch.device(options.get("inference_device", "cpu"))
    actor, payload = artifacts.load_member(config, state, state["latest"], device)
    del payload
    actor.eval()
    torch.set_num_threads(1)
    sessions = [core.ContractSession(config.environment, config.unit_limit) for _ in jobs]
    observations = np.empty((count, actor.layout.observation.features), np.float16)
    expected = np.empty_like(observations)
    trajectory = hashlib.sha256()
    started = time.perf_counter()
    devices = [device.index if device.index is not None else 0] if device.type == "cuda" else []
    with (
        torch.random.fork_rng(devices=devices),
        torch.inference_mode(),
        ScriptPrefetch(getattr(batch, "prepare_opponents", None)) as prefetch,
    ):
        torch.manual_seed(start)
        runtime = ActorRuntime(
            actor,
            count,
            sample=True,
            temperature=settings.ppo.temperature,
            precision=settings.precision,
            bf16_reduced_precision_reduction=settings.bf16_reduced_precision_reduction,
        )
        for turn in range(settings.turns):
            views = reference.observations(engines)
            prefetch.start()
            batch.observe_into(observations)
            for i, (_, seat, _) in enumerate(jobs):
                for player in (0, 1):
                    if batch.observation(i, player) != engines[i].observation(player):
                        raise ValueError(f"native batch state differs at turn {turn}, game {i}")
                sessions[i].update(views[2 * i + seat])
                sessions[i].observe_into(expected[i : i + 1])
            np.testing.assert_array_equal(observations, expected)
            np.copyto(runtime.host.numpy(), expected)
            runtime.act(turn)
            plans = runtime.selected.numpy()
            expected_actions = []
            for i, (_, seat, name) in enumerate(jobs):
                sessions[i].set_program(plans[i : i + 1], 1, list(settings.quantities))
                actions: list[dict[str, Any]] = [{}, {}]
                actions[seat] = dict(sessions[i].program_action())
                view = views[2 * i + 1 - seat]
                actions[1 - seat] = opponents[i].act(view)
                compiled = native.native_opponent_action(engines[i], 1 - seat, native_opponents[i])
                unit_count = 1 + len(view["farms"][1 - seat]["hands"])
                left = encoder.encode(compiled, unit_count=unit_count, max_market_orders=maximum)
                right = encoder.encode(
                    actions[1 - seat], unit_count=unit_count, max_market_orders=maximum
                )
                if (left.tokens, left.quantities) != (right.tokens, right.quantities):
                    raise ValueError(f"C++ script differs from original: {name}, turn {turn}")
                expected_actions.append(actions)
            prefetch.wait()
            batch.advance_programs(plans, 1, 1)
            trajectory.update(json.dumps(expected_actions, sort_keys=True).encode())
            for engine, game, actions in zip(
                engines, reference.games, expected_actions, strict=True
            ):
                engine.step(*actions)
                game.step(actions)
    reference.observations(engines)
    for i, engine in enumerate(engines):
        for seat in (0, 1):
            if batch.observation(i, seat) != engine.observation(seat):
                raise ValueError("native batch final state differs from official reference")
    if batch.completed_games != count or batch.transitions != count * settings.turns:
        raise ValueError("public training did not finish its exact physical-game budget")
    return {
        "passed": True,
        "backend": "native-cpp",
        "inference_device": str(device),
        "games": count,
        "independent_seeds": count // 2,
        "opponents": list(names),
        "official_reference": reference.report(),
        "matched_learner_feature_rows": count * settings.turns,
        "matched_script_actions": count * settings.turns,
        "script_prefetch": prefetch.prepare is not None,
        "trajectory_sha256": trajectory.hexdigest(),
        "cash": batch.cash().tolist(),
        "wall_seconds": time.perf_counter() - started,
        "scope": "integration correctness only; no algorithm comparison or strength claim",
    }
