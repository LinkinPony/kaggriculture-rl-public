"""Run a frozen paired memory ablation without altering training or its ledger."""

import gc
import json
import tarfile
import time
from pathlib import Path
from typing import Any, Literal

import hydra
import numpy as np
import torch
from omegaconf import DictConfig, OmegaConf
from pydantic import Field, model_validator

from kagg_revue.artifacts.io import digest, write_json
from kagg_revue.configuration import FrozenSettings
from kagg_revue.evaluation.games import _complete, _summary
from kagg_revue.evaluation.memory.reporting import report
from kagg_revue.evaluation.memory.runtime import HistoryDuel, HistoryPolicy
from kagg_revue.evaluation.temperature.games import load_games
from kagg_revue.learning.settings import RuntimeSettings
from kagg_revue.learning.state import source_identity
from kagg_revue.native import _revue_core, _revue_native
from kagg_revue.native.batches import create_selfplay_batch
from kagg_revue.opponents.batches import create_batch
from kagg_revue.opponents.portfolios.native import ASSET_SHA256
from kagg_revue.policy.checkpoints import load_policy
from kagg_revue.policy.inference import ActorRuntime
from kagg_revue.policy.memory.policy import MemoryPolicy


class Options(FrozenSettings):
    """Predeclared equal-weight opponent panel and independent direct duel seeds."""

    checkpoint: Path
    checkpoint_sha256: str
    output: Path
    opponents: tuple[str, ...]
    seed: int = Field(ge=0)
    seeds: int = Field(gt=0)
    duel_seed: int = Field(ge=0)
    duel_seeds: int = Field(gt=0)
    sampling_seed: int = Field(ge=0)
    batch_games: int = Field(default=32, gt=0)
    workers: int = Field(default=4, gt=0)
    device: str = "cuda:0"
    precision: Literal["bf16", "fp32"] = "bf16"
    memory_fraction: float = Field(default=0.08, gt=0, le=1)

    @model_validator(mode="after")
    def validate_panel(self) -> "Options":
        """Require complete fixed-shape mirror batches and unique opponents."""
        if self.batch_games % 2 or any(
            2 * count % self.batch_games for count in (self.seeds, self.duel_seeds)
        ):
            raise ValueError("both panels must divide into complete even seat-paired batches")
        if not self.opponents or len(set(self.opponents)) != len(self.opponents):
            raise ValueError("opponents must be nonempty and unique")
        return self


def release(runtime: ActorRuntime) -> None:
    """Release private graph workspaces before switching from panel to duel execution."""
    if runtime.capture is not None:
        runtime.capture.close()


