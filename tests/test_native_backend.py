import copy

import numpy as np
import pytest


def test_native_backend_completes_synthetic_episode() -> None:
    native = pytest.importorskip("kagg_revue.native._revue_native")
    engine = native.Engine(seed=3, configuration={"episodeSteps": 4})
    action = {"farmer": ["PASS"], "hands": [], "market": []}
    transitions = 0
    while not engine.done:
        engine.step(action, action)
        transitions += 1

    encoded = native.encode_actor_observation(
        engine.observation(0),
        dict(engine.configuration),
        4,
        None,
    )
    assert transitions == 3
    assert engine.done
    assert set(encoded) == {"board", "global", "units"}


def test_numeric_action_matches_official_boundary_transition() -> None:
    native = pytest.importorskip("kagg_revue.native._revue_native")
    official = native.Engine(seed=5, configuration={"episodeSteps": 4})
    numeric = official.clone()
    action = {"farmer": ["PASS"], "hands": [], "market": []}
    official.step(action, action)

    keys = list(native.action_codec_spec()["keys"])
    pass_token = keys.index("UNIT:PASS")
    stop_token = keys.index("MARKET:STOP")
    tokens = np.asarray([[pass_token, stop_token], [pass_token, stop_token]])
    quantities = np.zeros_like(tokens)
    counts = np.asarray([tokens.shape[1], tokens.shape[1]])
    units = np.ones(2, dtype=np.int64)
    numeric.step_numeric(tokens, quantities, counts, units)

    official_encoded = official.encode_numeric(0, 2)
    numeric_encoded = numeric.encode_numeric(0, 2)
    for expected, actual in zip(official_encoded, numeric_encoded, strict=True):
        np.testing.assert_array_equal(expected, actual)


def test_numeric_codec_preserves_order_slots_and_quantities() -> None:
    native = pytest.importorskip("kagg_revue.native._revue_native")
    keys = list(native.action_codec_spec()["keys"])
    selected = (
        "UNIT:PICKUP:WHEAT",
        "MARKET:SELL:WHEAT",
        "MARKET:SKIP_SLOT",
        "MARKET:HIRE",
        "MARKET:STOP",
    )
    tokens = np.asarray([keys.index(key) for key in selected], dtype=np.int64)
    quantities = np.asarray([7, 3, 0, 0, 0], dtype=np.int64)
    action = native.decode_action_tokens(tokens, quantities, len(selected), 1, len(selected))
    assert action == {
        "farmer": ["PICKUP", "WHEAT", 7],
        "hands": [],
        "market": [["SELL", "WHEAT", 3], [], ["HIRE"]],
    }


def test_engine_policy_session_matches_official_observation_session() -> None:
    native = pytest.importorskip("kagg_revue.native._revue_native")
    engine = native.Engine(seed=9, configuration={"episodeSteps": 4})
    direct = engine.policy_session(0, 2)
    official = native.PolicySession(engine.observation(0), dict(engine.configuration), 2)
    for direct_value, official_value in zip(direct.encode(), official.encode(), strict=True):
        np.testing.assert_array_equal(direct_value, official_value)
    np.testing.assert_array_equal(direct.legal_mask(), official.legal_mask())

    keys = list(native.action_codec_spec()["keys"])
    for token in (keys.index("UNIT:PASS"), keys.index("MARKET:STOP")):
        direct.select(token)
        official.select(token)
    assert direct.action() == official.action()


def test_inventory_order_features_preserve_private_insertion_order() -> None:
    native = pytest.importorskip("kagg_revue.native._revue_native")
    engine = native.Engine(seed=11, configuration={"episodeSteps": 4})
    observation = copy.deepcopy(engine.observation(0))
    names = list(native.actor_encoder_spec()["item_names"])
    observation["private"]["inventories"][0] = {
        names[3]: 2,
        names[1]: 4,
    }

    units = np.asarray(
        native.PolicySession(observation, dict(engine.configuration), 2).encode()[1]
    )
    start, stop = native.actor_encoder_spec()["unit_order_slice"]
    own_order = units[0, 0, start:stop]

    assert own_order[names.index(names[3])] == pytest.approx(1.0 / 12.0)
    assert own_order[names.index(names[1])] == pytest.approx(2.0 / 12.0)
    assert np.count_nonzero(own_order) == 2
    np.testing.assert_array_equal(units[1, :, start:stop], 0.0)


def test_market_hires_are_masked_at_actor_capacity_within_one_prefix() -> None:
    native = pytest.importorskip("kagg_revue.native._revue_native")
    engine = native.Engine(
        seed=13,
        configuration={"episodeSteps": 4, "maxMarketOrdersPerTurn": 4},
    )
    session = engine.policy_session(0, 3)
    keys = list(native.action_codec_spec()["keys"])
    hire = keys.index("MARKET:HIRE")

    session.select(keys.index("UNIT:PASS"))
    for expected in (True, True, False):
        assert bool(session.legal_mask()[hire]) is expected
        if expected:
            session.select(hire)
    with pytest.raises(ValueError, match="capacity"):
        session.select(hire)


