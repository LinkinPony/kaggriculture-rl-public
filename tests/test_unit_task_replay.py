from kagg_revue.rl.tasks.replay import UnitTraceStep, compress_unit_trace


def test_replay_compression_preserves_timing_and_waypoints() -> None:
    trace = (
        UnitTraceStep(0, (1, 1), ("NORTH",)),
        UnitTraceStep(1, (1, 0), ("EAST",)),
        UnitTraceStep(2, (2, 0), ("PASS",)),
        UnitTraceStep(3, (2, 0), ("WATER",)),
    )
    audit = compress_unit_trace(trace, board_size=5, day_end=5)
    assert audit.exact_reconstruction
    assert audit.waypoint_tasks == 1
    assert audit.waited_turns == 1
    assert [task.operation.name for task in audit.tasks] == ["POSITION", "WATER"]


def test_replay_compression_normalizes_implicit_unit_quantity() -> None:
    trace = (UnitTraceStep(0, (0, 0), ("PLACE", "SHEEP")),)
    audit = compress_unit_trace(trace, board_size=2, day_end=1)
    assert audit.exact_reconstruction
    assert audit.tasks[0].quantity == 1
