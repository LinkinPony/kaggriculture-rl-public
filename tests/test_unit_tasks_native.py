import numpy as np
import pytest
import torch

from kagg_revue.native import _revue_native as native
from kagg_revue.policy.tasks import (
    NativeTaskContract,
    UnitTaskPolicy,
    decision_inputs,
    plan_unit_tasks,
)
from kagg_revue.policy.tasks.contract import TaskOperation, TaskResultStatus
from kagg_revue.policy.tasks.gpu import TaskPlanningState
from kagg_revue.policy.tasks.grammar import TaskActions
from kagg_revue.policy.tasks.runtime import CompactTaskTrace
from kagg_revue.rl.tasks.compact import (
    collate_compact_task_records,
    compact_turn_records,
)


def _task_model(session: object) -> tuple[NativeTaskContract, UnitTaskPolicy]:
    contract = NativeTaskContract.from_spec(session.spec())
    architecture = contract.architecture(
        context_width=32,
        model_width=32,
        feedforward_width=64,
        attention_heads=4,
        prefix_layers=1,
    )
    return contract, UnitTaskPolicy(architecture, contract.catalog)


def test_native_task_time_is_independent_across_units() -> None:
    engine = native.Engine(17)
    engine.step(
        {"farmer": ["PASS"], "market": [["HIRE"]]},
        {"farmer": ["PASS"]},
    )
    session = native.UnitTaskSession(None, 4, 16)
    spec = session.spec()
    operations = np.asarray(spec["candidate_operations"])
    targets = np.asarray(spec["candidate_targets"])
    assert set(np.unique(operations)) == set(range(len(TaskOperation)))
    assert targets.shape[1] == 2

    first = session.observation(engine, 0)
    candidate_mask = np.asarray(first["candidate_mask"], dtype=np.bool_)
    arrivals = np.asarray(first["candidate_arrivals"], dtype=np.int64)
    positions = np.flatnonzero(
        (operations == int(TaskOperation.POSITION)) & candidate_mask
    )
    selected = int(positions[np.argmax(arrivals[positions])])
    completion = int(arrivals[selected])
    session.select(
        engine,
        0,
        1,
        selected,
        0,
        int(first["available_at"]),
        completion,
    )
    session.select(engine, 0, 1, 0, 0, 0, 0)
    second = session.observation(engine, 0)
    assert int(second["unit_index"]) == 1
    assert int(second["available_at"]) == int(first["available_at"])
    assert int(second["available_at"]) < completion


def test_official_visible_state_matches_engine_task_boundary() -> None:
    engine = native.Engine(19)
    engine_session = native.UnitTaskSession(None, 4, 16)
    visible_session = native.UnitTaskSession(None, 4, 16)
    visible = visible_session.visible_state(engine.observation(0))
    engine_decision = engine_session.observation(engine, 0)
    visible_decision = visible_session.observation_visible(visible)
    for key in (
        "mode_mask",
        "candidate_mask",
        "candidate_arrivals",
        "candidate_reasons",
        "candidate_features",
        "prefix_fields",
        "prefix_mask",
        "root_features",
    ):
        np.testing.assert_array_equal(engine_decision[key], visible_decision[key])
    engine_session.select(engine, 0, 1, 0, 0, 0, 0)
    visible_session.select_visible(visible, 1, 0, 0, 0, 0)
    engine_action = engine_session.action_numeric(engine, 0)
    visible_action = visible_session.action_numeric_visible(visible)
    np.testing.assert_array_equal(engine_action["tokens"], visible_action["tokens"])
    np.testing.assert_array_equal(
        engine_action["quantities"], visible_action["quantities"]
    )


def test_dynamic_operation_failure_is_feedback_not_a_hard_mask() -> None:
    engine = native.Engine(23)
    session = native.UnitTaskSession(None, 4, 16)
    spec = session.spec()
    operations = np.asarray(spec["candidate_operations"])
    targets = np.asarray(spec["candidate_targets"])
    farmer = tuple(engine.observation(0)["farms"][0]["farmer"])
    selected = int(
        np.flatnonzero(
            (operations == int(TaskOperation.WATER))
            & (targets[:, 0] == farmer[0])
            & (targets[:, 1] == farmer[1])
        )[0]
    )
    observation = session.observation(engine, 0)
    assert bool(np.asarray(observation["candidate_mask"])[selected])
    assert np.asarray(observation["candidate_features"])[selected, 7] == 0.0
    session.select(engine, 0, 1, selected, 0, 0, 1)
    session.select(engine, 0, 1, 0, 0, 0, 0)
    compiled = session.action_numeric(engine, 0)
    assert int(compiled["task_results"][0]) == int(TaskResultStatus.TARGET_INVALID)
    engine.step_mixed_numeric(
        0,
        compiled["tokens"],
        compiled["quantities"],
        1,
        1,
        {},
    )
    feedback = session.observation(engine, 0)
    prefix = np.asarray(feedback["prefix_fields"])
    assert int(feedback["replan_reason"]) == 4
    assert prefix[0, 8] == 1 + int(TaskResultStatus.TARGET_INVALID)


