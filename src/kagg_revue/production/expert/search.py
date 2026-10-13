"""Whole-game candidate comparisons with bounded device-resident window tapes."""

import time
from dataclasses import dataclass
from typing import Any

import numpy as np
import torch
from torch import Tensor

from kagg_revue.learning.collection.population import create_training_batch, script_games
from kagg_revue.policy.inference import ActorRuntime
from kagg_revue.production.expert.config import ExpertSettings
from kagg_revue.production.expert.proposals import SearchPolicy


@dataclass
class WindowTape:
    """One contiguous observation/action window per physical game."""

    observations: Tensor
    actions: Tensor
    steps: Tensor
    valid: Tensor

    def clone(self) -> "WindowTape":
        """Retain a candidate independently of reusable rollout buffers."""
        return WindowTape(
            *(v.clone() for v in (self.observations, self.actions, self.steps, self.valid))
        )


@dataclass
class SearchResult:
    """Hindsight search labels; these are not the deployable policy's outcomes."""

    baseline: WindowTape
    expert: WindowTape
    improved: Tensor
    report: dict[str, Any]


def strict_improvements(candidate: Tensor, incumbent: Tensor) -> Tensor:
    """Accept only a strictly higher terminal WDL, preserving the incumbent on ties."""
    return candidate > incumbent


