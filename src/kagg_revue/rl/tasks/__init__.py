"""Terminal-WDL learning for actor-owned unit task tapes."""

from kagg_revue.rl.tasks.checkpoint import (
    TASK_CHECKPOINT_VERSION,
    TASK_RNG_VERSION,
    TaskCheckpointStore,
    capture_task_rng_state,
    load_task_checkpoint,
    restore_task_rng_state,
    save_task_checkpoint,
)
from kagg_revue.rl.tasks.config import (
    TaskIncumbentSettings,
    TaskRlAppSettings,
    TaskRlSettings,
)
from kagg_revue.rl.tasks.data import (
    TaskDecisionBatch,
    TaskDecisionRecord,
    TaskTapeBatch,
    TaskTapeEpisode,
    collate_task_episodes,
    collate_task_records,
    records_from_trace,
    save_task_records,
)
from kagg_revue.rl.tasks.evaluate import evaluate_task_tape
from kagg_revue.rl.tasks.initialization import initialize_task_model
from kagg_revue.rl.tasks.learning import TaskUpdateMetrics, optimize_task_batch
from kagg_revue.rl.tasks.model import TaskTapeActorCritic, TaskTapeEvaluation
from kagg_revue.rl.tasks.objective import (
    AdvantageReference,
    TapePpoLoss,
    TerminalAdvantages,
    market_ppo_loss,
    market_terminal_advantages,
    task_ppo_loss,
    task_terminal_advantages,
)
from kagg_revue.rl.tasks.replay import (
    TapeAudit,
    UnitTraceStep,
    compress_unit_trace,
    expand_task_tape,
)
from kagg_revue.rl.tasks.rollout import (
    TaskRolloutCollector,
    TaskRolloutReport,
    task_rollout_jobs,
)
from kagg_revue.rl.tasks.runtime import TaskTapeAgent

__all__ = [
    "TASK_CHECKPOINT_VERSION",
    "TASK_RNG_VERSION",
    "AdvantageReference",
    "TapeAudit",
    "TapePpoLoss",
    "TaskDecisionBatch",
    "TaskDecisionRecord",
    "TaskCheckpointStore",
    "TaskIncumbentSettings",
    "TaskRlAppSettings",
    "TaskRlSettings",
    "TaskRolloutCollector",
    "TaskRolloutReport",
    "TaskTapeActorCritic",
    "TaskTapeAgent",
    "TaskTapeBatch",
    "TaskTapeEpisode",
    "TaskTapeEvaluation",
    "TaskUpdateMetrics",
    "TerminalAdvantages",
    "UnitTraceStep",
    "collate_task_episodes",
    "collate_task_records",
    "compress_unit_trace",
    "expand_task_tape",
    "evaluate_task_tape",
    "initialize_task_model",
    "capture_task_rng_state",
    "load_task_checkpoint",
    "market_ppo_loss",
    "market_terminal_advantages",
    "optimize_task_batch",
    "records_from_trace",
    "save_task_checkpoint",
    "save_task_records",
    "restore_task_rng_state",
    "task_ppo_loss",
    "task_terminal_advantages",
    "task_rollout_jobs",
]
