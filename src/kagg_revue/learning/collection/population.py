"""Whole-game opponent mixtures over the shared persistent native batches."""

from collections.abc import Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

import numpy as np
from numpy.typing import NDArray

from kagg_revue.learning.collection.frozen import FrozenBatches
from kagg_revue.learning.collection.history import HistoricalBatch
from kagg_revue.learning.matchmaking.imports import validate_layout
from kagg_revue.learning.settings import RuntimeSettings
from kagg_revue.native.batches import create_selfplay_batch
from kagg_revue.policy.contracts import ContractLayout

if TYPE_CHECKING:
    from kagg_revue.policy.inference import ActorRuntime


def script_games(settings: RuntimeSettings, games: int) -> int:
    """Resolve the schema-validated physical-game fraction for one shard."""
    return int(games * settings.ppo.script_fraction)


def historical_games(settings: RuntimeSettings, games: int) -> int:
    """Resolve whole historical games, each with just one trainable trajectory."""
    history = settings.ppo.history
    return int(games * history.fraction) if history is not None else 0


def policy_rows(cash: NDArray[np.float64], selfplay: int) -> NDArray[np.float64]:
    """Keep both mirror seats and only the learned seat against frozen opponents."""
    return np.concatenate((cash[:selfplay].reshape(-1), cash[selfplay:, 0]))


def episode_weights(selfplay: int, scripts: int) -> NDArray[np.float32]:
    """Give every physical game equal total mass despite different seat counts."""
    return np.concatenate(
        (np.full(2 * selfplay, 0.5, dtype=np.float32), np.ones(scripts, dtype=np.float32))
    )


@dataclass
class TrainingBatch:
    """Mirror and frozen-opponent populations sharing a contiguous learner handshake."""

    selfplay: Any
    scripts: Any
    selfplay_games: int
    opponents: tuple[str, ...]
    program_capacity: int = 0
    prepare_opponents: Callable[[], None] | None = None

    @property
    def step_index(self) -> int:
        """Require every population component to share one official turn."""
        clocks = {batch.step_index for batch in (self.selfplay, self.scripts) if batch is not None}
        if len(clocks) != 1:
            raise ValueError("training population components have inconsistent clocks")
        return int(clocks.pop())

    @property
    def split(self) -> int:
        """Return the policy-row boundary between the two populations."""
        return 2 * self.selfplay_games

    def observe_into(self, output: NDArray[np.float16]) -> None:
        """Encode native views directly into slices of the pinned input buffer."""
        if self.selfplay is not None:
            self.selfplay.observe_selfplay_into(output[: self.split])
        if self.scripts is not None:
            self.scripts.observe_into(output[self.split :])

    def advance(self, actions: NDArray[np.int64], turns: int) -> None:
        """Execute complete intervals in native code without script Python callbacks."""
        if self.selfplay is not None:
            if self.program_capacity:
                self.selfplay.advance_programs(
                    actions[: self.split], turns, self.program_capacity, True
                )
            else:
                self.selfplay.advance_selfplay(actions[: self.split], turns)
        if self.scripts is not None:
            if self.program_capacity:
                self.scripts.advance_programs(actions[self.split :], turns, self.program_capacity)
            else:
                self.scripts.advance(actions[self.split :], turns)

    def cash(self, turns: int) -> NDArray[np.float64]:
        """Seal completed physical games with learned-seat-first script outcomes."""
        batches = [batch for batch in (self.selfplay, self.scripts) if batch is not None]
        games = len(self.opponents)
        if (
            sum(batch.completed_games for batch in batches) != games
            or sum(batch.transitions for batch in batches) != games * turns
        ):
            raise RuntimeError("rollout did not finish every official-rule physical game")
        return np.concatenate([batch.cash() for batch in batches])


