"""Resolve the experiment into artifact-free native and optimizer controls."""

from kagg_revue.learning.config import Experiment
from kagg_revue.learning.settings import RuntimeSettings


def runtime_settings(config: Experiment) -> RuntimeSettings:
    """Build shared runtime geometry without constructing a BC pipeline profile."""
    scripts = config.script_population if not config.population.sampled_counts else None
    return RuntimeSettings(
        devices=config.execution.devices if config.execution else (config.device,),
        workers=config.execution.workers_per_rank if config.execution else config.workers,
        unit_limit=config.unit_limit,
        width=config.width,
        decision_interval=config.decision_interval,
        quantity_max=config.quantity_max,
        quantity_extra=config.quantity_extra,
        environment=config.environment,
        evaluation_games=config.evaluation.games,
        compile=config.compile,
        sequence_chunk_turns=config.sequence_chunk_turns,
        sequence_games_per_rank=config.sequence_games_per_rank,
        fused_loss=bool(config.execution and config.execution.fused_loss),
        script_population=scripts,
        precision=config.precision,
        bf16_reduced_precision_reduction=False,
        model={  # type: ignore[arg-type]
            "architecture": config.architecture,
            "time_prior": False,
            "prior_scale": 0.0,
            "operation_quantity_bias": config.operation_quantity_bias,
            "market_budget": config.market_budget,
            "agronomy": config.agronomy,
            "derived": config.derived,
            "gated": config.gated,
            "memory_turns": config.memory_turns,
            "memory_width": config.memory_width,
            "memory_layers": config.memory_layers,
            "memory_tokens": config.memory_tokens,
            "joint_units": config.joint_units,
            "depth": config.depth,
            "heads": config.heads,
            "expansion": config.expansion,
            "critic_width": config.critic_width,
            "critic_depth": config.critic_depth,
        },
        ppo={  # type: ignore[arg-type]
            "population": "script_mix" if scripts else "self_play",
            "script_fraction": scripts.fraction if scripts else 0,
            "script_opponents": scripts.agents if scripts else (),
            "ratio_scope": "prefix",
            "prefix_trace_lambda": 1.0,
            "prefix_warmup_updates": 0,
            "updates": config.updates,
            "games_per_update": config.games,
            "batch_rows": config.batch_rows,
            "microbatch_rows": (
                config.execution.microbatch_rows if config.execution else config.microbatch_rows
            ),
            "epochs": config.epochs,
            "actor_learning_rate": config.actor_learning_rate,
            "critic_learning_rate": config.critic_learning_rate,
            "learning_rate_warmup_updates": config.learning_rate_warmup_updates,
            "gamma": config.gamma,
            "gae_lambda": config.gae_lambda,
            "clip": config.clip,
            "target_kl": config.target_kl,
            "bc_weight": 0.0,
            "bc_rows": len(config.execution.devices) if config.execution else 1,
            "entropy_weight": config.entropy_weight,
            "reference_kl_weight": config.reference_kl_weight,
            "cash_weight": config.cash_weight,
            "cash_scale": config.cash_scale,
            "cash_margin": config.cash_margin,
            "win_weight": 1.0,
            "seed_start": config.train_seed,
            "checkpoint_interval": 1,
            "protection": None
            if config.kl_control == "early_stop"
            else {
                "backtrack_attempts": 1,
                "learning_rate_decay": 1.0,
                "skip_constant_returns": True,
            },
        },
    )