class Search:
    """Reuse one native shard and one graph shape for all complete candidates."""

    def __init__(self, config: ExpertSettings, policy: SearchPolicy) -> None:
        """Resolve physical-game ownership before entering the sequential turn loop."""
        self.config = config
        self.policy = policy
        p = config.production
        count = p.ppo.games_per_update // len(p.devices)
        self.selfplay = count - script_games(p, count)
        device = next(policy.parameters()).device
        games = torch.arange(count, device=device)
        self.seats = games[: self.selfplay] % 2
        self.rows = torch.cat(
            (2 * games[: self.selfplay] + self.seats, games[self.selfplay :] + self.selfplay)
        )
        self.runtime = ActorRuntime(
            policy,
            count + self.selfplay,
            sample=False,
            precision=p.precision,
            bf16_reduced_precision_reduction=p.bf16_reduced_precision_reduction,
        )
        self.length = max(proposal.decisions for proposal in config.proposals)

    def _play(
        self, seeds: list[int], starts: Tensor
    ) -> tuple[WindowTape, np.ndarray[Any, Any], dict[str, float]]:
        policy, runtime, p = self.policy, self.runtime, self.config.production
        device = runtime.device
        count = len(seeds)
        batch = create_training_batch(p, seeds)
        tape = WindowTape(
            torch.zeros(
                (self.length, count, policy.layout.observation.features),
                device=device,
                dtype=torch.float16,
            ),
            torch.zeros(
                (self.length, count, policy.layout.factors), device=device, dtype=torch.int16
            ),
            starts[None] + torch.arange(self.length, device=device)[:, None],
            torch.ones((self.length, count), device=device, dtype=torch.bool),
        )
        lanes = torch.arange(count, device=device)
        encode = inference = native = 0.0
        started = time.perf_counter()
        for decision, span in enumerate(policy.layout.spans):
            phase = time.perf_counter()
            batch.observe_into(runtime.host.numpy())
            encode += time.perf_counter() - phase
            phase = time.perf_counter()
            actions, _ = runtime.act(decision)
            slot = (decision - starts).clamp(0, self.length - 1)
            active = ((decision >= starts) & (decision < starts + self.length))[:, None]
            tape.observations[slot, lanes] = torch.where(
                active, runtime.observations[self.rows], tape.observations[slot, lanes]
            )
            tape.actions[slot, lanes] = torch.where(
                active, actions[self.rows].short(), tape.actions[slot, lanes]
            )
            inference += time.perf_counter() - phase
            phase = time.perf_counter()
            batch.advance(runtime.selected.numpy(), span)
            native += time.perf_counter() - phase
        torch.cuda.synchronize(device)
        cash = batch.cash(p.turns)
        # Alternate the explored self-play seat; the other frozen actor reacts normally.
        cash[: self.selfplay] = np.where(
            (np.arange(self.selfplay) % 2)[:, None] == 0,
            cash[: self.selfplay],
            cash[: self.selfplay, ::-1],
        )
        return (
            tape,
            cash,
            {
                "rollout_seconds": time.perf_counter() - started,
                "encoding_seconds": encode,
                "inference_seconds": inference,
                "native_seconds": native,
                "collation_seconds": 0.0,
            },
        )

    def run(self, seeds: list[int]) -> SearchResult:
        """Search identical seed/opponent games, never rank candidates by cash."""
        started = time.perf_counter()
        device = self.runtime.device
        starts = torch.randint(
            self.policy.layout.decisions - self.length + 1, (len(seeds),), device=device
        )
        self.policy.ends.zero_()
        baseline, cash, timing = self._play(seeds, starts)
        baseline_outcome = torch.as_tensor(np.sign(cash[:, 0] - cash[:, 1]), device=device)
        best_outcome = baseline_outcome.clone()
        best = baseline.clone()
        winner = torch.zeros(len(seeds), dtype=torch.long, device=device)
        records = []
        for index, proposal in enumerate(self.config.proposals, 1):
            self.policy.starts.zero_()
            self.policy.ends.zero_()
            self.policy.starts[self.rows] = starts
            self.policy.ends[self.rows] = starts + proposal.decisions
            self.policy.search_temperature.fill_(proposal.temperature)
            candidate, candidate_cash, candidate_timing = self._play(seeds, starts)
            outcome = torch.as_tensor(
                np.sign(candidate_cash[:, 0] - candidate_cash[:, 1]), device=device
            )
            better = strict_improvements(outcome, best_outcome)
            best.observations[:, better] = candidate.observations[:, better]
            best.actions[:, better] = candidate.actions[:, better]
            best.valid[:, better] = (torch.arange(self.length, device=device) < proposal.decisions)[
                :, None
            ]
            best_outcome = torch.where(better, outcome, best_outcome)
            winner = torch.where(better, index, winner)
            records.append(
                {
                    "candidate": index,
                    **proposal.model_dump(),
                    "wins": int((outcome > 0).sum()),
                    "ties": int((outcome == 0).sum()),
                    "losses": int((outcome < 0).sum()),
                    "better_than_baseline": int((outcome > baseline_outcome).sum()),
                    "worse_than_baseline": int((outcome < baseline_outcome).sum()),
                    "mean_cash": float(candidate_cash[:, 0].mean()),
                    "timing": candidate_timing,
                }
            )
            print(
                {
                    "device": str(device),
                    "search_candidate": index,
                    "improved_games_so_far": int((best_outcome > baseline_outcome).sum()),
                },
                flush=True,
            )
        improved = best_outcome > baseline_outcome
        report = {
            "seed_start": min(seeds),
            "seed_end": max(seeds),
            "root_games": len(seeds),
            "physical_games": len(seeds) * (1 + len(records)),
            "baseline": {
                "wins": int((baseline_outcome > 0).sum()),
                "ties": int((baseline_outcome == 0).sum()),
                "losses": int((baseline_outcome < 0).sum()),
                "mean_cash": float(cash[:, 0].mean()),
                "timing": timing,
            },
            "candidates": records,
            "improved_games": int(improved.sum()),
            "improved_selfplay": int(improved[: self.selfplay].sum()),
            "improved_script": int(improved[self.selfplay :].sum()),
            "winner": winner.cpu().tolist(),
            "search_seconds": time.perf_counter() - started,
            "hindsight_labels_only": True,
            "deployment_budget_qualified": False,
        }
        self.policy.ends.zero_()
        return SearchResult(baseline, best, improved, report)
