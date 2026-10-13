"""Bounded same-lineage opponent snapshots for pure plan self-play."""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from hashlib import sha256
from typing import cast

import torch
from torch import Tensor

from kagg_revue.policy.plans.model import (
    StructuredPlanArchitecture,
    StructuredPlanPolicy,
)

PLAN_POPULATION_VERSION = "structured-plan-self-play-population-v3"


def _cpu_state(model: StructuredPlanPolicy) -> dict[str, Tensor]:
    """Clone a policy into immutable CPU checkpoint storage."""
    return {
        name: value.detach().cpu().clone()
        for name, value in model.state_dict().items()
    }


def _state_fingerprint(
    architecture: StructuredPlanArchitecture,
    state: Mapping[str, Tensor],
) -> str:
    """Hash exact policy tensors independently of their container."""
    digest = sha256()
    digest.update(
        json.dumps(
            architecture.payload(),
            sort_keys=True,
            separators=(",", ":"),
        ).encode("ascii")
    )
    for name, value in sorted(state.items()):
        tensor = value.detach().cpu().contiguous()
        digest.update(name.encode("utf-8"))
        digest.update(str(tensor.dtype).encode("ascii"))
        digest.update(str(tuple(tensor.shape)).encode("ascii"))
        digest.update(tensor.reshape(-1).view(torch.uint8).numpy().tobytes())
    return digest.hexdigest()


@dataclass(frozen=True, eq=False)
class PlanOpponentEvaluation:
    """Most recent direct W/D/L panel against one frozen snapshot."""

    update: int
    wins: int
    ties: int
    losses: int

    def __post_init__(self) -> None:
        """Reject malformed direct-match records at their construction boundary."""
        fields = (self.update, self.wins, self.ties, self.losses)
        if any(not isinstance(value, int) or isinstance(value, bool) for value in fields):
            raise ValueError("structured-plan history evaluation counts are invalid")
        if self.update < 1 or min(self.wins, self.ties, self.losses) < 0:
            raise ValueError("structured-plan history evaluation counts are invalid")
        if self.games < 1:
            raise ValueError("structured-plan history evaluation must contain games")

    @property
    def games(self) -> int:
        """Return the number of complete official-rule matches."""
        return self.wins + self.ties + self.losses

    @property
    def wdl_variance(self) -> float:
        """Measure non-constant direct outcome information in [-1, 0, 1]."""
        games = self.games
        decisive = (self.wins + self.losses) / games
        mean = (self.wins - self.losses) / games
        return decisive - mean * mean

    def payload(self) -> dict[str, int]:
        """Return the checkpoint representation without derived fields."""
        return {
            "update": self.update,
            "wins": self.wins,
            "ties": self.ties,
            "losses": self.losses,
        }

    def summary(self) -> dict[str, int | float]:
        """Return direct outcomes and their selection information."""
        return {
            **self.payload(),
            "games": self.games,
            "wdl_variance": self.wdl_variance,
        }


@dataclass(frozen=True, eq=False)
class PlanHistoricalSnapshot:
    """One immutable policy artifact retained from this training lineage."""

    update: int
    identity: str
    model_state: dict[str, Tensor]
    evaluation: PlanOpponentEvaluation | None = None

    def summary(self) -> dict[str, object]:
        """Return tensor-free provenance for metrics and run reports."""
        return {
            "update": self.update,
            "identity": self.identity,
            "evaluation": (
                None if self.evaluation is None else self.evaluation.summary()
            ),
        }


