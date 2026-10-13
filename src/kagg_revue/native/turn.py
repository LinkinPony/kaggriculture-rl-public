"""Prefix shadow-state compilation for one player's unit phase."""

from typing import Any

from kagg_revue.native._revue_native import (
    compile_market_from_post_unit,
    compile_unit_prefix_from_obs,
)

TURN_COMPILER_SPEC_VERSION = 1


def compile_unit_prefix(
    observation: dict[str, Any],
    configuration: dict[str, Any] | None,
    requested_action: dict[str, Any],
) -> dict[str, Any]:
    """Return the actual unit action, post-unit state, and execution trace."""
    return compile_unit_prefix_from_obs(observation, configuration, requested_action)


def compile_market(
    observation: dict[str, Any],
    configuration: dict[str, Any] | None,
    post_unit: dict[str, Any],
    requested_market: Any,
) -> dict[str, Any]:
    """Return an executable ordered market queue and its exact transition."""
    return compile_market_from_post_unit(observation, configuration, post_unit, requested_market)


def compile_turn(
    observation: dict[str, Any],
    configuration: dict[str, Any] | None,
    requested_action: dict[str, Any],
) -> dict[str, Any]:
    """Compile unit and market phases into one executable official action."""
    unit_result = compile_unit_prefix(observation, configuration, requested_action)
    market_result = compile_market(
        observation,
        configuration,
        unit_result["post_unit"],
        requested_action.get("market", []),
    )
    action = dict(unit_result["action"])
    action["market"] = market_result["market"]
    return {
        "spec_version": TURN_COMPILER_SPEC_VERSION,
        "action": action,
        "post_unit": unit_result["post_unit"],
        "post_market": market_result["post_market"],
        "trace": {
            "unit": unit_result["trace"],
            "market": market_result["trace"],
        },
        "opponent_scenario": market_result["opponent_scenario"],
        "truncated_orders": market_result["truncated_orders"],
    }


__all__ = ["compile_market", "compile_turn", "compile_unit_prefix"]