def test_task_policy_replays_exact_masks_and_forced_end() -> None:
    engine = native.Engine(31)
    session = native.UnitTaskSession(None, 4, 16)
    contract, model = _task_model(session)
    raw = native.unit_task_observations_batch(
        [session], [engine], np.asarray([0], dtype=np.int64), 1
    )
    assert np.asarray(raw["prefix_fields"]).dtype == np.int32
    for name in (
        "unit_indices",
        "available_at",
        "day_end",
        "replan_reasons",
        "candidate_arrivals",
        "candidate_reasons",
    ):
        assert np.asarray(raw[name]).dtype == np.int16
    inputs = decision_inputs(raw, torch.zeros(1, 32), contract, device="cpu")
    assert inputs.prefix_fields.dtype == torch.int32
    assert inputs.candidate_features.dtype == torch.float16
    with torch.inference_mode():
        sampled = model.rollout(inputs, sample=True)
        replayed = model.evaluate_actions(inputs, sampled.actions, sampled.masks)
    torch.testing.assert_close(
        sampled.joint_log_probability, replayed.joint_log_probability
    )

    wait = int(
        np.flatnonzero(
            np.asarray(session.spec()["candidate_operations"])
            == int(TaskOperation.WAIT)
        )[0]
    )
    day_end = int(raw["day_end"][0])
    session.select(engine, 0, 1, wait, 0, day_end, day_end)
    forced_raw = native.unit_task_observations_batch(
        [session], [engine], np.asarray([0], dtype=np.int64), 1
    )
    assert np.asarray(forced_raw["candidate_mask"]).sum() == 1
    forced_inputs = decision_inputs(
        forced_raw, torch.zeros(1, 32), contract, device="cpu"
    )
    with torch.inference_mode():
        forced = model.rollout(forced_inputs, sample=True)
    assert int(forced.actions.candidate[0]) == 0
    assert int(forced.factor_counts[0]) == 0
    assert float(forced.joint_log_probability[0]) == 0.0


def test_factorized_task_rollout_reconstructs_from_compact_state() -> None:
    engine = native.Engine(33)
    session = native.UnitTaskSession(None, 4, 16)
    contract = NativeTaskContract.from_spec(session.spec())
    architecture = contract.architecture(
        architecture_version="factorized-v3",
        context_width=32,
        model_width=32,
        feedforward_width=64,
        attention_heads=4,
        prefix_layers=1,
        history_window=64,
    )
    model = UnitTaskPolicy(architecture, contract.catalog).eval()
    dense = session.observation(engine, 0)
    compact = session.compact_observation(engine, 0)
    for name in (
        "root_features",
        "prefix_fields",
        "prefix_mask",
        "target_conflicts",
        "resource_conflicts",
        "mode_mask",
    ):
        np.testing.assert_array_equal(compact[name], dense[name])
    assert "candidate_features" not in compact
    assert "candidate_mask" not in compact
    assert "candidate_arrivals" not in compact

    policy_batch = native.engine_policy_session_batch([engine], [0], 4, 1)
    economic_array = np.asarray(policy_batch.gpu_state_compact(), dtype=np.int32)
    economic_state = torch.as_tensor(economic_array)
    generator = torch.Generator().manual_seed(33)
    with torch.inference_mode():
        _compiled, trace = plan_unit_tasks(
            native,
            model,
            contract,
            [session],
            [engine],
            np.asarray([0], dtype=np.int64),
            torch.zeros((1, 32)),
            economic_state,
            workers=1,
            sample=True,
            generator=generator,
            record=True,
        )
    assert isinstance(trace, CompactTaskTrace)
    record = compact_turn_records(trace, turn_index=0)[0]
    assert record is not None
    batch = collate_compact_task_records(
        [record],
        [economic_array[0]],
        np.asarray([0], dtype=np.int64),
        context_width=32,
        contract=contract,
        device=torch.device("cpu"),
        factorized=True,
        history_window=architecture.history_window,
    )
    with torch.inference_mode():
        replayed = model.evaluate_actions(
            batch.inputs, batch.actions, batch.masks
        )
    torch.testing.assert_close(
        replayed.joint_log_probability,
        batch.old_joint_log_probability,
    )
    torch.testing.assert_close(replayed.value, batch.old_values)