def test_native_engine_batch_matches_individual_numeric_steps() -> None:
    native = pytest.importorskip("kagg_revue.native._revue_native")
    seeds = np.asarray([12, 13], dtype=np.int64)
    batch = native.EngineBatch(seeds, {"episodeSteps": 4})
    individual = [
        native.Engine(seed=int(seed), configuration={"episodeSteps": 4}) for seed in seeds
    ]
    keys = list(native.action_codec_spec()["keys"])
    actions = np.asarray([keys.index("UNIT:PASS"), keys.index("MARKET:STOP")], dtype=np.int64)
    tokens = np.broadcast_to(actions, (2, 2, 2)).copy()
    quantities = np.zeros_like(tokens)
    decisions = np.full((2, 2), 2, dtype=np.int64)
    units = np.ones((2, 2), dtype=np.int64)
    done = batch.step(tokens, quantities, decisions, units)
    for engine in individual:
        engine.step_numeric(tokens[0], quantities[0], decisions[0], units[0])
    np.testing.assert_array_equal(done, np.zeros(2, dtype=np.uint8))
    np.testing.assert_allclose(
        batch.money(),
        np.asarray([[engine.money(0), engine.money(1)] for engine in individual]),
    )


def test_deterministic_incumbent_batch_matches_observation_boundary() -> None:
    native = pytest.importorskip("kagg_revue.native._revue_native")
    configuration = {"episodeSteps": 8}
    seeds = (31, 32, 33, 34)
    candidate_players = np.asarray([0, 1, 0, 1], dtype=np.int64)
    engines = [native.Engine(seed, configuration) for seed in seeds]
    reference = [engine.clone() for engine in engines]
    sessions = [native.DeterministicIncumbentSession(configuration) for _ in seeds]
    planners = [native.NativePlanner(configuration, {"scheduler": "route_aware"}) for _ in seeds]
    width = 8
    stop = int(native.action_codec_spec()["market_stop_token"])

    while not all(engine.done for engine in engines):
        tokens = np.zeros((len(engines), 2, width), dtype=np.int64)
        quantities = np.zeros_like(tokens)
        decisions = np.zeros((len(engines), 2), dtype=np.int64)
        units = np.zeros_like(decisions)
        for row, (engine, player) in enumerate(zip(engines, candidate_players, strict=True)):
            observation = engine.observation(int(player))
            count = len(observation["farms"][int(player)]["farmer"])
            units[row, player] = count
            decisions[row, player] = count + 1
            tokens[row, player, count] = stop

        done = native.engine_step_deterministic_incumbent_batch(
            engines,
            candidate_players,
            sessions,
            tokens,
            quantities,
            decisions,
            units,
            len(engines),
        )
        for row, (engine, planner, player) in enumerate(
            zip(reference, planners, candidate_players, strict=True)
        ):
            opponent_action = planner.act(engine.observation(1 - int(player)))
            expected_done = engine.step_mixed_numeric(
                int(player),
                tokens[row, player],
                quantities[row, player],
                int(decisions[row, player]),
                int(units[row, player]),
                opponent_action,
            )
            assert bool(done[row]) is expected_done
            for seat in (0, 1):
                expected = engine.encode_numeric(seat, width)
                actual = engines[row].encode_numeric(seat, width)
                for expected_value, actual_value in zip(expected, actual, strict=True):
                    np.testing.assert_array_equal(expected_value, actual_value)


def test_native_policy_session_batch_matches_individual_sessions() -> None:
    native = pytest.importorskip("kagg_revue.native._revue_native")
    engines = [native.Engine(seed=seed, configuration={"episodeSteps": 4}) for seed in (21, 22)]
    sessions = [engine.policy_session(player, 2) for engine in engines for player in (0, 1)]
    batch = native.PolicySessionBatch(sessions, workers=2)

    encoded = batch.encode()
    for tensor_index, tensor in enumerate(encoded):
        expected = np.stack([session.encode()[tensor_index] for session in sessions])
        np.testing.assert_array_equal(tensor, expected)
    np.testing.assert_array_equal(
        batch.legal_masks(),
        np.stack([session.legal_mask() for session in sessions]),
    )
    phases, legal = batch.decision_inputs()
    np.testing.assert_array_equal(phases, np.zeros(len(sessions), dtype=np.int64))
    np.testing.assert_array_equal(
        legal,
        np.stack([session.legal_mask() for session in sessions]),
    )

    keys = list(native.action_codec_spec()["keys"])
    pass_token = keys.index("UNIT:PASS")
    stop_token = keys.index("MARKET:STOP")
    active = np.ones(len(sessions), dtype=np.uint8)
    quantities = np.zeros(len(sessions), dtype=np.int64)
    batch.select(np.full(len(sessions), pass_token), quantities, active)
    batch.select(np.full(len(sessions), stop_token), quantities, active)
    np.testing.assert_array_equal(batch.phases(), np.full(len(sessions), 2))


def test_incremental_policy_legality_matches_exact_prefix_compiler() -> None:
    native = pytest.importorskip("kagg_revue.native._revue_native")
    engine = native.Engine(seed=23, configuration={"episodeSteps": 8})
    passed = {"farmer": ["PASS"], "hands": [], "market": []}
    for _ in range(3):
        engine.step(
            {"farmer": ["PASS"], "hands": [], "market": [["HIRE"]]},
            passed,
        )
    session = engine.policy_session(0, 4)
    keys = list(native.action_codec_spec()["keys"])
    unit_tokens = int(native.action_codec_spec()["unit_tokens"])
    feature_names = list(native.derived_fact_spec()["candidate_feature_names"])
    executable = feature_names.index("executable")

    for preferred in ("UNIT:NORTH", "UNIT:WEST", "UNIT:SOUTH", "UNIT:EAST"):
        legal = np.asarray(session.legal_mask(), dtype=np.bool_)
        exact = np.asarray(session.candidate_facts())[:, executable] > 0.5
        np.testing.assert_array_equal(legal[:unit_tokens], exact[:unit_tokens])
        token = keys.index(preferred)
        session.select(token if legal[token] else keys.index("UNIT:PASS"))

    session.select(keys.index("MARKET:STOP"))
    engine.step(session.action(), passed)
