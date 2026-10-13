"""Fresh experimental wrappers that retain exact public-source provenance."""

from pathlib import Path
from types import FunctionType
from typing import Any, cast

from kagg_revue.opponents.public import PublicAgentRecord, PublicAgentRuntime
from kagg_revue.opponents.research.market import apply_market
from kagg_revue.opponents.research.settings import Variant


class ResearchRuntime:
    """Own one isolated source namespace and optional research interventions."""

    def __init__(
        self,
        record: PublicAgentRecord,
        configuration: dict[str, Any],
        variant: Variant,
    ) -> None:
        """Authenticate the original source before changing explicit experiment knobs."""
        self.base = PublicAgentRuntime(record, Path.cwd(), configuration)
        self.variant = variant
        self.namespace = cast(FunctionType, self.base._function).__globals__
        self.counters: dict[str, int] = {}
        for name, value in variant.globals.items():
            if name not in self.namespace or not isinstance(
                self.namespace[name], (bool, int, float)
            ):
                raise ValueError(f"unknown scalar strategy setting: {name}")
            self.namespace[name] = value
        if variant.opening is not None:
            if "_R42_OPENING" not in self.namespace:
                raise ValueError("source does not expose the supported opening")
            first, second, sale = variant.opening
            self.namespace["_R42_OPENING"] = [
                ["BUY_PRODUCT", "WHEAT", first],
                ["BUY_PRODUCT", "WHEAT", second],
                ["SELL", "WHEAT", sale],
            ]
            # The public module consumes this constant while initializing routes.
            # Update the episode-local routes, not only the now-unused constant.
            for tape in self.namespace["_IMPL"].chassis.routes.values():
                tape[0] = dict(tape[0], market=[list(o) for o in self.namespace["_R42_OPENING"]])

    def act(self, observation: dict[str, Any]) -> dict[str, Any]:
        """Compute the frozen action and apply the declared experimental controller."""
        action = self.base.act(observation)
        return apply_market(observation, action, self.namespace, self.variant, self.counters)