def test_history_pressure_preserves_every_active_task() -> None:
    configuration = {
        "turnsPerDay": 4,
        "episodeSteps": 8,
        "maxMarketOrdersPerTurn": 2,
    }
    engine = native.Engine(37, configuration)
    session = native.UnitTaskSession(configuration, 1, 16)
    operations = np.asarray(session.spec()["candidate_operations"])
    wait = int(
        np.flatnonzero(operations == int(TaskOperation.WAIT))[0]
    )
    for boundary in range(1, 5):
        session.observation(engine, 0)
        session.select(engine, 0, 1, wait, 0, boundary, boundary)
    session.select(engine, 0, 1, 0, 0, 0, 0)
    compiled = session.action_numeric(engine, 0)
    engine.step_mixed_numeric(
        0,
        compiled["tokens"],
        compiled["quantities"],
        1,
        1,
        {},
    )
    for boundary in range(2, 5):
        session.observation(engine, 0)
        session.select(engine, 0, 1, wait, 0, boundary, boundary)
    pressure = session.observation(engine, 0)
    mask = np.asarray(pressure["prefix_mask"], dtype=np.bool_)
    fields = np.asarray(pressure["prefix_fields"])[mask]
    assert fields.shape == (4, 9)
    assert np.count_nonzero(fields[:, 8] == 0) == 3
    assert np.asarray(pressure["candidate_mask"]).sum() == 1


def test_native_task_sequence_batch_matches_incremental_selection() -> None:
    engines = [native.Engine(41), native.Engine(41)]
    sessions = [native.UnitTaskSession(None, 4, 16) for _ in engines]
    players = np.asarray([0], dtype=np.int64)
    operations = np.asarray(sessions[0].spec()["candidate_operations"])
    wait = int(np.flatnonzero(operations == int(TaskOperation.WAIT))[0])
    sessions[0].select(engines[0], 0, 1, wait, 0, 1, 1)
    sessions[0].select(engines[0], 0, 1, 0, 0, 0, 0)
    snapshot = native.unit_task_snapshots_batch(
        [sessions[1]], [engines[1]], players, 1
    )
    assert bool(np.asarray(snapshot["requires_decision"])[0])
    selections = np.asarray(
        [[[1, wait, 0, 1, 1], [1, 0, 0, 0, 0]]], dtype=np.int16
    )
    native.unit_task_apply_sequences_batch(
        [sessions[1]],
        [engines[1]],
        players,
        selections,
        np.asarray([2], dtype=np.int16),
        1,
    )
    incremental = sessions[0].action_numeric(engines[0], 0)
    batched = sessions[1].action_numeric(engines[1], 0)
    for name in ("tokens", "quantities", "task_results"):
        np.testing.assert_array_equal(incremental[name], batched[name])


@pytest.mark.skipif(not torch.cuda.is_available(), reason="CUDA is unavailable")
def test_gpu_task_decision_matches_native_surface() -> None:
    engine = native.Engine(43)
    engine.step(
        {"farmer": ["PASS"], "market": [["HIRE"]]},
        {"farmer": ["PASS"]},
    )
    session = native.UnitTaskSession(None, 4, 16)
    contract = NativeTaskContract.from_spec(session.spec())
    players = np.asarray([0], dtype=np.int64)
    snapshot = native.unit_task_snapshots_batch([session], [engine], players, 1)
    policy_batch = native.engine_policy_session_batch([engine], [0], 4, 1)
    economic_state = torch.as_tensor(
        np.asarray(policy_batch.gpu_state_compact(), dtype=np.int32),
        device="cuda",
    )
    state = TaskPlanningState.from_native(snapshot, economic_state, contract)
    rows = torch.zeros(1, dtype=torch.long, device="cuda")
    context = torch.zeros((1, 32), device="cuda")
    catalog = contract.catalog.to("cuda")

    def compare_surface(decision: int) -> tuple[object, object]:
        inputs = state.inputs(
            rows,
            context,
            catalog,
            prefix_length=min(
                contract.prefix_capacity,
                state.initial_prefix_length + decision,
            ),
        )
        expected = native.unit_task_observations_batch(
            [session], [engine], players, 1
        )
        actual = {
            "root_features": inputs.root_features.cpu().numpy(),
            "prefix_fields": inputs.prefix_fields.cpu().numpy(),
            "prefix_mask": inputs.prefix_mask.cpu().numpy(),
            "candidate_features": inputs.candidate_features.float().cpu().numpy(),
            "candidate_mask": inputs.candidate_mask.cpu().numpy(),
            "candidate_arrivals": inputs.candidate_arrivals.cpu().numpy(),
            "mode_mask": inputs.mode_mask.cpu().numpy(),
            "available_at": inputs.available_at.cpu().numpy(),
            "day_end": inputs.day_end.cpu().numpy(),
        }
        for name, value in actual.items():
            reference = np.asarray(expected[name])
            if "features" in name:
                np.testing.assert_allclose(value, reference, atol=5e-4, rtol=0.0)
            else:
                np.testing.assert_array_equal(value, reference)
        return inputs, expected

    operations = np.asarray(session.spec()["candidate_operations"])
    targets = np.asarray(session.spec()["candidate_targets"])
    for decision in range(4):
        inputs, expected = compare_surface(decision)
        if decision % 2:
            candidate = 0
            earliest = 0
            deadline = 0
        else:
            candidate_mask = np.asarray(expected["candidate_mask"])[0]
            candidates = np.flatnonzero(
                candidate_mask
                & (operations == int(TaskOperation.POSITION))
                & (targets[:, 0] >= 0)
            )
            candidate = int(candidates[0])
            earliest = int(inputs.available_at.item())
            deadline = int(inputs.candidate_arrivals[0, candidate].item())
        values = (1, candidate, 0, earliest, deadline)
        actions = TaskActions(
            *(torch.tensor([value], device="cuda") for value in values)
        )
        state.apply(
            rows,
            actions,
            catalog,
            inputs.candidate_arrivals[:, candidate].contiguous(),
        )
        session.select(engine, 0, *values)
    assert not bool(state.active.item())


