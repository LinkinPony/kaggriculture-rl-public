"""Complete-game execution and paired terminal outcome records."""

import time
from typing import Any

import numpy as np

from kagg_revue.learning.settings import RuntimeSettings
from kagg_revue.policy.inference import ActorRuntime


def _complete(
    settings: RuntimeSettings, runtime: ActorRuntime, batch: Any, *, selfplay: bool
) -> tuple[Any, dict[str, float]]:
    started = time.perf_counter()
    encoding = inference = native = 0.0
    for decision, span in enumerate(runtime.policy.layout.spans):
        phase = time.perf_counter()
        if selfplay:
            batch.observe_selfplay_into(runtime.host.numpy())
        else:
            batch.observe_into(runtime.host.numpy())
        encoding += time.perf_counter() - phase
        phase = time.perf_counter()
        runtime.act(decision)
        inference += time.perf_counter() - phase
        phase = time.perf_counter()
        if runtime.policy.layout.work:
            batch.advance_programs(
                runtime.selected.numpy(), span, runtime.policy.layout.capacity, selfplay
            )
        elif selfplay:
            batch.advance_selfplay(runtime.selected.numpy(), span)
        else:
            batch.advance(runtime.selected.numpy(), span)
        native += time.perf_counter() - phase
    count = settings.evaluation_games
    if batch.completed_games != count or batch.transitions != count * settings.turns:
        raise RuntimeError("panel did not complete every official-rule physical game")
    elapsed = time.perf_counter() - started
    return batch.cash(), {
        "elapsed_seconds": elapsed,
        "physical_games_per_second": count / elapsed,
        "encoding_seconds": encoding,
        "inference_seconds": inference,
        "native_seconds": native,
        "collation_seconds": 0.0,
    }


def _summary(
    cash: Any, jobs: list[tuple[int, int, str]], timing: dict[str, float]
) -> dict[str, Any]:
    outcomes = np.sign(cash[:, 0] - cash[:, 1])
    return {
        "wins": int((outcomes > 0).sum()),
        "ties": int((outcomes == 0).sum()),
        "losses": int((outcomes < 0).sum()),
        "mean_cash": float(cash[:, 0].mean()),
        "median_cash": float(np.median(cash[:, 0])),
        "p10_cash": float(np.quantile(cash[:, 0], 0.1)),
        "mean_cash_difference": float((cash[:, 0] - cash[:, 1]).mean()),
        "games": [
            {
                "seed": seed,
                "seat": seat,
                "opponent": opponent,
                "cash": float(cash[i, 0]),
                "opponent_cash": float(cash[i, 1]),
                "outcome": int(outcomes[i]),
            }
            for i, (seed, seat, opponent) in enumerate(jobs)
        ],
        "timing": timing,
        "sample": False,
        "deployment_budget_qualified": False,
    }
