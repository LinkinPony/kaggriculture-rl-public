from __future__ import annotations

from kagg_revue.rl.plans.health import PlanCollapseGuard, PlanHealthObservation


def _observation(
    update: int,
    *,
    opponent_update: int = 0,
    stopped: float = 0.95,
    changed: float = 0.05,
    losses: int = 9,
) -> PlanHealthObservation:
    return PlanHealthObservation(
        update=update,
        opponent_update=opponent_update,
        stop_fraction=stopped,
        plan_change_fraction=changed,
        wins=1,
        ties=0,
        losses=losses,
    )


def _guard() -> PlanCollapseGuard:
    return PlanCollapseGuard(
        warmup_updates=3,
        anchor_panels=2,
        stop_fraction_floor=0.9,
        plan_change_fraction_ceiling=0.1,
        anchor_loss_rate_floor=0.8,
    )


def test_plan_collapse_guard_requires_repeated_direct_anchor_regression() -> None:
    guard = _guard()
    guard.observe(_observation(2, opponent_update=1))
    guard.observe(_observation(3))
    assert not guard.quarantined

    guard.observe(_observation(4, changed=0.5))
    guard.observe(_observation(5))
    assert not guard.quarantined
    report = guard.observe(_observation(6))
    assert guard.quarantined
    assert report["quarantined"] is True

    restored = _guard()
    restored.load_state_dict(guard.state_dict(), completed_update=6)
    assert restored.quarantined
