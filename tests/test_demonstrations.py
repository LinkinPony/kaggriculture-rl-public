import json
from pathlib import Path

import numpy as np
import pytest

from kagg_revue.datasets.demonstrations.encoding import quantity_columns
from kagg_revue.datasets.demonstrations.shards import index_quantities
from kagg_revue.datasets.demonstrations.verify import verify
from kagg_revue.native import _revue_native as native
from kagg_revue.policy.settings import GeometrySettings, ModelSettings
from kagg_revue.production.contracts import ContractLayout


def _geometry() -> GeometrySettings:
    return GeometrySettings(
        unit_limit=3,
        width=16,
        decision_interval=1,
        quantity_max=16,
        quantity_extra=(32,),
        environment={
            "boardSize": 4,
            "episodeSteps": 13,
            "turnsPerDay": 6,
            "maxMarketOrdersPerTurn": 4,
        },
        model=ModelSettings(architecture="grounded-v1", time_prior=False, critic_depth=1),
    )


def test_sorted_replay_targets_reproduce_state_features_and_have_actor_support() -> None:
    geometry = _geometry()
    engine = native.Engine(11, geometry.environment)
    steps = []
    actions = [
        {
            "farmer": ["PASS"],
            "market": [["BUY_PRODUCT", "WHEAT", 4], ["BUY_PRODUCT", "FERTILIZER", 2], ["HIRE"]],
        },
        {"farmer": ["PICKUP", "WHEAT", 2]},
        {"farmer": ["PICKUP", "FERTILIZER", 1]},
        {"farmer": ["WATER"]},
        {"farmer": ["DROP"]},
        {"farmer": ["NORTH"], "market": [["BUY_SEED", "WHEAT", 1]]},
        {"farmer": ["PLANT", "WHEAT"]},
        {"farmer": ["WATER"]},
        {"farmer": ["HARVEST"]},
        {},
        {},
        {},
    ]
    for step in range(13):
        if step:
            engine.step(actions[step - 1], actions[step - 1])
        steps.append(
            [
                {
                    "observation": engine.observation(seat),
                    "action": actions[step - 1] if step else None,
                    "status": "ACTIVE" if step < 12 else "DONE",
                }
                for seat in (0, 1)
            ]
        )
    replay = json.loads(
        json.dumps(
            {"steps": steps, "configuration": geometry.environment, "info": {"seed": 11}},
            sort_keys=True,
        )
    )
    result = verify(replay, ContractLayout.resolve(geometry))
    assert result["matched"]
    assert result["verified_observations"] == 26
    assert result["eligible_rows"] == 24
    assert result["inventory_order_reconstructions"] > 0
    assert not {"ppo", "bc"} & geometry.model_dump().keys()


def test_unseen_selection_quantities_are_flagged_without_extending_training_vocabulary(
    tmp_path: Path,
) -> None:
    layout = ContractLayout.resolve(_geometry())
    labels = np.zeros((2, layout.factors), np.int64)
    labels[:, quantity_columns(layout)] = 1
    labels[1, quantity_columns(layout)[0]] = 777
    for name, data in (
        ("raw_actions", labels),
        ("observations", np.zeros((2, 1))),
        ("origins", np.zeros((2, 2))),
    ):
        np.save(tmp_path / f"shard-{name}.npy", data)
    record = {
        "raw_actions": "shard-raw_actions.npy",
        "observations": "shard-observations.npy",
        "origins": "shard-origins.npy",
        "split": "train",
        "literal_quantities": [1, 777],
    }
    with pytest.raises(ValueError, match="dropped a training label"):
        index_quantities(tmp_path, record.copy(), layout)
    record["split"] = "selection"
    index_quantities(tmp_path, record, layout)
    np.testing.assert_array_equal(np.load(tmp_path / record["quantity_coverage"]), [True, False])
    assert record["quantity_uncovered_rows"] == 1
    assert 777 not in layout.observation.quantities


@pytest.mark.parametrize("split", ["train", "selection", "confirmation"])
def test_fixed_quantity_cap_preserves_small_counts_and_other_action_fields(
    tmp_path: Path, split: str
) -> None:
    geometry = _geometry().model_copy(update={"quantity_max": 100, "quantity_extra": ()})
    layout = ContractLayout.resolve(geometry)
    columns = quantity_columns(layout)
    labels = np.zeros((3, layout.factors), np.int64)
    labels[:, columns] = 1
    labels[:, 0] = [1, 2, 3]
    labels[:, columns[0]] = [99, 100, 101]
    labels[:, columns[-1]] = [80, 100, 1000000]
    for name, data in (
        ("raw_actions", labels),
        ("observations", np.zeros((3, 1))),
        ("origins", np.zeros((3, 2))),
    ):
        np.save(tmp_path / f"shard-{name}.npy", data)
    record = {
        "raw_actions": "shard-raw_actions.npy",
        "observations": "shard-observations.npy",
        "origins": "shard-origins.npy",
        "split": split,
        "literal_quantities": [1, 80, 99, 100, 101, 1000000],
    }
    index_quantities(tmp_path, record, layout, clip=True)
    actual = np.load(tmp_path / record["actions"]).astype(np.int64)
    actual[:, columns] = np.asarray(layout.observation.quantities)[actual[:, columns]]
    expected = labels.copy()
    expected[:, columns] = np.minimum(expected[:, columns], 100)
    np.testing.assert_array_equal(actual, expected)
    np.testing.assert_array_equal(np.load(tmp_path / record["quantity_coverage"]), True)
    assert record["quantity_clipped_fields"] == 2
    assert record["quantity_clipped_rows"] == 1
    assert record["quantity_uncovered_rows"] == 0
