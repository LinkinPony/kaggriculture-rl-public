from kagg_revue.bc.actions import ReplayActionEncoder
from kagg_revue.bc.replay import _canonicalize_observable_sell_quantities
from kagg_revue.native import _revue_native as native
from kagg_revue.native.engine import Engine


def _encoder() -> ReplayActionEncoder:
    keys = [
        "UNIT:PASS",
        "UNIT:NORTH",
        "UNIT:SOUTH",
        "UNIT:EAST",
        "UNIT:WEST",
        "UNIT:PICKUP_DEFAULT:WHEAT",
        "UNIT:PICKUP:WHEAT",
        "UNIT:FEED",
        "MARKET:STOP",
        "MARKET:SKIP_SLOT",
        "MARKET:SELL:WHEAT",
        "MARKET:HIRE",
    ]
    return ReplayActionEncoder(
        {
            "keys": keys,
            "unit_tokens": 8,
            "market_stop_token": 8,
        }
    )


def test_replay_action_encoding_fills_units_and_terminates_market() -> None:
    encoded = _encoder().encode(
        {
            "farmer": ["PICKUP", "WHEAT", 3],
            "hands": [["NORTH"]],
            "market": [[], ["SELL", "WHEAT", 2]],
        },
        unit_count=3,
        max_market_orders=3,
    )

    assert encoded.tokens == (6, 1, 0, 9, 10, 8)
    assert encoded.quantities == (3, 0, 0, 0, 2, 0)
    assert encoded.unit_decisions == 3
    assert encoded.market_orders == 2
    assert encoded.repairs == {"missing_hand_passes": 1}


def test_full_market_uses_capacity_instead_of_extra_stop_token() -> None:
    encoded = _encoder().encode(
        {"farmer": ["PASS"], "market": [["HIRE"], ["HIRE"]]},
        unit_count=1,
        max_market_orders=2,
    )

    assert encoded.tokens == (0, 11, 11)
    assert 8 not in encoded.tokens


def test_official_noops_and_ignored_arguments_are_canonicalized() -> None:
    encoded = _encoder().encode(
        {
            "farmer": ["FEED", "WHEAT"],
            "market": [["SELL", "WHEAT", 0]],
        },
        unit_count=1,
        max_market_orders=2,
    )

    assert encoded.tokens == (7, 9, 8)
    assert encoded.quantities == (0, 0, 0)
    assert encoded.repairs == {
        "extra_unit_arguments_dropped": 1,
        "invalid_market_requests_to_skip": 1,
    }


def test_sell_requests_use_observable_stock_instead_of_sentinels() -> None:
    engine = Engine(7)
    observation = engine.observation(0)
    observation["private"]["shed"]["WHEAT"] = 3
    codec = ReplayActionEncoder(native.action_codec_spec())
    encoded = codec.encode(
        {
            "farmer": ["PASS"],
            "market": [
                ["SELL", "WHEAT", 999],
                ["SELL", "CARROT", 999],
            ],
        },
        unit_count=1,
        max_market_orders=2,
    )

    canonical = _canonicalize_observable_sell_quantities(
        encoded,
        observation,
        engine.configuration,
        codec,
    )

    assert tuple(codec.keys[token] for token in canonical.tokens) == (
        "UNIT:PASS",
        "MARKET:SELL:WHEAT",
        "MARKET:SKIP_SLOT",
    )
    assert canonical.quantities == (0, 3, 0)
    assert canonical.repairs == {
        "empty_sell_requests_to_skip": 1,
        "sell_quantities_capped_to_observable_stock": 1,
    }
