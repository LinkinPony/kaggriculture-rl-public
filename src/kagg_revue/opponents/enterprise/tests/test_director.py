"""Rule and logistics regressions for the independently authored controller."""

from typing import Any

from kagg_revue.native import _revue_native as native
from kagg_revue.opponents.enterprise.agent import Director
from kagg_revue.opponents.enterprise.economy import price
from kagg_revue.opponents.enterprise.packaging import source


def test_price_model_matches_rule_engine_on_both_sides_of_equilibrium() -> None:
    """Investment valuation must use the actual nonlinear settlement price curve."""
    engine = native.Engine(1, {})
    for item, parameters in engine.configuration["marketParams"].items():
        for offset in (-1000, -450, -200, -1, 0, 1, 105, 450, 1000):
            inventory = parameters["I0"] + offset
            assert price(parameters, inventory) == engine.market_price(item, inventory)


def test_fertilizer_for_field_work_is_not_immediately_dropped() -> None:
    """A supplied worker at the shed must leave for work instead of cycling inventory."""
    engine = native.Engine(1860917601, {})
    observation = dict(engine.observation(0))
    observation["private"]["inventories"][0]["FERTILIZER"] = 2
    observation["private"]["seeds"]["WHEAT"] = 1
    director = Director(dict(engine.configuration), {"buy_fertilizer": True})
    action = director.act(observation)
    assert action["farmer"][0] not in {"DROP", "PICKUP", "PASS"}


def test_standalone_export_has_identical_live_actions_for_a_complete_season() -> None:
    """Flattening original modules must preserve state, economy and scheduling behavior."""
    engine = native.Engine(1860917602, {})
    settings = {"efficient_transport": True, "crews": False, "territories": False}
    program, hashes = source(settings, dict(engine.configuration))
    assert set(hashes) == {"economy", "tasks", "territories", "finance", "agent"}
    assert "from kagg_revue" not in program
    namespace: dict[str, Any] = {}
    exec(compile(program, "independent-export", "exec"), namespace)  # noqa: S102
    director = Director(dict(engine.configuration), settings)
    for _ in range(719):
        observation = dict(engine.observation(0))
        expected = director.act(observation)
        assert namespace["agent"](observation, dict(engine.configuration)) == expected
        engine.step(expected, {})
    assert engine.done
