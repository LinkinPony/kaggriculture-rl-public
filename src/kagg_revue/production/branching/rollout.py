"""Batched native state forks and terminal continuations over model-generated programs."""

import time
from typing import Any, cast

import numpy as np
import torch
from torch import Tensor, nn

from kagg_revue.learning.collection.population import (
    TrainingBatch,
    create_training_batch,
    script_games,
)
from kagg_revue.policy.inference import ActorRuntime
from kagg_revue.policy.spatial.model import Policy
from kagg_revue.policy.spatial.work import WorkPolicy
from kagg_revue.production.branching.actors import ContinuationPolicy
from kagg_revue.production.branching.config import BranchSettings
from kagg_revue.production.branching.data import BranchTape
from kagg_revue.production.branching.proposals import ProposalPolicy, proposal_controls
from kagg_revue.production.expert.imitation import ExpertLabels
from kagg_revue.production.expert.telemetry import progress


def fork_batch(batch: TrainingBatch, self_indices: Any, script_indices: Any) -> TrainingBatch:
    """Fork both persistent populations without exposing native game objects to Python."""
    names = batch.opponents
    return TrainingBatch(
        batch.selfplay.fork(np.asarray(self_indices, dtype=np.int64)),
        batch.scripts.fork(np.asarray(script_indices, dtype=np.int64)),
        len(self_indices),
        ("self_play",) * len(self_indices)
        + tuple(names[batch.selfplay_games + int(i)] for i in script_indices),
        batch.program_capacity,
    )


