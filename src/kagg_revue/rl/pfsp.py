"""Historical policy sampling from direct complete-match outcomes."""

from __future__ import annotations

import random
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from hashlib import sha256
from typing import cast

import torch
from torch import Tensor, nn

from kagg_revue.policy.state import causal_actor_state
from kagg_revue.rl.data import Trajectory


def actor_fingerprint(actor: nn.Module) -> str:
    """Hash tensor names, types, shapes and values independent of containers."""
    digest = sha256()
    for key, value in sorted(actor.state_dict().items()):
        tensor = value.detach().cpu().contiguous()
        digest.update(key.encode("utf-8"))
        digest.update(str(tensor.dtype).encode("ascii"))
        digest.update(str(tuple(tensor.shape)).encode("ascii"))
        digest.update(tensor.reshape(-1).view(torch.uint8).numpy().tobytes())
    return digest.hexdigest()


@dataclass(eq=False)
class HistoricalPolicy:
    """One immutable actor snapshot and its candidate-relative match record."""

    identity: str
    source: dict[str, object]
    actor_state: dict[str, Tensor]
    wins: int = 0
    ties: int = 0
    losses: int = 0

    @property
    def games(self) -> int:
        """Return the number of direct official matches against this snapshot."""
        return self.wins + self.ties + self.losses

    @property
    def win_probability(self) -> float:
        """Return a smoothed candidate score with ties worth one half."""
        return (self.wins + 0.5 * self.ties + 1.0) / (self.games + 2.0)

    @property
    def priority(self) -> float:
        """Prioritize informative opponents near an even direct match."""
        probability = self.win_probability
        return probability * (1.0 - probability)

    def record(self, trajectories: Sequence[Trajectory]) -> None:
        """Accumulate candidate-relative W/D/L observations."""
        self.wins += sum(trajectory.outcome > 0 for trajectory in trajectories)
        self.ties += sum(trajectory.outcome == 0 for trajectory in trajectories)
        self.losses += sum(trajectory.outcome < 0 for trajectory in trajectories)

    def summary(self) -> dict[str, object]:
        """Return a serialization-safe identity and direct outcome record."""
        return {
            "identity": self.identity,
            "source": self.source,
            "games": self.games,
            "wins": self.wins,
            "ties": self.ties,
            "losses": self.losses,
            "win_probability": self.win_probability,
            "pfsp_priority": self.priority,
        }