def create_training_batch(
    settings: RuntimeSettings, seeds: list[int], history_runtime: "ActorRuntime | None" = None
) -> TrainingBatch:
    """Balance frozen opponents and seats while preserving unique training seeds."""
    scripts = script_games(settings, len(seeds))
    history = historical_games(settings, len(seeds))
    selfplay = len(seeds) - scripts - history
    pool = settings.ppo.script_opponents
    jobs = [
        (seed, index % 2, pool[(index // 2) % len(pool)])
        for index, seed in enumerate(seeds[selfplay : selfplay + scripts])
    ]
    if allocation := settings.ppo.script_allocation:
        if (
            {name for name, _ in allocation} != set(pool)
            or len(allocation) != len(pool)
            or sum(count for _, count in allocation) != scripts
            or any(count <= 0 or count % 2 for _, count in allocation)
        ):
            raise ValueError("script allocation must balance every declared opponent and seat")
        names = [name for name, count in allocation for _ in range(count)]
        jobs = [
            (seed, index % 2, name)
            for index, (seed, name) in enumerate(
                zip(seeds[selfplay : selfplay + scripts], names, strict=True)
            )
        ]
    historical = None
    if history:
        if history_runtime is None:
            raise ValueError("historical self-play requires its frozen actor runtime")
        learner_layout = ContractLayout.resolve(settings)
        frozen_layout = history_runtime.policy.layout
        validate_layout(learner_layout, frozen_layout)
        quantities = frozen_layout.observation.quantities
        quantity_maps = None
        native_settings = settings
        if quantities != settings.quantities:
            union = tuple(sorted(set(settings.quantities) | set(quantities)))
            native_settings = settings.model_copy(
                update={"quantity_extra": tuple(q for q in union if q > settings.quantity_max)}
            )
            quantity_maps = (
                np.asarray([union.index(q) for q in settings.quantities], dtype=np.int64),
                np.asarray([union.index(q) for q in quantities], dtype=np.int64),
            )
        historical = HistoricalBatch(
            create_selfplay_batch(native_settings, seeds[selfplay + scripts :]),
            np.arange(history, dtype=np.int64) % 2,
            history_runtime.host.numpy(),
            history_runtime.selected.numpy(),
            quantity_maps,
            learner_layout.work_factors,
            frozen_layout.observation.support_features,
        )
    scripted = None
    if scripts:
        if settings.script_population is not None:
            from kagg_revue.learning.collection.public import create_public_batch

            scripted = create_public_batch(settings, jobs)
        else:
            from kagg_revue.opponents.batches import create_batch

            scripted = create_batch(settings, jobs)
    frozen: Any = scripted if scripts else historical
    if scripts and history:
        frozen = FrozenBatches([(scripted, scripts), (historical, history)])
    return TrainingBatch(
        create_selfplay_batch(settings, seeds[:selfplay]) if selfplay else None,
        frozen,
        selfplay,
        ("self_play",) * selfplay
        + tuple(name for _, _, name in jobs)
        + ("historical_self_play",) * history,
        ContractLayout.resolve(settings).capacity
        if settings.model.architecture in {"work-v1", "grounded-v1", "grounded-v2"}
        else 0,
        getattr(scripted, "prepare_opponents", None) if scripts else None,
    )


def outcomes(cash: NDArray[np.float64], names: list[str]) -> dict[str, Any]:
    """Report direct outcomes separately for self-play and each frozen opponent."""
    labels = np.asarray(names)
    result: dict[str, Any] = {}
    for name in dict.fromkeys(names):
        selected = cash[labels == name]
        difference = selected[:, 0] - selected[:, 1]
        learned = selected.reshape(-1) if name == "self_play" else selected[:, 0]
        result[name] = {
            "games": len(selected),
            "training_fraction": len(selected) / len(cash),
            "training_trajectories": len(learned),
            "wins": int((difference > 0).sum()),
            "ties": int((difference == 0).sum()),
            "losses": int((difference < 0).sum()),
            "mean_terminal_cash": float(learned.mean()),
            "mean_cash_difference": float(difference.mean()),
        }
    return result
