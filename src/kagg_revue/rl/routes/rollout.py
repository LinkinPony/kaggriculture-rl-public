"""Complete-match rollout for event-driven route PPO."""

from __future__ import annotations

import time
from collections.abc import Mapping, Sequence
from dataclasses import dataclass

import numpy as np
import torch
from numpy.typing import NDArray

from kagg_revue.core.backend import BackendApi
from kagg_revue.opponents.kaito.native import create_native_session as kaito_session
from kagg_revue.opponents.native_batch import (
    create_native_opponent_session,
    step_native_opponent_batch,
)
from kagg_revue.rl.capabilities.direct_control import collect_paired_direct_control
from kagg_revue.rl.routes.contract import ROUTE_DECISION_BY_STEP, ROUTE_DECISIONS
from kagg_revue.rl.routes.features import encode_route_features
from kagg_revue.rl.routes.model import RouteActorCritic

RouteJob = tuple[int, int, str]


@dataclass(frozen=True, slots=True)
class RouteGameResult:
    """Direct outcome record for one paired-seat complete match."""

    seed: int
    seat: int
    opponent_id: str
    outcome: int
    direct_outcome: int
    terminal_cash: float
    opponent_cash: float
    direct_terminal_cash: float
    direct_opponent_cash: float
    selected_route: int


@dataclass(frozen=True, slots=True)
class RouteRolloutBatch:
    """Sparse PPO decisions plus their complete terminal outcomes."""

    features: NDArray[np.float32]
    prior_actions: NDArray[np.int64]
    actions: NDArray[np.int64]
    actor_weights: NDArray[np.float32]
    old_log_probabilities: NDArray[np.float32]
    old_values: NDArray[np.float32]
    episode_indices: NDArray[np.int64]
    decision_indices: NDArray[np.int64]
    candidate_routes: NDArray[np.int64]
    game_rewards: NDArray[np.float32]
    games: tuple[RouteGameResult, ...]
    diagnostics: dict[str, float | int]

    def validate(self) -> None:
        """Reject misaligned sparse decisions before optimization."""
        decisions = self.features.shape[0]
        if self.features.ndim != 2 or decisions < 1:
            raise ValueError("route rollout must contain two-dimensional decisions")
        arrays = (
            self.prior_actions,
            self.actions,
            self.actor_weights,
            self.old_log_probabilities,
            self.old_values,
            self.episode_indices,
            self.decision_indices,
            self.candidate_routes,
        )
        if any(value.shape != (decisions,) for value in arrays):
            raise ValueError("route rollout decision arrays differ in length")
        if self.game_rewards.shape != (len(self.games),):
            raise ValueError("route rollout rewards differ from complete games")
        if np.any(self.episode_indices < 0) or np.any(self.episode_indices >= len(self.games)):
            raise ValueError("route rollout episode index is outside its game batch")


