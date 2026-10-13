"""Full-size integration and recovery checks for protocol or implementation changes."""

import json
from pathlib import Path
from typing import Any

import hydra
import torch
from omegaconf import DictConfig, OmegaConf

from kagg_revue.artifacts.io import digest, write_json
from kagg_revue.learning import state as artifacts
from kagg_revue.learning.collection.verification import official
from kagg_revue.learning.config import Experiment, Population
from kagg_revue.learning.execution import Execution
from kagg_revue.learning.optimization.settings import CashMargin
from kagg_revue.learning.performance.artifacts import qualification_copy
from kagg_revue.learning.performance.qualification import _training
from kagg_revue.learning.recovery.archive import materialize
from kagg_revue.learning.recovery.population import BatchChange, changed_protocol
from kagg_revue.learning.recovery.rewards import margin_protocol, wdl_protocol
from kagg_revue.learning.recovery.selfplay import SelfPlayChange, resolved, sampling_fields
from kagg_revue.opponents.artifacts import identity as script_identity
from kagg_revue.opponents.settings import PublicPopulation


def qualify(change: dict[str, Any], options: dict[str, Any]) -> None:
    """Exercise live scripts and full optimizer continuation without an ablation experiment."""
    source, destination = Path(change["run"]), Path(options["output_dir"])
    original = json.loads((source / "state.json").read_text())
    original_hash = digest(source / "state.json")
    batch = BatchChange.model_validate(change["batch"]) if change.get("batch") else None
    pure = bool(change.get("selfplay"))
    wdl = bool(change.get("wdl"))
    implementation = bool(change.get("implementation"))
    margin = CashMargin.model_validate(change["cash_margin"]) if change.get("cash_margin") else None
    if implementation and any(
        (margin, wdl, pure, batch, change.get("population"), change.get("execution"))
    ):
        raise ValueError("implementation qualification must preserve the entire protocol")
    if margin is not None and (wdl or pure or batch or change.get("population")):
        raise ValueError("cash-margin qualification cannot change sampling or other rewards")
    if wdl and (pure or batch):
        raise ValueError("WDL qualification cannot change sampling or batch controls")
    config = (
        Experiment.model_validate(original["protocol"])
        if implementation
        else margin_protocol(original, margin)
        if margin is not None
        else wdl_protocol(original)
        if wdl
        else resolved(original, SelfPlayChange.model_validate(change))
        if pure
        else changed_protocol(
            original,
            Population.model_validate(change["population"]),
            PublicPopulation.model_validate(change["script_population"]),
            batch,
            Execution.model_validate(change["execution"]) if change.get("execution") else None,
        )
    )
    assert config.execution is not None
    identity = artifacts.source_identity()
    if (implementation or wdl or margin is not None) and identity["native_sha256"] != original[
        "native"
    ]:
        raise ValueError("source or reward changes must preserve the authenticated rule engine")
    if pure or ((wdl or margin is not None) and config.script_population is None):
        if identity["native_sha256"] != original["native"]:
            raise ValueError("self-play tuning must preserve the authenticated rule engine")
        official_result = {
            "scope": "unchanged authenticated rule engine; no frozen training opponents"
        }
    elif batch or (
        config.population.pfsp is not None
        and original.get("script_runtime")
        and config.script_population is not None
        and all(
            original["script_runtime"].get(key) == value
            for key, value in script_identity(config.script_population).items()
        )
    ):
        assert config.script_population is not None
        previous_runtime = original["script_runtime"]
        current_runtime = script_identity(config.script_population)
        if any(previous_runtime.get(key) != value for key, value in current_runtime.items()):
            raise ValueError("batch resizing must preserve the authenticated C++ script runtime")
        official_result = {"scope": "unchanged authenticated rule engine and script runtime"}
    else:
        official_result = official(config, original, options)
        write_json(Path(change["qualification"]).with_name("official.json"), official_result)
        print(json.dumps({"phase": "official", **official_result}), flush=True)
    test = qualification_copy(
        source,
        destination,
        config.execution,
        int(options["updates"]),
        population_changes=None
        if implementation or batch or pure or wdl or margin is not None
        else {
            "population": config.population.model_dump(),
            "script_population": config.script_population.model_dump()
            if config.script_population
            else None,
        },
        batch_changes=batch.model_dump() if batch else None,
        protocol_changes=sampling_fields(config) if pure else None,
        wdl=wdl,
        cash_margin=margin,
        evaluation_games=options.get("evaluation_games"),
    )
    prepared = json.loads((destination / "state.json").read_text())
    short = implementation or pure or wdl or margin is not None
    if int(options["updates"]) < (4 if short else 8):
        raise ValueError("integration must cover multiple checkpoint boundaries and a resume")
    # The qualification copy must itself support the source-archive recovery path.
    isolated = Path("tmp") / destination.name
    isolated.mkdir(parents=True, exist_ok=False)
    try:
        import shutil

        materialize(destination, json.loads((destination / "state.json").read_text()), isolated)
    finally:
        shutil.rmtree(isolated)
    stopped_status = _training(
        destination,
        destination / "qualification-stop.log",
        original["completed_update"] + (1 if short else 3),
    )
    stopped = artifacts.restore(test.model_copy(update={"resume": True}))
    stopped_payload = torch.load(
        destination / stopped["latest"], map_location="cpu", weights_only=False
    )
    required = {"model", "critic", "actor_optimizer", "critic_optimizer", "rng", "lineage"}
    if not required <= stopped_payload.keys():
        raise ValueError("stopped checkpoint lacks complete training state")
    if len(stopped_payload["rng"]["workers"]) != len(config.execution.devices):
        raise ValueError("stopped checkpoint omitted per-rank random streams")
    resumed_status = _training(
        destination, destination / "qualification-resume.log", None, archived=True
    )
    final = artifacts.restore(test.model_copy(update={"resume": True}))
    rows = final["records"][original["completed_update"] :]
    expected_updates = list(range(original["completed_update"] + 1, test.updates + 1))
    if [row["update"] for row in rows] != expected_updates:
        raise ValueError("stop/resume skipped or duplicated a logical update")
    history = int(config.games * config.population.fraction)
    scripts = (
        int(config.games * config.script_population.fraction) if config.script_population else 0
    )
    agents = config.script_population.agents if config.script_population else ()
    expected_counts: dict[str, int] = {
        "self_play": config.games - history - scripts,
        "historical_self_play": history,
        **{name: scripts // len(agents) for name in agents},
    }
    expected_counts = {name: count for name, count in expected_counts.items() if count}
    completed_games = sum(row["physical_games"] for row in original["records"])
    for row in rows:
        if config.cash_margin is not None:
            for worker in row["workers"]:
                if (
                    worker.get("cash_margin_reward") != config.cash_margin.model_dump(mode="json")
                    or worker.get("terminal_reward_max_error") != 0.0
                    or worker["cash_reward_weight"] != 0
                    or worker["win_reward_weight"] != 1
                ):
                    raise ValueError(
                        "cash-margin continuation generated incorrect terminal returns"
                    )
        if wdl:
            for worker in row["workers"]:
                if (
                    worker["cash_reward_weight"] != 0
                    or worker["win_reward_weight"] != 1
                    or not set(worker["reward_values"]) <= {-1.0, 0.0, 1.0}
                ):
                    raise ValueError("WDL continuation generated non-WDL training returns")
        if pure and (row["opponent"] is not None or row["history_score"] is not None):
            raise ValueError("pure self-play recorded a frozen opponent or historical score")
        completed_games += config.games
        if (
            row["physical_games"] != config.games
            or row["cumulative_physical_games"] != completed_games
        ):
            raise ValueError("rollout resizing lost the actual historical physical-game count")
        actual_counts = {name: panel["games"] for name, panel in row["populations"].items()}
        counts = dict(expected_counts)
        if config.population.pfsp is not None:
            counts.update({name: panel["games"] for name, panel in row["pfsp"]["scripts"].items()})
        if config.population.unified:
            from kagg_revue.learning.matchmaking.unified import pooled_games

            frozen = pooled_games(
                config,
                row["update"],
                len(config.execution.devices),
                prepared["pfsp"]["started_update"],
            )
            counts = row["pfsp"]["population_games"]
            if counts["self_play"] != config.games - frozen:
                raise ValueError("unified population fraction differs from cumulative rounding")
        elif config.population.separate_scripts:
            from kagg_revue.learning.matchmaking.separate import game_counts

            history_count, script_count = game_counts(
                config,
                row["update"],
                len(config.execution.devices),
                prepared["pfsp"]["started_update"],
            )
            counts = row["pfsp"]["population_games"]
            if (
                counts["historical_self_play"] != history_count
                or counts["self_play"] != config.games - history_count - script_count
                or sum(
                    n
                    for name, n in counts.items()
                    if name not in {"self_play", "historical_self_play"}
                )
                != script_count
            ):
                raise ValueError("separate populations differ from the cumulative game budgets")
        if actual_counts != counts:
            raise ValueError("training populations differ from the requested physical-game mix")
        expected_trajectories = config.games + counts["self_play"]
        if (
            sum(panel["training_trajectories"] for panel in row["populations"].values())
            != expected_trajectories
        ):
            raise ValueError("frozen opponent actions were counted as learner trajectories")
    parent = original["members"][original["latest"]]
    for update in expected_updates:
        name = artifacts.budget_member(final, update)
        if name not in final["members"]:
            continue
        payload = torch.load(destination / name, map_location="cpu", weights_only=False)
        if payload["lineage"]["parent_sha256"] != parent:
            raise ValueError("population continuation broke checkpoint ancestry")
        parent = final["members"][name]
    if original_hash != digest(source / "state.json"):
        raise ValueError("integration qualification modified the production run")
    if identity["source_sha256"] != artifacts.source_identity()["source_sha256"]:
        raise ValueError("source changed while qualifying the population transition")
    pfsp_verification = None
    if config.population.pfsp is not None:
        from kagg_revue.learning.matchmaking.verification import verify

        pfsp_verification = verify(test, prepared, final, destination)
    write_json(
        Path(change["qualification"]),
        {
            "passed": resumed_status["status"] == "complete",
            "run_id": original["run_id"],
            "completed_update": original["completed_update"],
            "checkpoint_sha256": original["members"][original["latest"]],
            "source_state_sha256": original_hash,
            "source_sha256": identity["source_sha256"],
            "previous_source": original["source"],
            "native_sha256": identity["native_sha256"],
            "script_runtime": script_identity(config.script_population)
            if config.script_population
            else None,
            "protocol": artifacts.protocol(config),
            "official": official_result,
            "qualification_run": str(destination),
            "stopped": stopped_status,
            "resumed": resumed_status,
            "full_optimizer_rng_and_parent_chain": True,
            "archived_source_recovery": True,
            "source_run_unchanged": True,
            "wdl_returns_verified": wdl,
            "cash_margin_returns_verified": config.cash_margin is not None,
            "expected_populations": expected_counts,
            "records": rows,
            "pfsp_verification": pfsp_verification,
            "external_opponents": final.get("external_opponents", {}),
            "scope": "integration and continuation qualification only; no ablation",
        },
    )
    print(json.dumps({"phase": "passed", "report": change["qualification"]}), flush=True)


@hydra.main(
    version_base=None,
    config_path=str(Path(__file__).resolve().parents[4] / "configs"),
    config_name="learning_population_change",
)
def main(configuration: DictConfig) -> None:
    """Resolve a short integration check before changing a long-running experiment."""
    change = OmegaConf.to_container(configuration.change, resolve=True)
    options = OmegaConf.to_container(configuration.qualification, resolve=True)
    assert isinstance(change, dict) and isinstance(options, dict)
    qualify(change, options)  # type: ignore[arg-type]


if __name__ == "__main__":
    main()
