"""Bounded mixed-opponent RL and archive recovery from the latest stopped BC weights."""

import json
import os
from pathlib import Path
from typing import Any

import hydra
import torch
from omegaconf import DictConfig, OmegaConf

from kagg_revue.artifacts.io import digest, write_json
from kagg_revue.learning import state as artifacts
from kagg_revue.learning.collection.verification import official
from kagg_revue.learning.config import Experiment
from kagg_revue.learning.matchmaking.verification import finite, verify
from kagg_revue.learning.performance.artifacts import qualification_copy
from kagg_revue.learning.performance.qualification import _training
from kagg_revue.learning.pretraining import native as native_transition
from kagg_revue.learning.pretraining.handoff import ALLOWED, activate, stopped
from kagg_revue.opponents.artifacts import identity as script_identity


def qualify(config: Experiment, options: DictConfig) -> None:
    """Verify real scripted games, historical inputs, PPO state and a checkpoint restart."""
    assert config.script_population is not None
    source = config.output_dir
    original = stopped(config)
    native_transition.validate(original, Path(options.encoder_qualification))
    identity = artifacts.source_identity()
    source_hash = digest(source / "state.json")
    report = Path(options.qualification)
    official_result = official(
        config,
        original,
        {
            "official_games": 10,
            "official_seed": 4430000000,
            "reference_directory": "data/external/kaggriculture-reference-1.32.7",
            "inference_device": "cuda:0",
        },
    )
    write_json(report.with_name("official.json"), official_result)
    print(json.dumps({"phase": "official_passed"}), flush=True)
    torch.cuda.empty_cache()
    destination = Path(options.qualification_run)
    assert config.execution is not None
    values = config.model_dump(mode="json")
    test = qualification_copy(
        source,
        destination,
        config.execution,
        int(options.updates),
        protocol_changes={key: values[key] for key in ALLOWED - {"execution"}},
        evaluation_games=2,
    )
    test = test.model_copy(update={"checkpoint_interval": 1, "train_seed": 4431000000})
    prepared = json.loads((destination / "state.json").read_text())
    native_transition.install(destination, prepared, Path(options.encoder_qualification))
    # Reuse already staged immutable historical files on this filesystem.
    # activate() still authenticates each source, complete hash and model layout.
    for historical in config.population.sources:
        for checkpoint in historical.checkpoints:
            relative = Path("historical") / historical.run.name / Path(checkpoint).name
            cached = source / relative
            if cached.is_file():
                target = destination / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                os.link(cached, target)
    activate(test, prepared, Path(options.native_qualification))
    write_json(destination / "state.json", prepared)
    write_json(destination / "resolved-config.json", prepared["protocol"])
    print(json.dumps({"phase": "prepared", "external": len(prepared["external_opponents"])}))
    stopped_status = _training(destination, destination / "qualification-stop.log", 1)
    before = json.loads((destination / "state.json").read_text())
    if not 0 < before["completed_update"] < test.updates:
        raise ValueError("qualification did not leave an RL update for archive recovery")
    final_status = _training(
        destination, destination / "qualification-resume.log", None, archived=True
    )
    final = json.loads((destination / "state.json").read_text())
    verification = verify(test, before, final, destination)
    parent = original["members"][original["latest"]]
    updates = []
    for row in final["records"]:
        update = row["update"]
        name = f"checkpoints/update-{update:06d}.pt"
        payload = torch.load(destination / name, map_location="cpu", weights_only=False)
        if (
            digest(destination / name) != final["members"][name]
            or payload["lineage"]["parent_sha256"] != parent
            or not finite(payload)
            or payload["pfsp"] != _pfsp_at(prepared, test, final, update)
        ):
            raise ValueError("RL handoff broke BC ancestry or full checkpoint state")
        parent = final["members"][name]
        for worker in row["workers"]:
            if (
                worker["cash_reward_weight"] != 0
                or worker["win_reward_weight"] != 1
                or not set(worker["reward_values"]) <= {-1.0, 0.0, 1.0}
            ):
                raise ValueError("handoff changed pure terminal WDL rewards")
        if not row["populations"].get("historical_self_play", {}).get("games"):
            raise ValueError("qualification did not sample PFSP history")
        assert config.script_population is not None
        sampled = {n: p["games"] for n, p in row["pfsp"]["scripts"].items() if p["games"]}
        actual = {
            n: row["populations"][n]["games"]
            for n in config.script_population.agents
            if n in row["populations"]
        }
        if not sampled or actual != sampled:
            raise ValueError("qualification script games differ from the PFSP draw")
        updates.append(update)
    if updates != list(range(1, test.updates + 1)):
        raise ValueError("qualification skipped an RL update")
    if final["pretraining"] != original["pretraining"]:
        raise ValueError("RL startup changed the preserved BC state")
    if digest(source / "state.json") != source_hash:
        raise ValueError("qualification modified the stopped source run")
    if artifacts.source_identity()["source_sha256"] != identity["source_sha256"]:
        raise ValueError("source changed during mixed-BC qualification")
    result = {
        "passed": final_status["status"] == "complete",
        "run_id": original["run_id"],
        "source_state_sha256": source_hash,
        "checkpoint_sha256": original["members"][original["latest"]],
        "source_sha256": identity["source_sha256"],
        "native_sha256": identity["native_sha256"],
        "encoder_qualification_sha256": digest(Path(options.encoder_qualification)),
        "native_qualification_sha256": digest(Path(options.native_qualification)),
        "script_runtime": script_identity(config.script_population),
        "protocol": artifacts.protocol(config),
        "qualification_run": str(destination),
        "stopped_status": stopped_status,
        "final_status": final_status,
        "official": official_result,
        "pfsp_verification": verification,
        "bc_state_preserved": True,
        "bc_parent_chain_verified": True,
        "pure_terminal_wdl": True,
        "external_opponents": len(final["external_opponents"]),
        "records": final["records"],
        "cycle_timings": [
            json.loads(line)
            for line in (destination / "cycle-timing.jsonl").read_text().splitlines()
        ],
    }
    write_json(report, result)
    print(json.dumps({"phase": "passed", "report": str(report)}), flush=True)


def _pfsp_at(
    original: dict[str, Any], config: Experiment, final: dict[str, Any], stop: int
) -> dict[str, Any]:
    """Replay every sampled opponent from the BC handoff, including its first update."""
    import copy

    from kagg_revue.learning.matchmaking.scheduler import Matchmaker

    state = copy.deepcopy(original)
    scheduler = Matchmaker(config, state)
    for row in final["records"][:stop]:
        match = scheduler.select(
            row["update"], len(config.execution.devices) if config.execution else 1
        )
        if match.report != row["pfsp"] or match.history != row["opponent"]["path"]:
            raise ValueError("PFSP selection differs from the original handoff state")
        scheduler.observe(match, row["update"], row["populations"])
    return dict(state["pfsp"])


@hydra.main(
    version_base=None,
    config_path="../../../../configs",
    config_name="learning_agronomy_rl_20260917",
)
def main(configuration: DictConfig) -> None:
    """Qualify the actual latest BC on both GPUs before activating its new RL protocol."""
    torch.set_num_threads(2)
    config = Experiment.model_validate(
        OmegaConf.to_container(configuration.experiment, resolve=True)
    )
    qualify(config, configuration.handoff)


if __name__ == "__main__":
    main()