class RouteRolloutCollector:
    """Run route-selected Kaito against a frozen native population."""

    def __init__(
        self,
        backend: BackendApi,
        model: RouteActorCritic,
        environment: Mapping[str, object],
        *,
        unit_limit: int,
        cpu_workers: int,
        action_generator: torch.Generator,
    ) -> None:
        """Bind immutable execution and sampling state."""
        self._backend = backend
        self._model = model
        self._environment = dict(environment)
        self._unit_limit = unit_limit
        self._cpu_workers = cpu_workers
        self._action_generator = action_generator
        market_orders = self._environment.get("maxMarketOrdersPerTurn")
        if not isinstance(market_orders, int) or isinstance(market_orders, bool):
            raise TypeError("route rollout market order capacity must be an integer")
        self._maximum_market_orders = market_orders

    def collect(self, jobs: Sequence[RouteJob], *, sample: bool) -> RouteRolloutBatch:
        """Collect one PPO batch and its same-job frozen DIRECT control."""
        if not jobs:
            raise ValueError("route rollout requires complete-match jobs")
        engines = [
            self._backend.engine(seed=int(seed), configuration=self._environment)
            for seed, _seat, _opponent in jobs
        ]
        players = np.asarray([seat for _seed, seat, _opponent in jobs], dtype=np.int64)
        opponent_ids = tuple(opponent for _seed, _seat, opponent in jobs)
        sessions = [kaito_session(self._maximum_market_orders) for _ in jobs]
        opponent_sessions = [
            create_native_opponent_session(opponent, self._maximum_market_orders)
            for opponent in opponent_ids
        ]
        routes = np.zeros(len(jobs), dtype=np.int64)
        width = self._maximum_market_orders + self._unit_limit
        tokens = np.zeros((len(jobs), width), dtype=np.int64)
        quantities = np.zeros_like(tokens)
        decision_counts = np.zeros(len(jobs), dtype=np.int64)
        unit_counts = np.zeros(len(jobs), dtype=np.int64)
        done = np.zeros(len(jobs), dtype=np.bool_)

        feature_rows: list[NDArray[np.float32]] = []
        prior_rows: list[NDArray[np.int64]] = []
        action_rows: list[NDArray[np.int64]] = []
        actor_weight_rows: list[NDArray[np.float32]] = []
        log_probability_rows: list[NDArray[np.float32]] = []
        value_rows: list[NDArray[np.float32]] = []
        episode_rows: list[NDArray[np.int64]] = []
        decision_rows: list[NDArray[np.int64]] = []
        candidate_rows: list[NDArray[np.int64]] = []
        diverged = np.zeros(len(jobs), dtype=np.bool_)
        actor_seconds = 0.0
        primitive_turns = 0
        started = time.perf_counter()
        previous_training = self._model.training
        self._model.eval()
        try:
            while not bool(done.all()):
                step = int(engines[0].step_index)
                if any(int(engine.step_index) != step for engine in engines):
                    raise RuntimeError("route rollout lanes lost lockstep")
                route_decision = ROUTE_DECISION_BY_STEP.get(step)
                if route_decision is not None:
                    active = np.flatnonzero(routes == 0).astype(np.int64, copy=False)
                    if active.size:
                        actor_started = time.perf_counter()
                        active_players = players[active]
                        prior = np.fromiter(
                            (
                                int(
                                    self._backend.kaito_v48_proposed_route(
                                        engines[int(index)],
                                        int(players[int(index)]),
                                        0,
                                    )
                                    == route_decision.route_index
                                )
                                for index in active
                            ),
                            dtype=np.int64,
                            count=int(active.size),
                        )
                        decision_index = ROUTE_DECISIONS.index(route_decision)
                        features = encode_route_features(
                            self._backend,
                            [engines[int(index)] for index in active],
                            active_players,
                            decision_index=decision_index,
                            candidate_route=route_decision.route_index,
                            prior_actions=prior,
                            unit_limit=self._unit_limit,
                            workers=self._cpu_workers,
                        )
                        device = next(self._model.parameters()).device
                        feature_tensor = torch.as_tensor(features, device=device)
                        prior_tensor = torch.as_tensor(prior, device=device)
                        with torch.no_grad():
                            logits, values = self._model(feature_tensor, prior_tensor)
                            log_probabilities = torch.log_softmax(logits, dim=-1)
                            if sample:
                                probabilities = log_probabilities.exp()
                                actions = torch.multinomial(
                                    probabilities,
                                    1,
                                    generator=self._action_generator,
                                ).squeeze(1)
                            else:
                                actions = logits.argmax(dim=-1)
                            selected_log_probabilities = log_probabilities.gather(
                                1,
                                actions[:, None],
                            ).squeeze(1)
                        action_values = actions.cpu().numpy().astype(np.int64, copy=False)
                        mismatched = action_values != prior
                        actor_weights = np.logical_or(diverged[active], mismatched).astype(
                            np.float32,
                            copy=False,
                        )
                        diverged[active[mismatched]] = True
                        switched = active[action_values == 1]
                        routes[switched] = route_decision.route_index
                        feature_rows.append(features)
                        prior_rows.append(prior)
                        action_rows.append(action_values)
                        actor_weight_rows.append(actor_weights)
                        log_probability_rows.append(
                            selected_log_probabilities.cpu()
                            .numpy()
                            .astype(np.float32, copy=False)
                        )
                        value_rows.append(
                            values.cpu().numpy().astype(np.float32, copy=False)
                        )
                        episode_rows.append(active)
                        decision_rows.append(
                            np.full(active.size, decision_index, dtype=np.int64)
                        )
                        candidate_rows.append(
                            np.full(
                                active.size,
                                route_decision.route_index,
                                dtype=np.int64,
                            )
                        )
                        actor_seconds += time.perf_counter() - actor_started

                self._backend.kaito_v48_route_action_numeric_batch(
                    engines,
                    players,
                    sessions,
                    routes,
                    tokens,
                    quantities,
                    decision_counts,
                    unit_counts,
                    min(self._cpu_workers, len(jobs)),
                )
                done = step_native_opponent_batch(
                    self._backend,
                    engines,
                    players,
                    opponent_ids,
                    opponent_sessions,
                    tokens,
                    quantities,
                    decision_counts,
                    unit_counts,
                    self._cpu_workers,
                )
                primitive_turns += len(jobs)
        finally:
            self._model.train(previous_training)

        terminal_cash = np.asarray(
            [engine.money(int(player)) for engine, player in zip(engines, players, strict=True)],
            dtype=np.float64,
        )
        opponent_cash = np.asarray(
            [
                engine.money(1 - int(player))
                for engine, player in zip(engines, players, strict=True)
            ],
            dtype=np.float64,
        )
        outcomes = np.sign(terminal_cash - opponent_cash).astype(np.int64, copy=False)
        control = collect_paired_direct_control(
            self._backend,
            self._environment,
            jobs,
            maximum_market_orders=self._maximum_market_orders,
            cpu_workers=self._cpu_workers,
        )
        direct_outcomes = control.outcomes.astype(np.int64, copy=False)
        rewards = (outcomes - direct_outcomes).astype(np.float32, copy=False)
        games = tuple(
            RouteGameResult(
                seed=int(seed),
                seat=int(seat),
                opponent_id=opponent,
                outcome=int(outcomes[index]),
                direct_outcome=int(direct_outcomes[index]),
                terminal_cash=float(terminal_cash[index]),
                opponent_cash=float(opponent_cash[index]),
                direct_terminal_cash=float(control.terminal_cash[index]),
                direct_opponent_cash=float(control.opponent_cash[index]),
                selected_route=int(routes[index]),
            )
            for index, (seed, seat, opponent) in enumerate(jobs)
        )
        batch = RouteRolloutBatch(
            features=np.concatenate(feature_rows),
            prior_actions=np.concatenate(prior_rows),
            actions=np.concatenate(action_rows),
            actor_weights=np.concatenate(actor_weight_rows),
            old_log_probabilities=np.concatenate(log_probability_rows),
            old_values=np.concatenate(value_rows),
            episode_indices=np.concatenate(episode_rows),
            decision_indices=np.concatenate(decision_rows),
            candidate_routes=np.concatenate(candidate_rows),
            game_rewards=rewards,
            games=games,
            diagnostics={
                "elapsed_seconds": time.perf_counter() - started,
                "actor_seconds": actor_seconds,
                "candidate_primitive_turns": primitive_turns,
                "control_primitive_turns": control.primitive_turns,
                "control_elapsed_seconds": control.elapsed_seconds,
            },
        )
        batch.validate()
        return batch


__all__ = [
    "RouteGameResult",
    "RouteJob",
    "RouteRolloutBatch",
    "RouteRolloutCollector",
]
