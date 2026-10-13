"""Native source-policy opponents for explicitly configured training populations."""

from typing import Any

from kagg_revue.learning.settings import RuntimeSettings
from kagg_revue.native import _revue_native
from kagg_revue.native.batches import Job


def create_batch(settings: RuntimeSettings, jobs: list[Job], *, teacher: bool = False) -> Any:
    """Construct owners once; native calls release the GIL for the complete batch."""
    from kagg_revue.opponents.native_batch import create_native_opponent_session

    maximum_orders = int(settings.environment["maxMarketOrdersPerTurn"])
    opponents = [
        None if name == "pass" else create_native_opponent_session(name, maximum_orders)
        for _, _, name in jobs
    ]
    teachers = []
    if teacher:
        from kagg_revue.opponents.kaito.native import create_native_session

        teachers = [create_native_session(maximum_orders) for _ in jobs]
    return _revue_native.ParallelBatch(
        settings.environment,
        [seed for seed, _, _ in jobs],
        [seat for _, seat, _ in jobs],
        [name for _, _, name in jobs],
        opponents,
        teachers,
        settings.unit_limit,
        settings.workers,
        list(settings.quantities),
    )
