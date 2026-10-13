"""Recoverable policy-space optimization with direct WDL validation before adoption."""

import json
import os
import shutil
import time
from pathlib import Path
from typing import Any

import hydra
import torch
import torch.distributed as dist
import torch.multiprocessing as mp
from omegaconf import DictConfig, OmegaConf

from kagg_revue.artifacts.io import digest, write_json
from kagg_revue.evaluation.neural import NeuralMatches
from kagg_revue.policy.checkpoints import load_policy, save_policy
from kagg_revue.policy.contracts import ContractLayout
from kagg_revue.policy.spatial.model import Policy
from kagg_revue.production.artifacts import provenance
from kagg_revue.production.evaluation.matches import ScriptMatches
from kagg_revue.production.expert.config import EvolutionSettings
from kagg_revue.production.expert.generation import propose_generation
from kagg_revue.production.expert.mutations import ParameterSearch, readout_parameters
from kagg_revue.production.expert.selection import select_generation
from kagg_revue.production.expert.telemetry import generation_summary, progress
from kagg_revue.production.reporting import evaluation_report, retain_checkpoints
from kagg_revue.production.train import _gather


def _restore(policy: Policy, path: Path) -> dict[str, Any]:
    loaded, saved = load_policy(path, torch.device("cpu"))
    policy.load_state_dict(loaded.state_dict())
    return saved


def _rank(rank: int, resolved: dict[str, Any], rendezvous: str) -> None:
    config = EvolutionSettings.model_validate(resolved)
    p = config.production
    world = len(p.devices)
    device = torch.device(p.devices[rank])
    torch.cuda.set_device(device)
    torch.set_num_threads(p.cpu_threads)
    if world > 1:
        dist.init_process_group(
            "nccl", init_method=rendezvous, rank=rank, world_size=world, device_id=device
        )
    torch.manual_seed(p.seed + rank)
    directory = p.output_dir
    latest_path = directory / "checkpoints/latest.json"
    latest = json.loads(latest_path.read_text()) if latest_path.exists() else None
    assert p.checkpoint is not None
    checkpoint = Path(latest["path"]) if latest else p.checkpoint
    loaded, saved = load_policy(checkpoint, torch.device("cpu"))
    policy = loaded.to(device).eval().requires_grad_(False)
    if policy.layout != ContractLayout.resolve(p):
        raise ValueError("resolved policy-search architecture differs from its checkpoint")
    generation = int(saved["generation"]) if latest else 0
    if latest:
        previous, current = dict(saved["evolution_configuration"]), dict(resolved)
        previous.pop("generations")
        current.pop("generations")
        if previous != current:
            raise ValueError(
                "changed policy-search experiments require an isolated output directory"
            )
    del saved, loaded
    parent = Policy.from_layout(policy.layout).to(device).eval().requires_grad_(False)
    parent.load_state_dict(policy.state_dict())
    scripts = ScriptMatches(p, policy)
    neural = NeuralMatches(p, policy, parent)
    mutation = ParameterSearch(readout_parameters(policy))
    reference = None
    if rank == 0:
        opponent, unused = load_policy(config.reference, torch.device("cpu"))
        del unused
        reference = NeuralMatches(p, policy, opponent.to(device).eval().requires_grad_(False))
    source = json.loads((directory / "source.json").read_text())
    first_generation = True
    while generation < config.generations:
        generation += 1
        started = time.perf_counter()
        torch.cuda.reset_peak_memory_stats(device)
        parent.load_state_dict(policy.state_dict())
        mutation.recenter()
        local = propose_generation(config, policy, mutation, scripts, neural, rank, generation)
        local["cold_capture_seconds"] = (
            (
                scripts.runtime.capture_seconds
                + neural.runtime.capture_seconds
                + (reference.runtime.capture_seconds if reference else 0)
            )
            if first_generation
            else 0
        )
        ranks = _gather(local, world)
        if rank == 0:
            assert reference is not None
            phase = time.perf_counter()
            finalists = sorted(
                (candidate for record in ranks for candidate in record["finalists"]),
                key=lambda candidate: (-candidate["fitness"], candidate["candidate"]),
            )[: config.finalists]
            selected = select_generation(
                config, policy, parent, scripts, reference, finalists, generation
            )
            selection_seconds = time.perf_counter() - phase
            previous_checkpoint = checkpoint
            checkpoint = directory / "checkpoints" / f"update-{generation:06d}.pt"
            progress(directory, generation, rank, "checkpoint", 0, 1)
            phase = time.perf_counter()
            save_policy(
                checkpoint,
                policy,
                p,
                generation=generation,
                training_phase="policy_search",
                evolution_configuration=resolved,
                provenance=source,
                optimizer={
                    "kind": "elitist_parameter_search",
                    "generation": generation,
                    "parent": str(previous_checkpoint),
                    "parent_sha256": digest(previous_checkpoint),
                    "accepted": selected["selected"],
                },
                rng={"mutation_seed": config.mutation_seed, "generation": generation},
            )
            identity = {"path": str(checkpoint), "sha256": digest(checkpoint), "update": generation}
            write_json(latest_path, identity)
            selection_path = directory / "selection" / f"generation-{generation:06d}.json"
            write_json(selection_path, selected)
            evaluation_report(
                p,
                {f"selection generation {generation}": selected["scripts"]},
                source,
                checkpoint=checkpoint,
                seed=selected["seed_start"],
            )
            checkpoint_seconds = time.perf_counter() - phase
            total_games = (
                sum(record["physical_games"] for record in ranks) + selected["physical_games"]
            )
            elapsed = time.perf_counter() - started
            record = {
                "generation": generation,
                "timestamp": time.time(),
                "policy_search": generation_summary(ranks, selected),
                "checkpoint": identity,
                "source_revision": source["revision"],
                "optimizer_steps": 1,
                "accepted_policy_update": selected["selected"] is not None,
                "parent": str(previous_checkpoint),
                "parent_sha256": digest(previous_checkpoint),
                "ranks": ranks,
                "selection": str(selection_path),
                "paired_scripts": selected["paired_scripts"],
                "paired_neural": selected["paired_neural"],
                "timing": {
                    "generation_seconds": elapsed,
                    "selection_seconds": selection_seconds,
                    "checkpoint_seconds": checkpoint_seconds,
                    "physical_games": total_games,
                    "physical_games_per_second": total_games / elapsed,
                },
            }
            write_json(directory / "generations" / f"generation-{generation:06d}.json", record)
            with (directory / "metrics.jsonl").open("a") as stream:
                stream.write(
                    json.dumps({key: value for key, value in record.items() if key != "ranks"})
                    + "\n"
                )
            print(
                json.dumps({key: value for key, value in record.items() if key != "ranks"}),
                flush=True,
            )
            retain_checkpoints(checkpoint.parent, config.retain_generations)
            old = (
                directory
                / "candidates"
                / f"generation-{generation - config.retain_generations:06d}"
            )
            if old.exists():
                shutil.rmtree(old)
            progress(directory, generation, rank, "complete", 1, 1)
        if world > 1:
            dist.barrier()
        if rank != 0:
            latest = json.loads(latest_path.read_text())
            checkpoint = Path(latest["path"])
            _restore(policy, checkpoint)
        first_generation = False
    if world > 1:
        dist.destroy_process_group()


