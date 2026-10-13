import pytest

from kagg_revue.rl.programs.schedule import rollout_seed_offset, update_range


def test_program_resume_uses_absolute_target() -> None:
    updates = update_range(3, 7)

    assert updates.start == 3
    assert updates.stop == 8


def test_program_rollout_seed_schedule_survives_resume() -> None:
    assert rollout_seed_offset(11, 1, 4) == 11
    assert rollout_seed_offset(11, 3, 4) == 19


@pytest.mark.parametrize("first_update,target_update", [(0, 2), (3, 2)])
def test_program_update_range_rejects_invalid_span(
    first_update: int,
    target_update: int,
) -> None:
    with pytest.raises(ValueError, match="target"):
        update_range(first_update, target_update)
