"""A bounded, authenticated host-memory cache of the active historical population."""

import json
from collections import OrderedDict
from typing import Any

import torch

from kagg_revue.learning.config import Experiment
from kagg_revue.learning.matchmaking.imports import layout_from_payload
from kagg_revue.policy.grounded.typed import TypedGroundedPolicy
from kagg_revue.policy.inference import ActorRuntime
from kagg_revue.policy.memory.compilation import compile_actor
from kagg_revue.policy.spatial.model import Policy


class PopulationCache:
    """Keep immutable own-run model tensors in RAM, without loading optimizer state on GPU."""

    def __init__(self, config: Experiment, state: dict[str, Any]) -> None:
        """Bind cache entries to the authoritative checkpoint hashes."""
        self.config = config
        self.state = state
        self.entries: OrderedDict[str, dict[str, Any]] = OrderedDict()
        self.loaded: str | None = None
        self.runtimes: dict[str, tuple[ActorRuntime, str]] = {}

    def load(self, name: str, target: Policy) -> None:
        """Authenticate once per immutable hash and reuse the bounded CPU tensor copy."""
        identity = self.state["members"][name]
        if identity == self.loaded:
            return
        payload = self._payload(name)
        if target.layout != layout_from_payload(payload):
            raise ValueError("historical cache target has different checkpoint semantics")
        target.load_state_dict(payload["model"])
        self.loaded = identity

    def _payload(self, name: str) -> dict[str, Any]:
        from kagg_revue.learning.state import member_path

        identity = self.state["members"][name]
        if identity not in self.entries:
            payload = torch.load(
                member_path(self.config, self.state, name), map_location="cpu", weights_only=False
            )
            external = self.state.get("external_opponents", {}).get(name)
            expected_run = external["run_id"] if external else self.state["run_id"]
            if payload.get("lineage", {}).get("run_id") != expected_run:
                raise ValueError("historical policy belongs to a different random root")
            if external and (
                external["sha256"] != identity or external["role"] != "frozen_opponent_only"
            ):
                raise ValueError("external history differs from its frozen registration")
            self.entries[identity] = {"model": payload["model"], "layout": payload["layout"]}
            while len(self.entries) > self.config.population.capacity:
                self.entries.popitem(last=False)
        self.entries.move_to_end(identity)
        return self.entries[identity]

    def runtime(
        self, name: str, device: torch.device, count: int, *, slot: int = 0
    ) -> ActorRuntime:
        """Reuse one frozen graph per vocabulary and authenticated weight identity."""
        payload = self._payload(name)
        identity = self.state["members"][name]
        key = json.dumps([payload["layout"], count, slot], sort_keys=True)
        if key not in self.runtimes:
            policy = Policy.from_layout(layout_from_payload(payload)).to(device)
            policy.load_state_dict(payload["model"])
            policy.requires_grad_(False)
            if (
                self.config.compile
                and device.type == "cuda"
                and isinstance(policy, TypedGroundedPolicy)
            ):
                compile_actor(policy)
            runtime = ActorRuntime(
                policy,
                count,
                sample=True,
                precision=self.config.precision,
                bf16_reduced_precision_reduction=False,
                compile_inference=bool(
                    self.config.execution and self.config.execution.compile_inference
                ),
            )
            self.runtimes[key] = (runtime, identity)
        runtime, loaded = self.runtimes[key]
        if loaded != identity:
            runtime.policy.load_state_dict(payload["model"])
            self.runtimes[key] = (runtime, identity)
        return runtime
