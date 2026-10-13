from pathlib import Path
from typing import Any

from kagg_revue.teacher.submission import (
    ConditionalRouteArtifact,
    ConditionalRouteBranch,
    SubmissionTeacher,
    SubmissionTeacherArtifact,
)


def _action(operation: str, *, hands: list[list[str]] | None = None) -> dict[str, Any]:
    return {
        "farmer": [operation],
        "hands": [] if hands is None else hands,
        "market": [],
    }


def _observation(
    step: int,
    *,
    day: int = 0,
    shops: list[str] | None = None,
    hands: list[list[int]] | None = None,
    farmer_tile: dict[str, str] | str = "SOIL",
) -> dict[str, Any]:
    farm = {
        "farmer": [0, 0],
        "hands": [] if hands is None else hands,
        "tiles": [[farmer_tile, "SOIL"], ["SOIL", "SOIL"]],
    }
    return {
        "step": step,
        "day": day,
        "player": 0,
        "farms": [farm, farm],
        "town": {"unlocked_shops": [] if shops is None else shops},
    }


def _teacher(
    default: tuple[dict[str, Any], ...],
    *,
    branches: tuple[ConditionalRouteBranch, ...] = (),
    repair_weeds: bool = False,
) -> SubmissionTeacher:
    route = ConditionalRouteArtifact(
        event_shop="YARN_STORE",
        default_route_id="default",
        default_support=1,
        default_actions=default,
        branches=branches,
        source={"fixture": True},
    )
    artifact = SubmissionTeacherArtifact(
        archive_path=Path("synthetic.tar.gz"),
        archive_sha256="a" * 64,
        source_commit="b" * 40,
        route_sha256="c" * 64,
        repair_weeds=repair_weeds,
        weed_replay_steps=2,
        route=route,
    )
    return SubmissionTeacher({"episodeSteps": len(default) + 1}, artifact)


def test_submission_teacher_switches_only_after_observable_branch() -> None:
    default = (_action("PASS"), _action("NORTH"))
    branch = ConditionalRouteBranch(
        route_id="day-3",
        first_event_day=3,
        activation_step=1,
        support=1,
        actions=(default[0], _action("SOUTH")),
    )
    teacher = _teacher(default, branches=(branch,))

    initial = teacher.plan(_observation(0, hands=[[1, 0]]))
    switched = teacher.plan(_observation(1, day=3, shops=["YARN_STORE"]))

    assert initial["action"] == _action("PASS", hands=[["PASS"]])
    assert switched["action"] == _action("SOUTH")
    assert teacher.metadata()["route_id"] == "day-3"
    teacher.reset()
    assert teacher.act(_observation(1)) == _action("NORTH")


def test_submission_teacher_replays_intended_action_after_weed_dig() -> None:
    teacher = _teacher(
        (_action("PLANT", hands=None) | {"farmer": ["PLANT", "WHEAT"]}, _action("PASS")),
        repair_weeds=True,
    )

    repaired = teacher.plan(_observation(0, farmer_tile={"kind": "WEED"}))
    replayed = teacher.plan(_observation(1))

    assert repaired["action"]["farmer"] == ["DIG"]
    assert repaired["weed_repairs_started"] == 1
    assert replayed["action"]["farmer"] == ["PLANT", "WHEAT"]