class PlanSelfPlayPopulation:
    """Retain CPU snapshots and install one selected opponent on the GPU."""

    def __init__(
        self,
        architecture: StructuredPlanArchitecture,
        *,
        capacity: int,
        snapshot_interval: int,
        selection_seed: int,
        device: torch.device,
    ) -> None:
        """Create an independently selected, bounded same-lineage population."""
        if capacity < 1:
            raise ValueError("structured-plan history capacity must be positive")
        if snapshot_interval < 1:
            raise ValueError("structured-plan snapshot interval must be positive")
        if selection_seed < 0:
            raise ValueError("structured-plan population seed must be non-negative")
        self._architecture = architecture
        self._capacity = capacity
        self._snapshot_interval = snapshot_interval
        self._selection_seed = selection_seed
        self._device = device
        self._snapshots: list[PlanHistoricalSnapshot] = []
        self._resident = StructuredPlanPolicy(architecture).to(device)
        self._resident.eval()
        self._resident.requires_grad_(False)
        self._resident_identity: str | None = None

    @property
    def size(self) -> int:
        """Return the number of retained frozen opponents."""
        return len(self._snapshots)

    @property
    def identities(self) -> tuple[str, ...]:
        """Return retained artifact identities from oldest to newest."""
        return tuple(snapshot.identity for snapshot in self._snapshots)

    def _identity(self, update: int, state: Mapping[str, Tensor]) -> str:
        fingerprint = _state_fingerprint(self._architecture, state)
        return f"history:u{update:08d}:{fingerprint}"

    def snapshot(
        self,
        update: int,
        model: StructuredPlanPolicy,
        *,
        force: bool = False,
    ) -> bool:
        """Freeze a due update and retain only the newest bounded history."""
        if model.architecture != self._architecture:
            raise ValueError("structured-plan history architecture differs")
        if update < 0:
            raise ValueError("structured-plan history update must be non-negative")
        if not force and update % self._snapshot_interval:
            return False
        if self._snapshots and update <= self._snapshots[-1].update:
            if update == self._snapshots[-1].update:
                return False
            raise ValueError("structured-plan history updates must increase")
        state = _cpu_state(model)
        self._snapshots.append(
            PlanHistoricalSnapshot(
                update=update,
                identity=self._identity(update, state),
                model_state=state,
            )
        )
        if len(self._snapshots) > self._capacity:
            del self._snapshots[0]
        return True

    def select(self, update: int) -> PlanHistoricalSnapshot:
        """Select unseen or least-recently matched direct-W/D/L history."""
        if not self._snapshots:
            raise RuntimeError("structured-plan history has no initial snapshot")
        unseen = [
            snapshot for snapshot in self._snapshots if snapshot.evaluation is None
        ]
        if unseen:
            return min(unseen, key=lambda snapshot: snapshot.update)

        digest = sha256()
        digest.update(str(self._selection_seed).encode("ascii"))
        digest.update(b":")
        digest.update(str(update).encode("ascii"))
        for snapshot in self._snapshots:
            digest.update(b":")
            digest.update(snapshot.identity.encode("ascii"))
        rotation = int.from_bytes(digest.digest()[:8], "big") % len(self._snapshots)
        order = {
            snapshot.identity: (index - rotation) % len(self._snapshots)
            for index, snapshot in enumerate(self._snapshots)
        }
        return min(
            self._snapshots,
            key=lambda snapshot: (
                cast(PlanOpponentEvaluation, snapshot.evaluation).update,
                -cast(PlanOpponentEvaluation, snapshot.evaluation).wdl_variance,
                order[snapshot.identity],
            ),
        )

    def record_outcomes(
        self,
        identity: str,
        update: int,
        outcomes: Sequence[int],
    ) -> PlanOpponentEvaluation:
        """Replace one snapshot's matchup record with the latest direct panel."""
        if update < 1 or not outcomes:
            raise ValueError("structured-plan history evaluation must be nonempty")
        if any(outcome not in (-1, 0, 1) for outcome in outcomes):
            raise ValueError("structured-plan history outcomes must be W/D/L")
        matches = [
            index
            for index, snapshot in enumerate(self._snapshots)
            if snapshot.identity == identity
        ]
        if len(matches) != 1:
            raise ValueError("structured-plan evaluated history identity is unknown")
        evaluation = PlanOpponentEvaluation(
            update=update,
            wins=sum(outcome > 0 for outcome in outcomes),
            ties=sum(outcome == 0 for outcome in outcomes),
            losses=sum(outcome < 0 for outcome in outcomes),
        )
        index = matches[0]
        snapshot = self._snapshots[index]
        if update <= snapshot.update or (
            snapshot.evaluation is not None
            and update <= snapshot.evaluation.update
        ):
            raise ValueError("structured-plan history evaluation updates must increase")
        self._snapshots[index] = PlanHistoricalSnapshot(
            update=snapshot.update,
            identity=snapshot.identity,
            model_state=snapshot.model_state,
            evaluation=evaluation,
        )
        return evaluation

    def policy(self, snapshot: PlanHistoricalSnapshot) -> StructuredPlanPolicy:
        """Install a selected immutable state into the resident inference model."""
        if not any(candidate is snapshot for candidate in self._snapshots):
            raise ValueError("structured-plan opponent is outside the retained history")
        if snapshot.identity != self._resident_identity:
            pointers = tuple(parameter.data_ptr() for parameter in self._resident.parameters())
            self._resident.load_state_dict(snapshot.model_state, strict=True)
            if tuple(parameter.data_ptr() for parameter in self._resident.parameters()) != pointers:
                raise RuntimeError("structured-plan history load replaced resident storage")
            self._resident_identity = snapshot.identity
        self._resident.eval()
        return self._resident

    def state_dict(self) -> dict[str, object]:
        """Return the complete bounded population for an update checkpoint."""
        return {
            "state_version": PLAN_POPULATION_VERSION,
            "capacity": self._capacity,
            "snapshot_interval": self._snapshot_interval,
            "selection_seed": self._selection_seed,
            "snapshots": [
                {
                    "update": snapshot.update,
                    "identity": snapshot.identity,
                    "model_state": {
                        name: value.detach().cpu().clone()
                        for name, value in snapshot.model_state.items()
                    },
                    "evaluation": (
                        None
                        if snapshot.evaluation is None
                        else snapshot.evaluation.payload()
                    ),
                }
                for snapshot in self._snapshots
            ],
        }

    def _validated_state(self, value: object) -> dict[str, Tensor]:
        expected = self._resident.state_dict()
        if not isinstance(value, Mapping) or any(
            not isinstance(name, str) or not isinstance(tensor, Tensor)
            for name, tensor in value.items()
        ):
            raise ValueError("structured-plan history model state is invalid")
        state = cast(dict[str, Tensor], dict(value))
        if set(state) != set(expected):
            raise ValueError("structured-plan history parameter names differ")
        result: dict[str, Tensor] = {}
        for name, tensor in expected.items():
            candidate = state[name]
            if candidate.shape != tensor.shape or candidate.dtype != tensor.dtype:
                raise ValueError(f"structured-plan history tensor differs: {name}")
            result[name] = candidate.detach().cpu().clone()
        return result

    def load_state_dict(
        self,
        value: object,
        *,
        completed_update: int,
    ) -> None:
        """Authenticate and restore retained artifacts without payload aliases."""
        expected_keys = {
            "state_version",
            "capacity",
            "snapshot_interval",
            "selection_seed",
            "snapshots",
        }
        if not isinstance(value, Mapping) or set(value) != expected_keys:
            raise ValueError("structured-plan population checkpoint is incomplete")
        if (
            value.get("state_version") != PLAN_POPULATION_VERSION
            or value.get("capacity") != self._capacity
            or value.get("snapshot_interval") != self._snapshot_interval
            or value.get("selection_seed") != self._selection_seed
        ):
            raise ValueError("structured-plan population checkpoint contract differs")
        raw_snapshots = value.get("snapshots")
        if (
            not isinstance(raw_snapshots, list)
            or not raw_snapshots
            or len(raw_snapshots) > self._capacity
        ):
            raise ValueError("structured-plan population checkpoint is not bounded")

        snapshots: list[PlanHistoricalSnapshot] = []
        previous_update = -1
        for raw_snapshot in raw_snapshots:
            if not isinstance(raw_snapshot, Mapping) or set(raw_snapshot) != {
                "update",
                "identity",
                "model_state",
                "evaluation",
            }:
                raise ValueError("structured-plan history snapshot is incomplete")
            update = raw_snapshot.get("update")
            identity = raw_snapshot.get("identity")
            if (
                not isinstance(update, int)
                or isinstance(update, bool)
                or update <= previous_update
                or update > completed_update
                or (update != 0 and update % self._snapshot_interval)
            ):
                raise ValueError("structured-plan history snapshot update is invalid")
            state = self._validated_state(raw_snapshot.get("model_state"))
            if not isinstance(identity, str) or identity != self._identity(update, state):
                raise ValueError("structured-plan history snapshot identity differs")
            raw_evaluation = raw_snapshot.get("evaluation")
            evaluation: PlanOpponentEvaluation | None = None
            if raw_evaluation is not None:
                evaluation = self._validated_evaluation(
                    raw_evaluation,
                    completed_update=completed_update,
                    snapshot_update=update,
                )
            snapshots.append(
                PlanHistoricalSnapshot(update, identity, state, evaluation)
            )
            previous_update = update
        self._snapshots = snapshots
        self._resident_identity = None

    def report(
        self,
        selected: PlanHistoricalSnapshot | None = None,
    ) -> dict[str, object]:
        """Return tensor-free population and selected-opponent identities."""
        return {
            "kind": "direct-wdl-matched-same-lineage-history",
            "capacity": self._capacity,
            "snapshot_interval": self._snapshot_interval,
            "selected": None if selected is None else selected.summary(),
            "snapshots": [snapshot.summary() for snapshot in self._snapshots],
        }

    @staticmethod
    def _validated_evaluation(
        value: object,
        *,
        completed_update: int,
        snapshot_update: int,
    ) -> PlanOpponentEvaluation:
        if not isinstance(value, Mapping) or set(value) != {
            "update",
            "wins",
            "ties",
            "losses",
        }:
            raise ValueError("structured-plan history evaluation is incomplete")
        fields = tuple(value.get(name) for name in ("update", "wins", "ties", "losses"))
        if any(not isinstance(field, int) or isinstance(field, bool) for field in fields):
            raise ValueError("structured-plan history evaluation counts are invalid")
        update, wins, ties, losses = cast(tuple[int, int, int, int], fields)
        if update <= snapshot_update or update > completed_update:
            raise ValueError("structured-plan history evaluation lies outside the run")
        evaluation = PlanOpponentEvaluation(update, wins, ties, losses)
        return evaluation


__all__ = [
    "PLAN_POPULATION_VERSION",
    "PlanHistoricalSnapshot",
    "PlanOpponentEvaluation",
    "PlanSelfPlayPopulation",
]