class HistoricalPfsp:
    """Keep a bounded actor lineage and sample one dense GPU opponent per update."""

    def __init__(
        self,
        capacity: int,
        self_play_probability: float,
        seed: int,
    ) -> None:
        """Create an independently seeded, bounded history pool."""
        if capacity < 1:
            raise ValueError("PFSP history capacity must be positive")
        if not 0.0 <= self_play_probability <= 1.0:
            raise ValueError("PFSP self-play probability must lie in [0, 1]")
        self._capacity = capacity
        self._self_play_probability = self_play_probability
        self._random = random.Random(seed)
        self._policies: list[HistoricalPolicy] = []

    @property
    def size(self) -> int:
        """Return the current number of retained actor snapshots."""
        return len(self._policies)

    @staticmethod
    def _snapshot(actor: nn.Module) -> dict[str, Tensor]:
        return {key: value.detach().cpu().clone() for key, value in actor.state_dict().items()}

    def add(
        self,
        identity: str,
        source: Mapping[str, object],
        actor: nn.Module,
    ) -> None:
        """Freeze one actor once, evicting the oldest excess snapshot."""
        self.add_state(identity, source, actor.state_dict())

    def add_state(
        self,
        identity: str,
        source: Mapping[str, object],
        actor_state: Mapping[str, Tensor],
    ) -> None:
        """Freeze an explicit actor state once, evicting the oldest snapshot."""
        if any(policy.identity == identity for policy in self._policies):
            return
        normalized, _ = causal_actor_state(actor_state)
        self._policies.append(
            HistoricalPolicy(
                identity=identity,
                source=dict(source),
                actor_state={
                    key: value.detach().cpu().clone() for key, value in normalized.items()
                },
            )
        )
        if len(self._policies) > self._capacity:
            del self._policies[0]

    def select(self, current_identity: str) -> HistoricalPolicy | None:
        """Choose self-play or one non-current historical actor by PFSP weight."""
        eligible = [policy for policy in self._policies if policy.identity != current_identity]
        if not eligible or self._random.random() < self._self_play_probability:
            return None
        return self._random.choices(
            eligible,
            weights=[policy.priority for policy in eligible],
            k=1,
        )[0]

    def record(self, policy: HistoricalPolicy, trajectories: Sequence[Trajectory]) -> None:
        """Bind results only to the exact sampled snapshot."""
        if not any(candidate is policy for candidate in self._policies):
            raise ValueError("PFSP result references an actor outside the history pool")
        policy.record(trajectories)

    def state_dict(self) -> dict[str, object]:
        """Return the complete bounded population and its sampler state."""
        return {
            "state_version": "historical-pfsp-v1",
            "capacity": self._capacity,
            "self_play_probability": self._self_play_probability,
            "random_state": self._random.getstate(),
            "policies": [
                {
                    "identity": policy.identity,
                    "source": dict(policy.source),
                    "actor_state": {
                        key: value.detach().cpu().clone()
                        for key, value in policy.actor_state.items()
                    },
                    "wins": policy.wins,
                    "ties": policy.ties,
                    "losses": policy.losses,
                }
                for policy in self._policies
            ],
        }

    def load_state_dict(self, state: Mapping[str, object]) -> None:
        """Restore a validated population without retaining payload aliases."""
        if state.get("state_version") != "historical-pfsp-v1":
            raise ValueError("PFSP checkpoint state version is unsupported")
        if state.get("capacity") != self._capacity:
            raise ValueError("PFSP checkpoint capacity differs from the resolved profile")
        if state.get("self_play_probability") != self._self_play_probability:
            raise ValueError("PFSP checkpoint sampling probability differs")
        random_state = state.get("random_state")
        if not isinstance(random_state, tuple):
            raise ValueError("PFSP checkpoint lacks its random state")
        raw_policies = state.get("policies")
        if not isinstance(raw_policies, list) or len(raw_policies) > self._capacity:
            raise ValueError("PFSP checkpoint has an invalid bounded population")

        policies: list[HistoricalPolicy] = []
        identities: set[str] = set()
        for raw_policy in raw_policies:
            if not isinstance(raw_policy, Mapping):
                raise ValueError("PFSP checkpoint policy is not a mapping")
            identity = raw_policy.get("identity")
            source = raw_policy.get("source")
            actor_state = raw_policy.get("actor_state")
            if not isinstance(identity, str) or not identity or identity in identities:
                raise ValueError("PFSP checkpoint policy identity is invalid")
            if not isinstance(source, Mapping) or not isinstance(actor_state, Mapping):
                raise ValueError("PFSP checkpoint policy payload is incomplete")
            normalized, _ = causal_actor_state(actor_state)
            tensors = {
                key: value.detach().cpu().clone() for key, value in normalized.items()
            }
            counts: list[int] = []
            for name in ("wins", "ties", "losses"):
                value = raw_policy.get(name)
                if not isinstance(value, int) or isinstance(value, bool) or value < 0:
                    raise ValueError(f"PFSP checkpoint {name} count is invalid")
                counts.append(value)
            identities.add(identity)
            policies.append(
                HistoricalPolicy(
                    identity=identity,
                    source=dict(cast(Mapping[str, object], source)),
                    actor_state=tensors,
                    wins=counts[0],
                    ties=counts[1],
                    losses=counts[2],
                )
            )

        sampler = random.Random()
        try:
            sampler.setstate(random_state)
        except (TypeError, ValueError) as error:
            raise ValueError("PFSP checkpoint random state is invalid") from error
        self._random = sampler
        self._policies = policies

    def report(self) -> dict[str, object]:
        """Return the current reproducible pool state without tensor payloads."""
        return {
            "kind": "historical_pfsp",
            "self_play_probability": self._self_play_probability,
            "capacity": self._capacity,
            "policies": [policy.summary() for policy in self._policies],
        }


__all__ = ["HistoricalPfsp", "HistoricalPolicy", "actor_fingerprint"]
