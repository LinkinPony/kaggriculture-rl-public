"""Archive an explicitly requested latest-BC handoff to the existing neural PPO pool."""

import fcntl
import json
import shutil
import time
from typing import Any

import hydra
import torch
from omegaconf import DictConfig, OmegaConf

from kagg_revue.artifacts.io import digest, write_json
from kagg_revue.learning import state as artifacts
from kagg_revue.learning.config import Experiment
from kagg_revue.learning.performance.artifacts import archive_source
from kagg_revue.learning.pretraining.handoff import stopped


def commit(config: Experiment) -> dict[str, Any]:
    """Preserve the BC weights, Adam and lineage while registering fresh PPO optimizers."""
    directory = config.output_dir
    with (directory / "run.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        state = stopped(config)
        original = Experiment.model_validate(state["protocol"])
        if (
            config.memory_turns
            or config.population != original.population
            or config.population.sources
            or config.script_population is not None
            or original.script_population is not None
        ):
            raise ValueError("neural BC handoff must preserve the stateless model and own-run pool")
        identity = artifacts.source_identity()
        if identity["native_sha256"] != state["native"]:
            raise ValueError("BC handoff must preserve the native environment")
        selected = state["latest"]
        revision = directory / "bc-completion" / "0001"
        revision.mkdir(parents=True, exist_ok=False)
        write_json(revision / "previous-state.json", state)
        archive_source(revision, identity)
        backup = revision / "bc-final.pt"
        shutil.copy2(artifacts.member_path(original, state, selected), backup)
        if digest(backup) != state["members"][selected]:
            raise ValueError("BC boundary backup differs from the authenticated checkpoint")
        event = {
            "time": time.time(),
            "reason": "explicit_user_stop_bc_start_dual_gpu_ppo_with_warmup_and_gae",
            "checkpoint": selected,
            "checkpoint_sha256": state["members"][selected],
            "pretraining": state["pretraining"],
            "previous_source": state["source"],
            "source": identity["source_sha256"],
            "previous_protocol": state["protocol"],
            "protocol": artifacts.protocol(config),
            "revision": str(revision.relative_to(directory)),
            "effective_from_update": 1,
            "actor_optimizer": "fresh PPO AdamW; original BC Adam retained in bc-final.pt",
            "critic": "same frozen architecture, fresh random initialization and AdamW",
            "warmup": {
                "updates": config.learning_rate_warmup_updates,
                "scope": "both optimizers, absolute PPO update, linear ramp to configured rate",
            },
            "gae_scope": "one gamma/lambda transition per game turn, zero terminal bootstrap",
        }
        state.update(
            rl_initial=selected,
            bc_final=selected,
            pool=[selected],
            source=identity["source_sha256"],
            source_directory=str(revision.relative_to(directory)),
            protocol=artifacts.protocol(config),
            bc_completion=event,
        )
        write_json(revision / "transition.json", event)
        artifacts.write_ledger(directory, state)
        write_json(directory / "resolved-config.json", state["protocol"])
        return event


@hydra.main(
    version_base=None,
    config_path="../../../../configs",
    config_name="learning_compact_ppo_20260921",
)
def main(configuration: DictConfig) -> None:
    """Commit the stopped same-run BC boundary before archived-source PPO recovery."""
    torch.set_num_threads(2)
    config = Experiment.model_validate(
        OmegaConf.to_container(configuration.experiment, resolve=True)
    )
    event = commit(config)
    print(json.dumps({"phase": "bc_to_ppo", "checkpoint": event["checkpoint"]}), flush=True)


if __name__ == "__main__":
    main()
