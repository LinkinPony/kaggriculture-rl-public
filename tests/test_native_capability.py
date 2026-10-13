import numpy as np
import pytest


def test_capability_candidate_batch_obeys_numeric_abi() -> None:
    native = pytest.importorskip("kagg_revue.native._revue_native")
    configuration = {"episodeSteps": 48}
    engines = [native.Engine(seed=seed, configuration=configuration) for seed in (3, 5)]
    sessions = [native.CapabilitySession(configuration, 12, 2) for _ in engines]
    players = np.asarray([0, 1], dtype=np.int64)

    candidates = native.capability_candidates_batch(
        sessions, engines, players, workers=2
    )
    spec = native.capability_spec()
    assert candidates["mode"].shape == (2, 12)
    assert candidates["int_fields"].shape == (2, 12, 2, 6)
    assert candidates["float_fields"].shape == (2, 12, 2, 4)
    assert candidates["candidate_features"].shape == (2, 12, 32)
    assert candidates["root_features"].shape == (2, 90)
    assert candidates["candidate_mask"][:, 0].all()
    np.testing.assert_array_equal(candidates["float_fields"], candidates["edit_values"])
    np.testing.assert_array_equal(candidates["candidate_mask"], candidates["mask"])

    for column, vocabulary_size in enumerate(spec["integer_vocab_sizes"]):
        values = candidates["int_fields"][..., column]
        assert np.all(values >= 0)
        assert np.all(values < vocabulary_size)
    padding = candidates["edit_mask"] == 0
    assert np.all(candidates["int_fields"][padding] == 0)
    assert np.all(candidates["float_fields"][padding] == 0.0)


def test_selected_capability_executes_until_next_day_boundary() -> None:
    native = pytest.importorskip("kagg_revue.native._revue_native")
    configuration = {"episodeSteps": 50}
    engine = native.Engine(seed=7, configuration=configuration)
    session = native.CapabilitySession(configuration, 16, 2)
    candidates = session.candidates(engine, 0)
    patch = int(
        np.flatnonzero(
            (candidates["mode"] == native.capability_spec()["modes"]["PATCH"])
            & (candidates["candidate_mask"] != 0)
        )[0]
    )
    session.select(patch)
    assert not session.decision_required(engine, 0)

    turns_per_day = int(engine.configuration["turnsPerDay"])
    for _ in range(turns_per_day):
        action = session.action_numeric(engine, 0)
        assert not action["requires_direct"]
        width = max(1, int(action["decision_count"]))
        tokens = np.zeros((2, width), dtype=np.int64)
        quantities = np.zeros_like(tokens)
        decision_counts = np.ones(2, dtype=np.int64)
        unit_counts = np.ones(2, dtype=np.int64)
        count = int(action["decision_count"])
        tokens[0, :count] = action["tokens"]
        quantities[0, :count] = action["quantities"]
        decision_counts[0] = count
        unit_counts[0] = int(action["unit_count"])
        engine.step_numeric(tokens, quantities, decision_counts, unit_counts)

    assert session.decision_required(engine, 0)


def test_direct_controller_is_one_macro_choice_per_day() -> None:
    native = pytest.importorskip("kagg_revue.native._revue_native")
    configuration = {"episodeSteps": 48}
    engine = native.Engine(seed=11, configuration=configuration)
    session = native.CapabilitySession(configuration, 16, 2)
    candidates = session.candidates(engine, 0)
    direct = int(
        np.flatnonzero(
            (candidates["mode"] == native.capability_spec()["modes"]["DIRECT_TURN"])
            & (candidates["candidate_mask"] != 0)
        )[0]
    )
    session.select(direct)
    assert not session.decision_required(engine, 0)

    width = 1
    tokens = np.zeros((2, width), dtype=np.int64)
    quantities = np.zeros_like(tokens)
    counts = np.ones(2, dtype=np.int64)
    units = np.ones(2, dtype=np.int64)
    for _ in range(int(engine.configuration["turnsPerDay"])):
        assert session.action_numeric(engine, 0)["requires_direct"]
        engine.step_numeric(tokens, quantities, counts, units)

    assert session.decision_required(engine, 0)
