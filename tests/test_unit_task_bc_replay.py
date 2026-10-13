import torch

from kagg_revue.bc.actions import EncodedTurnAction, ReplayActionEncoder
from kagg_revue.bc.tasks.replay import (
    canonicalize_boundary_movements,
    canonicalize_static_unit_noops,
)
from kagg_revue.policy.tasks.grammar import TaskCatalog


def _codec() -> ReplayActionEncoder:
    return ReplayActionEncoder(
        {
            "keys": (
                "UNIT:PASS",
                "UNIT:NORTH",
                "UNIT:SOUTH",
                "UNIT:EAST",
                "UNIT:WEST",
                "UNIT:DROP",
                "MARKET:STOP",
            ),
            "unit_tokens": 6,
            "market_stop_token": 6,
        }
    )


def test_boundary_movement_noop_is_canonicalized_to_pass() -> None:
    codec = _codec()
    encoded = EncodedTurnAction(
        tokens=(2, 3, 6),
        quantities=(0, 0, 0),
        unit_decisions=2,
        market_orders=0,
        repairs={},
    )

    result = canonicalize_boundary_movements(
        encoded,
        positions=((2, 4), (0, 0)),
        board_size=5,
        codec=codec,
    )

    assert result.tokens == (0, 3, 6)
    assert result.quantities == encoded.quantities
    assert result.repairs == {"out_of_board_movements_to_pass": 1}


def test_in_board_movement_is_preserved_without_repair() -> None:
    codec = _codec()
    encoded = EncodedTurnAction(
        tokens=(1, 6),
        quantities=(0, 0),
        unit_decisions=1,
        market_orders=0,
        repairs={},
    )

    result = canonicalize_boundary_movements(
        encoded,
        positions=((2, 2),),
        board_size=5,
        codec=codec,
    )

    assert result is encoded


def test_statically_impossible_operation_is_canonicalized_to_pass() -> None:
    codec = _codec()
    catalog = TaskCatalog(
        operations=torch.tensor((0, 4)),
        arguments=torch.tensor((-1, -1)),
        targets=torch.tensor(((-1, -1), (1, 1))),
        requires_quantity=torch.tensor((False, False)),
        operation_turns=torch.tensor((0, 1)),
    )
    encoded = EncodedTurnAction(
        tokens=(5, 6),
        quantities=(0, 0),
        unit_decisions=1,
        market_orders=0,
        repairs={},
    )

    result = canonicalize_static_unit_noops(
        encoded,
        positions=((2, 2),),
        codec=codec,
        catalog=catalog,
    )

    assert result.tokens == (0, 6)
    assert result.repairs == {
        "statically_impossible_unit_operations_to_pass": 1
    }