def run(config: Options) -> dict[str, Any]:
    """Authenticate artifacts, finish all scheduled games, and retain per-game evidence."""
    if digest(config.checkpoint) != config.checkpoint_sha256:
        raise ValueError("frozen checkpoint hash mismatch")
    config.output.mkdir(parents=True, exist_ok=True)
    resolved = config.model_dump(mode="json")
    configuration = config.output / "configuration.json"
    if configuration.exists() and json.loads(configuration.read_text()) != resolved:
        raise ValueError("existing evaluation has a different protocol")
    write_json(configuration, resolved)
    identity = source_identity()
    identity["script_native_sha256"] = digest(Path(_revue_native.__file__))
    identity["script_assets"] = {name: ASSET_SHA256[name] for name in config.opponents}
    identity_path = config.output / "source.json"
    if identity_path.exists() and json.loads(identity_path.read_text()) != identity:
        raise ValueError("evaluation source or native runtime changed during resume")
    write_json(identity_path, identity)
    if not (config.output / "source.tar.gz").exists():
        with tarfile.open(config.output / "source.tar.gz", "w:gz") as archive:
            for name in identity["files"]:
                archive.add(name, arcname=name, recursive=False)
    torch.set_num_threads(2)
    device = torch.device(config.device)
    if device.type == "cuda":
        torch.cuda.set_device(device)
        torch.cuda.set_per_process_memory_fraction(config.memory_fraction, device)
    actor, payload = load_policy(config.checkpoint, torch.device("cpu"))
    if not isinstance(actor, MemoryPolicy):
        raise TypeError("the selected actor must have explicit temporal memory")
    settings = RuntimeSettings.model_validate(payload["settings"]).model_copy(
        update={"evaluation_games": config.batch_games, "workers": config.workers}
    )
    update = payload.get("update")
    del payload
    actor.to(device).eval().requires_grad_(False)
    dtype = (
        torch.bfloat16 if device.type == "cuda" and config.precision == "bf16" else torch.float32
    )
    rows = load_games(config.output / "games.jsonl")
    keys = ("mode", "opponent", "seed", "seat")
    completed = {tuple(row[k] for k in keys) for row in rows}
    expected = {
        (mode, name, seed, seat)
        for mode in ("on", "off")
        for name in config.opponents
        for seed in range(config.seed, config.seed + config.seeds)
        for seat in (0, 1)
    } | {
        ("duel", "same_weights_memory_off", seed, seat)
        for seed in range(config.duel_seed, config.duel_seed + config.duel_seeds)
        for seat in (0, 1)
    }
    if len(completed) != len(rows) or not completed <= expected:
        raise ValueError("existing games are duplicated or outside the frozen panel")

    def save_games(result: dict[str, Any], mode: str, rng_seed: int) -> None:
        for row in result["games"]:
            row.update(mode=mode, sampling_seed=rng_seed)
        with (config.output / "games.jsonl").open("a") as stream:
            for row in result["games"]:
                stream.write(json.dumps(row) + "\n")
        rows.extend(result["games"])
        progress = {
            "completed": len(rows),
            "total": len(expected),
            "mode": mode,
            **result["timing"],
        }
        write_json(config.output / "progress.json", progress)
        print(json.dumps(progress), flush=True)

    def done(mode: str, jobs: list[tuple[int, int, str]]) -> bool:
        flags = [(mode, name, seed, seat) in completed for seed, seat, name in jobs]
        if any(flags) and not all(flags):
            raise ValueError("partial batch detected; RNG pairing requires a complete batch")
        return all(flags)

    wrapper = HistoryPolicy(actor, config.batch_games, dtype)
    runtime = ActorRuntime(
        wrapper,
        config.batch_games,
        sample=True,
        temperature=1.0,
        precision=config.precision,
        bf16_reduced_precision_reduction=False,
    )
    qualification: dict[str, Any] = {}
    for name in config.opponents:
        for offset in range(0, 2 * config.seeds, config.batch_games):
            jobs = [
                (config.seed + i // 2, i % 2, name)
                for i in range(offset, offset + config.batch_games)
            ]
            rng_seed = config.sampling_seed + offset
            first_actions = []
            for mode in ("on", "off"):
                if done(mode, jobs):
                    continue
                wrapper.history_enabled.fill_(mode == "on")
                batch = create_batch(settings, jobs)
                # Exercise the actual captured path and check initial-state invariance.
                batch.observe_into(runtime.host.numpy())
                torch.manual_seed(rng_seed)
                runtime.act(0)
                first_actions.append(runtime.selected.clone())
                # Full execution resets state and RNG, so this probe adds no game turns.
                torch.manual_seed(rng_seed)
                cash, timing = _complete(settings, runtime, batch, selfplay=False)
                retained = int((wrapper.execution.state.turns >= 0).sum())
                expected_tokens = actor.layout.network.memory_tokens * (
                    min(settings.turns, actor.layout.network.memory_turns) if mode == "on" else 1
                )
                if retained != expected_tokens:
                    raise RuntimeError(
                        "memory ablation did not retain the intended number of turns"
                    )
                qualification[mode + "_retained_tokens"] = retained
                save_games(_summary(cash, jobs, timing), mode, rng_seed)
            if len(first_actions) == 2 and not torch.equal(*first_actions):
                raise RuntimeError("on/off actions differ with empty history and paired RNG")
    qualification["first_turn_actions_paired"] = True
    qualification["checkpoint_unchanged"] = all(
        torch.equal(tensor.cpu(), value)
        for tensor, value in zip(
            actor.state_dict().values(),
            torch.load(config.checkpoint, map_location="cpu", weights_only=False)["model"].values(),
            strict=True,
        )
    )
    if not qualification["checkpoint_unchanged"]:
        raise RuntimeError("actor parameters changed during evaluation")
    release(runtime)
    del runtime, wrapper
    gc.collect()
    if device.type == "cuda":
        torch.cuda.empty_cache()
    duel = HistoryDuel(actor, config.batch_games, dtype)
    runtime = ActorRuntime(
        duel,
        2 * config.batch_games,
        sample=True,
        temperature=1.0,
        precision=config.precision,
        bf16_reduced_precision_reduction=False,
    )
    for offset in range(0, 2 * config.duel_seeds, config.batch_games):
        jobs = [
            (config.duel_seed + i // 2, i % 2, "same_weights_memory_off")
            for i in range(offset, offset + config.batch_games)
        ]
        if done("duel", jobs):
            continue
        rng_seed = config.sampling_seed + 100000 + offset
        torch.manual_seed(rng_seed)
        batch = create_selfplay_batch(settings, [job[0] for job in jobs])
        cash, timing = _complete(settings, runtime, batch, selfplay=True)
        seats = np.arange(config.batch_games) % 2
        cash = np.where(seats[:, None] == 0, cash, cash[:, ::-1])
        save_games(_summary(cash, jobs, timing), "duel", rng_seed)
    release(runtime)
    if len(rows) != len(expected):
        raise RuntimeError("incomplete memory ablation panel")
    result = {
        "configuration": resolved,
        "update": update,
        "qualification": qualification,
        "native_core_sha256": digest(Path(_revue_core.__file__)),
        "completed_at": time.time(),
        **report(rows, config.opponents),
    }
    write_json(config.output / "report.json", result)
    print(json.dumps(result), flush=True)
    return result


@hydra.main(
    version_base=None,
    config_path=str(Path(__file__).resolve().parents[4] / "configs"),
    config_name="evaluation_memory",
)
def main(configuration: DictConfig) -> None:
    """Resolve the bounded ablation protocol through Hydra."""
    run(Options.model_validate(OmegaConf.to_container(configuration.ablation, resolve=True)))


if __name__ == "__main__":
    main()
