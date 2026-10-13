import numpy as np

from kagg_revue.native import _revue_native as native


def test_bulk_replay_preserves_visible_history_and_aligns_next_step_actions() -> None:
    environment = {"boardSize": 4, "episodeSteps": 9, "turnsPerDay": 3, "maxMarketOrdersPerTurn": 2}
    engine = native.Engine(7, environment)
    units = 2
    batch = native.ParallelBatch(environment, [7], [0], ["pass"], [None], [], units, 1, [1])
    steps = [
        [
            {"observation": engine.observation(seat), "status": "ACTIVE", "action": {}}
            for seat in (0, 1)
        ]
    ]
    for turn in range(8):
        action = {"farmer": ["EAST"] if turn == 0 else [], "hands": [], "market": []}
        engine.step(action, {})
        steps.append(
            [
                {
                    "observation": engine.observation(seat),
                    "status": "ACTIVE",
                    "action": action if seat == 0 else {},
                }
                for seat in (0, 1)
            ]
        )
    for seat in (0, 1):
        encoded = np.empty((8, batch.entity_features), np.float16)
        labels = np.empty((8, units + 2, 2), np.int64)
        native.ContractSession(environment, units).encode_replay_into(steps, seat, encoded, labels)
        reference = native.ContractSession(environment, units)
        for turn in range(8):
            reference.update(steps[turn][seat]["observation"])
            expected = np.empty((1, batch.entity_features), np.float16)
            reference.observe_into(expected)
            np.testing.assert_array_equal(encoded[turn], expected[0])
        if seat == 0:
            assert labels[0, 0, 0] != labels[-1, 0, 0]
            assert not labels[-1].any()
        else:
            assert not labels.any()
