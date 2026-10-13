from dataclasses import asdict

from kagg_revue.production.expert.budget import LearningBudget


def test_only_new_expert_renews_learning_after_resume() -> None:
    budget = LearningBudget()
    limit, steps = 2, 3
    for _ in range(limit):
        assert budget.available(limit)
        budget.record(steps)
    restored = LearningBudget(**asdict(budget))
    assert not restored.available(limit)
    assert restored.available(None)
    before = restored.optimizer_steps
    restored.renew()
    assert restored.available(limit)
    assert restored.optimizer_steps == before
    restored.record(steps)
    assert restored.optimizer_steps == before + steps