def launch(config: EvolutionSettings) -> None:
    """Preserve the initial/reference identities and resume completed optimizer generations."""
    p = config.production
    assert p.checkpoint is not None
    directory = p.output_dir
    directory.mkdir(parents=True, exist_ok=True)
    source = provenance(p)
    if not source["clean"]:
        raise ValueError("policy-search training requires a clean source revision")
    inputs = {
        "initial": {"path": str(p.checkpoint), "sha256": digest(p.checkpoint)},
        "reference": {"path": str(config.reference), "sha256": digest(config.reference)},
    }
    if (directory / "inputs.json").exists() and json.loads(
        (directory / "inputs.json").read_text()
    ) != inputs:
        raise ValueError("the frozen experiment inputs changed on resume")
    write_json(directory / "inputs.json", inputs)
    write_json(directory / "source.json", source)
    write_json(directory / "sources" / f"{source['revision']}.json", source)
    write_json(directory / "resolved-config.json", config.model_dump(mode="json"))
    status = directory / "run-status.json"
    write_json(status, {"status": "running", "pid": os.getpid(), "started_at": time.time()})
    rendezvous = (Path("tmp/parallel-policy") / f"evolution-{time.time_ns()}").resolve()
    rendezvous.parent.mkdir(parents=True, exist_ok=True)
    try:
        mp.spawn(  # type: ignore[attr-defined, no-untyped-call]
            _rank,
            args=(config.model_dump(mode="json"), rendezvous.as_uri()),
            nprocs=len(p.devices),
            join=True,
        )
        write_json(status, {"status": "completed", "pid": os.getpid(), "ended_at": time.time()})
    except BaseException:
        write_json(status, {"status": "failed", "pid": os.getpid(), "ended_at": time.time()})
        raise
    finally:
        rendezvous.unlink(missing_ok=True)


@hydra.main(
    version_base=None, config_path="../../../../configs", config_name="production_evolution"
)
def main(configuration: DictConfig) -> None:
    """Resolve the exact production profile before starting any optimizer work."""
    launch(EvolutionSettings.model_validate(OmegaConf.to_container(configuration, resolve=True)))


if __name__ == "__main__":
    main()