class StateSearch:
    """One prefix batch, one proposal graph and one shared continuation graph per rank."""

    def __init__(
        self, config: BranchSettings, student: WorkPolicy, alternate: WorkPolicy, rank: int
    ):
        """Resolve production shapes before entering any sequential game loop."""
        self.config, self.rank, self.alternate = config, rank, alternate
        p, device, layout = config.production, next(student.parameters()).device, student.layout
        self.frozen = (
            cast(WorkPolicy, Policy.from_layout(layout).to(device)).eval().requires_grad_(False)
        )
        self.frozen.load_state_dict(student.state_dict())
        self.games = p.ppo.games_per_update // len(p.devices)
        self.scripts = script_games(p, self.games)
        self.selfplay = self.games - self.scripts
        self.roots = self.games // config.root_groups
        self.self_roots = self.selfplay // config.root_groups
        self.script_roots = self.scripts // config.root_groups
        runtime_options: dict[str, Any] = {
            "sample": False,
            "precision": p.precision,
            "bf16_reduced_precision_reduction": p.bf16_reduced_precision_reduction,
        }
        self.prefix = ActorRuntime(self.frozen, 2 * self.selfplay + self.scripts, **runtime_options)
        self.proposal = (
            ProposalPolicy(layout, self.roots * config.candidates)
            .to(device)
            .eval()
            .requires_grad_(False)
        )
        self.proposal.load_state_dict(student.state_dict())
        self.generator = ActorRuntime(
            self.proposal, self.roots * config.candidates, **runtime_options
        )
        self.workspace = Policy.from_layout(layout).to(device).eval().requires_grad_(False)
        self.workspace.load_state_dict(student.state_dict())
        seats = (torch.arange(self.self_roots, device=device) % 2).repeat_interleave(
            config.candidates
        )
        self.mixed = ContinuationPolicy(
            self.workspace, self.frozen, seats, self.script_roots * config.candidates
        )
        self.suffix = ActorRuntime(
            self.mixed,
            (2 * self.self_roots + self.script_roots) * config.candidates,
            **runtime_options,
        )
        self.label_graph: nn.Module | None = None
        self.capture_seconds = sum(
            r.capture_seconds for r in (self.prefix, self.generator, self.suffix)
        )

    def _labels(self, observations: Tensor, steps: Tensor) -> tuple[Tensor, Tensor]:
        if self.label_graph is None:
            wrapper = ExpertLabels(self.frozen, self.config.production.precision == "bf16")
            self.label_graph = cast(
                nn.Module,
                torch.cuda.make_graphed_callables(wrapper, (observations.clone(), steps.clone())),
            )
        return cast(tuple[Tensor, Tensor], self.label_graph(observations, steps))

    @torch.no_grad()
    def _root(self, batch: TrainingBatch, group: int, decision: int, tape: BranchTape) -> None:
        c, p = self.config, self.config.production
        device = self.prefix.device
        started = time.perf_counter()
        self_indices = np.arange(group * self.self_roots, (group + 1) * self.self_roots)
        script_indices = np.arange(group * self.script_roots, (group + 1) * self.script_roots)
        rows = np.concatenate(
            (2 * self_indices + self_indices % 2, 2 * self.selfplay + script_indices)
        )
        observations = self.prefix.observations[torch.as_tensor(rows, device=device)]
        steps = torch.full((self.roots,), decision, device=device, dtype=torch.long)
        base_actions, logits = self._labels(observations, steps)
        forced = proposal_controls(
            self.frozen,
            observations,
            steps,
            base_actions,
            logits,
            c.candidates,
            c.pivots,
            c.alternatives,
        )
        self.proposal.forced.copy_(forced.flatten(0, 1))
        self.generator.host.copy_(
            self.prefix.host[torch.as_tensor(rows)].repeat_interleave(c.candidates, 0)
        )
        actions, probabilities = self.generator.act(decision)
        selection = slice(group * self.roots, (group + 1) * self.roots)
        tape.observations[selection].copy_(observations)
        tape.steps[selection].fill_(decision)
        tape.actions[selection].copy_(actions.reshape(self.roots, c.candidates, -1))
        tape.previous[selection].copy_(probabilities.sum(-1).reshape(self.roots, c.candidates))
        tape.seats[selection] = torch.as_tensor(
            np.concatenate((self_indices % 2, script_indices % 2)), device=device
        )
        tape.scripts[selection] = torch.arange(self.roots, device=device) >= self.self_roots
        prefix_indices = np.concatenate((self_indices, self.selfplay + script_indices))
        tape.seeds[selection] = self.seeds[torch.as_tensor(prefix_indices, device=device)]
        tape.timing["proposal_seconds"] += time.perf_counter() - started
        started = time.perf_counter()
        branches = fork_batch(
            batch, np.repeat(self_indices, c.candidates), np.repeat(script_indices, c.candidates)
        )
        tape.timing["fork_seconds"] += time.perf_counter() - started
        # Root opponent actions are shared; later reactions use independent cloned memory.
        programs = torch.empty_like(self.suffix.actions)
        programs[self.mixed.own_rows] = actions
        opponent_rows = torch.as_tensor(2 * self_indices + 1 - self_indices % 2, device=device)
        programs[self.mixed.opponent_rows] = self.prefix.actions[opponent_rows].repeat_interleave(
            c.candidates, 0
        )
        self.suffix.selected.copy_(programs, non_blocking=True)
        torch.cuda.current_stream(device).synchronize()
        branches.advance(self.suffix.selected.numpy(), self.frozen.layout.spans[decision])
        for continuation, policy in enumerate((self.frozen, self.alternate)):
            progress(
                p.output_dir,
                self.update,
                self.rank,
                "continuation",
                2 * group + continuation,
                2 * c.root_groups,
            )
            started = time.perf_counter()
            continued = fork_batch(
                branches,
                np.arange(branches.selfplay_games),
                np.arange(self.script_roots * c.candidates),
            )
            tape.timing["fork_seconds"] += time.perf_counter() - started
            self.workspace.load_state_dict(policy.state_dict())
            for following in range(decision + 1, self.frozen.layout.decisions):
                started = time.perf_counter()
                continued.observe_into(self.suffix.host.numpy())
                tape.timing["encoding_seconds"] += time.perf_counter() - started
                started = time.perf_counter()
                self.suffix.act(following)
                tape.timing["inference_seconds"] += time.perf_counter() - started
                started = time.perf_counter()
                continued.advance(self.suffix.selected.numpy(), self.frozen.layout.spans[following])
                tape.timing["native_seconds"] += time.perf_counter() - started
            cash = torch.as_tensor(continued.cash(p.turns), device=device)
            learned_seats = self.mixed.own_rows[: branches.selfplay_games] % 2
            first = cash[: branches.selfplay_games]
            cash[: branches.selfplay_games] = torch.where(
                learned_seats[:, None] == 0, first, first.flip(-1)
            )
            cash = cash.reshape(self.roots, c.candidates, 2)
            tape.cash[selection, continuation] = cash
            tape.outcomes[selection, continuation] = (
                (cash[..., 0] - cash[..., 1]).sign().to(torch.int8)
            )

    @torch.no_grad()
    def run(self, student: WorkPolicy, update: int) -> BranchTape:
        """Sample stratified root times and simulate every candidate through termination."""
        started = time.perf_counter()
        c, p, device = self.config, self.config.production, self.prefix.device
        self.update = update
        self.frozen.load_state_dict(student.state_dict())
        self.proposal.load_state_dict(student.state_dict())
        start = p.ppo.seed_start + (update - 1) * p.ppo.games_per_update + self.rank * self.games
        seeds = [start + i // 2 for i in range(self.games)]
        self.seeds = torch.tensor(seeds, device=device)
        batch = create_training_batch(p, seeds)
        tape = BranchTape.allocate(
            self.games,
            c.candidates,
            student.layout.observation.features,
            student.layout.factors,
            device,
        )
        tape.timing = dict.fromkeys(
            (
                "fork_seconds",
                "proposal_seconds",
                "encoding_seconds",
                "inference_seconds",
                "native_seconds",
            ),
            0.0,
        )
        boundaries = np.linspace(0, student.layout.decisions, c.root_groups + 1, dtype=int)
        rng = np.random.default_rng(c.root_seed + update)
        roots = {
            int(rng.integers(a, b)): group
            for group, (a, b) in enumerate(zip(boundaries[:-1], boundaries[1:], strict=True))
        }
        progress(p.output_dir, update, self.rank, "prefix", 0, student.layout.decisions)
        for decision, span in enumerate(student.layout.spans):
            phase = time.perf_counter()
            batch.observe_into(self.prefix.host.numpy())
            tape.timing["encoding_seconds"] += time.perf_counter() - phase
            phase = time.perf_counter()
            self.prefix.act(decision)
            tape.timing["inference_seconds"] += time.perf_counter() - phase
            if decision in roots:
                self._root(batch, roots[decision], decision, tape)
            phase = time.perf_counter()
            batch.advance(self.prefix.selected.numpy(), span)
            tape.timing["native_seconds"] += time.perf_counter() - phase
        tape.prefix_cash = batch.cash(p.turns)
        tape.timing["rollout_seconds"] = time.perf_counter() - started
        tape.timing["collation_seconds"] = 0.0
        return tape
