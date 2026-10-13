"""Overlap CPU game preparation with another group's causal CUDA inference."""

import math
import time
from concurrent.futures import Future, ThreadPoolExecutor
from contextlib import ExitStack
from dataclasses import dataclass, field
from typing import Any

import numpy as np
import torch

from kagg_revue.learning.collection.archive import PopulationCache
from kagg_revue.learning.collection.partitions import Partition, counts, partition
from kagg_revue.learning.collection.population import (
    TrainingBatch,
    create_training_batch,
    episode_weights,
    historical_games,
    policy_rows,
    script_games,
)
from kagg_revue.learning.collection.prefetch import ScriptPrefetch
from kagg_revue.learning.collection.quadrants import measure
from kagg_revue.learning.collection.sampling import Rollout, _advance
from kagg_revue.learning.config import Experiment
from kagg_revue.learning.optimization.objectives import terminal_rewards
from kagg_revue.learning.settings import RuntimeSettings
from kagg_revue.policy.inference import ActorRuntime
from kagg_revue.policy.spatial.model import Policy


@dataclass
class Group:
    """Each group exclusively owns its engine, host buffers and recurrent states."""

    part: Partition
    batch: TrainingBatch
    runtime: ActorRuntime
    history: ActorRuntime | None
    seeds: list[int]
    indices: torch.Tensor
    history_stream: Any = None
    scripts: ScriptPrefetch | None = None
    timing: dict[str, float] = field(
        default_factory=lambda: {
            "native_seconds": 0.0,
            "encoding_seconds": 0.0,
            "inference_seconds": 0.0,
            "script_compute_seconds": 0.0,
        }
    )

    def prepare(self) -> None:
        """Compute native decisions and encode only the current immutable state."""
        assert self.scripts is not None
        self.scripts.start()
        started = time.perf_counter()
        self.batch.observe_into(self.runtime.host.numpy())
        self.timing["encoding_seconds"] += time.perf_counter() - started

    def advance(
        self,
        begin: torch.cuda.Event,
        ready: torch.cuda.Event,
        decision: int,
        span: int,
        again: bool,
    ) -> None:
        """Wait for this group's D2H and tape copies before reusing any host buffer."""
        with torch.cuda.device(self.runtime.device):
            ready.synchronize()
            self.timing["inference_seconds"] += begin.elapsed_time(ready) / 1000
        assert self.scripts is not None
        self.scripts.wait()
        started = time.perf_counter()
        _advance(self.batch, self.runtime, span, decision, self.seeds)
        self.timing["native_seconds"] += time.perf_counter() - started
        if again:
            self.prepare()