@pytest.mark.skipif(not torch.cuda.is_available(), reason="CUDA is unavailable")
def test_gpu_task_conflicts_match_native_across_retained_suffix() -> None:
    engine = native.Engine(47)
    engine.step(
        {"farmer": ["PASS"], "market": [["HIRE"]]},
        {"farmer": ["PASS"]},
    )
    session = native.UnitTaskSession(None, 4, 16)
    contract = NativeTaskContract.from_spec(session.spec())
    operations = np.asarray(session.spec()["candidate_operations"])
    targets = np.asarray(session.spec()["candidate_targets"])
    players = np.asarray([0], dtype=np.int64)

    observation = session.observation(engine, 0)
    arrivals = np.asarray(observation["candidate_arrivals"])
    legal = np.asarray(observation["candidate_mask"], dtype=np.bool_)
    adjacent = np.flatnonzero(
        legal
        & (operations == int(TaskOperation.POSITION))
        & (targets[:, 0] >= 0)
        & (arrivals == int(observation["available_at"]) + 1)
    )
    position = int(adjacent[0])
    session.select(
        engine,
        0,
        1,
        position,
        0,
        int(observation["available_at"]),
        int(arrivals[position]),
    )
    observation = session.observation(engine, 0)
    legal = np.asarray(observation["candidate_mask"], dtype=np.bool_)
    plant = int(
        np.flatnonzero(legal & (operations == int(TaskOperation.PLANT)))[0]
    )
    arrival = int(np.asarray(observation["candidate_arrivals"])[plant])
    session.select(engine, 0, 1, plant, 0, arrival, arrival + 1)
    session.select(engine, 0, 1, 0, 0, 0, 0)
    assert int(session.observation(engine, 0)["unit_index"]) == 1
    session.select(engine, 0, 1, 0, 0, 0, 0)
    compiled = session.action_numeric(engine, 0)
    engine.step_mixed_numeric(
        0,
        compiled["tokens"],
        compiled["quantities"],
        int(compiled["unit_count"]),
        int(compiled["unit_count"]),
        {},
    )

    snapshot = native.unit_task_snapshots_batch(
        [session], [engine], players, 1
    )
    assert np.asarray(snapshot["optional_mask"])[0, 0] == 1
    policy_batch = native.engine_policy_session_batch([engine], [0], 4, 1)
    economic_state = torch.as_tensor(
        np.asarray(policy_batch.gpu_state_compact(), dtype=np.int32),
        device="cuda",
    )
    state = TaskPlanningState.from_native(snapshot, economic_state, contract)
    rows = torch.zeros(1, dtype=torch.long, device="cuda")
    context = torch.zeros((1, 32), device="cuda")
    catalog = contract.catalog.to("cuda")

    for decision in range(2):
        inputs = state.inputs(
            rows,
            context,
            catalog,
            prefix_length=state.initial_prefix_length,
        )
        expected = native.unit_task_observations_batch(
            [session], [engine], players, 1
        )
        np.testing.assert_allclose(
            inputs.candidate_features.float().cpu().numpy(),
            np.asarray(expected["candidate_features"]),
            atol=5e-4,
            rtol=0.0,
        )
        np.testing.assert_array_equal(
            inputs.candidate_mask.cpu().numpy(),
            np.asarray(expected["candidate_mask"]),
        )
        if decision == 0:
            actions = TaskActions(
                *(torch.zeros(1, dtype=torch.long, device="cuda") for _ in range(5))
            )
            state.apply(
                rows,
                actions,
                catalog,
                inputs.candidate_arrivals[:, 0].contiguous(),
            )
            session.select(engine, 0, 0, 0, 0, 0, 0)