class PipelineCollection:
    """Two CPU producers and stable, ordered GPU launches; every row stays on-policy."""

    def __init__(self, config: Experiment, actor: Policy, cache: PopulationCache | None) -> None:
        """Share model parameters while keeping all inference state private to each group."""
        if config.curriculum is not None:
            raise ValueError("pipelined collection currently requires fresh full games")
        self.config, self.actor, self.cache = config, actor, cache
        self.device = next(actor.parameters()).device
        self.runtimes: dict[tuple[int, int], ActorRuntime] = {}

    def runtime(self, slot: int, rows: int) -> ActorRuntime:
        """Capture a separate graph and causal memory for each group/row-count pair."""
        key = (slot, rows)
        if key not in self.runtimes:
            with torch.random.fork_rng(devices=[self.device]):
                self.runtimes[key] = ActorRuntime(
                    self.actor,
                    rows,
                    sample=True,
                    precision=self.config.precision,
                    bf16_reduced_precision_reduction=False,
                    compile_inference=bool(
                        self.config.execution and self.config.execution.compile_inference
                    ),
                )
        return self.runtimes[key]

    def prepare(self, world: int) -> None:
        """Warm the bounded learner shapes before measuring updates or resuming training."""
        config = self.config
        if not config.population.separate_scripts:
            return
        assert config.script_population is not None
        games = config.games // world
        history = int(config.games * config.population.fraction) // world
        pairs = config.games * config.script_population.fraction / (2 * world)
        for scripts in {2 * math.floor(pairs), 2 * math.ceil(pairs)}:
            for slot, (own, script, frozen) in enumerate(
                counts(games - history - scripts, scripts, history)
            ):
                self.runtime(slot, 2 * own + script + frozen)

    def groups(self, settings: RuntimeSettings, seeds: list[int], name: str | None) -> list[Group]:
        """Prepare frozen weights outside the measured CPU/GPU rollout pipeline."""
        groups = []
        for slot, part in enumerate(partition(settings, len(seeds))):
            runtime = self.runtime(slot, len(part.rows))
            history = None
            if part.history:
                assert self.cache is not None and name is not None
                with torch.random.fork_rng(devices=[self.device]):
                    history = self.cache.runtime(name, self.device, part.history, slot=slot + 1)
            local_seeds = [seeds[index] for index in part.games]
            group = Group(
                part,
                create_training_batch(part.settings, local_seeds, history),
                runtime,
                history,
                local_seeds,
                torch.tensor(part.rows, device=self.device),
            )
            if history is not None and settings.ppo.concurrent_history_inference:
                group.history_stream = torch.cuda.Stream(device=self.device)  # type: ignore[no-untyped-call]
            groups.append(group)
        return groups

    def collect(
        self,
        settings: RuntimeSettings,
        groups: list[Group],
        *,
        overlap: bool = True,
    ) -> Rollout:
        """Launch groups in a fixed RNG order while CPU advancement waits on per-group events.

        ``overlap=False`` uses the same partitions and launches as a serial reference.
        Phase times sum overlapping group work; rollout_seconds is the elapsed wall time.
        """
        layout = self.actor.layout
        games = sum(len(group.seeds) for group in groups)
        scripts, history = script_games(settings, games), historical_games(settings, games)
        selfplay = games - scripts - history
        rows = 2 * selfplay + scripts + history
        observations = torch.empty(
            (layout.decisions, rows, layout.observation.features),
            dtype=torch.float16,
            device=self.device,
        )
        actions = torch.empty(
            (layout.decisions, rows, layout.factors), dtype=torch.int16, device=self.device
        )
        probabilities = torch.empty_like(actions, dtype=torch.float32)
        wait_seconds = 0.0
        started = time.perf_counter()
        with ExitStack() as stack:
            for group in groups:
                group.scripts = stack.enter_context(ScriptPrefetch(group.batch.prepare_opponents))
            # Preserve each native team's allocator locality and thread-local
            # encoder scratch across turns instead of migrating groups between producers.
            pools = [
                stack.enter_context(
                    ThreadPoolExecutor(max_workers=1, thread_name_prefix=f"native-group-{slot}")
                )
                for slot in range(len(groups))
            ]
            futures: list[Future[None]] = [
                pool.submit(group.prepare) for pool, group in zip(pools, groups, strict=True)
            ]
            for decision, span in enumerate(layout.spans):
                for slot, group in enumerate(groups):
                    waited = time.perf_counter()
                    futures[slot].result()
                    wait_seconds += time.perf_counter() - waited
                    current = torch.cuda.current_stream(self.device)
                    begin, ready = (
                        torch.cuda.Event(enable_timing=True),  # type: ignore[no-untyped-call]
                        torch.cuda.Event(enable_timing=True),  # type: ignore[no-untyped-call]
                    )
                    begin.record(current)
                    if group.history_stream is not None:
                        group.history_stream.wait_stream(current)
                    selected, likelihood = group.runtime.act(decision, synchronize=False)
                    if group.history is not None:
                        if group.history_stream is None:
                            group.history.act(decision, synchronize=False)
                        else:
                            with torch.cuda.stream(group.history_stream):
                                group.history.act(decision, synchronize=False)
                            current.wait_stream(group.history_stream)
                    observations[decision].index_copy_(0, group.indices, group.runtime.observations)
                    actions[decision].index_copy_(0, group.indices, selected.to(torch.int16))
                    probabilities[decision].index_copy_(0, group.indices, likelihood)
                    ready.record(current)
                    futures[slot] = pools[slot].submit(
                        group.advance, begin, ready, decision, span, decision + 1 < layout.decisions
                    )
                    if not overlap:
                        futures[slot].result()
            for future in futures:
                future.result()
            for group in groups:
                assert group.scripts is not None
                group.timing["script_compute_seconds"] = group.scripts.compute_seconds
                group.timing["script_wait_seconds"] = group.scripts.wait_seconds
        torch.cuda.synchronize(self.device)
        elapsed = time.perf_counter() - started
        cash = np.empty((games, 2), np.float64)
        opponents = [""] * games
        for group in groups:
            cash[list(group.part.games)] = group.batch.cash(layout.observation.turns)
            for index, name in zip(group.part.games, group.batch.opponents, strict=True):
                opponents[index] = name
        rewards = terminal_rewards(
            cash,
            cash_weight=settings.ppo.cash_weight,
            cash_scale=settings.ppo.cash_scale,
            win_weight=settings.ppo.win_weight,
            cash_margin=settings.ppo.cash_margin,
        )
        timing = {key: sum(group.timing[key] for group in groups) for key in groups[0].timing}
        timing.update(
            rollout_seconds=elapsed,
            scheduler_wait_seconds=wait_seconds,
            physical_games_per_second=games / elapsed,
            pipeline_groups=float(len(groups)),
            collation_seconds=0.0,
        )
        monitoring_started = time.perf_counter()
        terminal = torch.empty((rows, layout.observation.features), dtype=torch.float16)
        for group in groups:
            group.batch.observe_into(group.runtime.host.numpy())
            terminal[list(group.part.rows)] = group.runtime.host
        land = measure(observations, terminal, layout)
        timing["quadrant_monitor_seconds"] = time.perf_counter() - monitoring_started
        timing["rollout_seconds"] += timing["quadrant_monitor_seconds"]
        timing["physical_games_per_second"] = games / timing["rollout_seconds"]
        return Rollout(
            observations.flatten(0, 1),
            actions.flatten(0, 1),
            probabilities.flatten(0, 1),
            torch.arange(layout.decisions, device=self.device).repeat_interleave(rows),
            torch.tensor(
                policy_rows(rewards, selfplay), device=self.device, dtype=torch.float32
            ).repeat(layout.decisions),
            cash,
            timing,
            torch.tensor(episode_weights(selfplay, scripts + history), device=self.device).repeat(
                layout.decisions
            ),
            tuple(opponents),
            groups[0].runtime.temperature,
            land,
        )
