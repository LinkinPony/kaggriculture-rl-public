"""Compare the new core, archived full backend and official complete neural games."""

import tarfile
from pathlib import Path
from typing import Any

import hydra
import numpy as np
import torch
from omegaconf import DictConfig, OmegaConf
from pydantic import Field, model_validator

from kagg_revue.artifacts.io import digest, write_json
from kagg_revue.configuration import FrozenSettings
from kagg_revue.learning.state import load_member, source_identity
from kagg_revue.learning.validation import validated_run
from kagg_revue.native import _revue_core as core
from kagg_revue.native import _revue_native as baseline
from kagg_revue.native.comparison import MirrorReference
from kagg_revue.policy.inference import ActorRuntime


class Qualification(FrozenSettings):
    """A registered new policy, separate audit seeds, and an official interpreter."""

    run: Path
    member: str
    output_dir: Path
    reference_directory: Path
    device: str = "cuda:0"
    seed: int = Field(default=1290000000, ge=0)
    games: int = Field(default=8, ge=2)

    @model_validator(mode="after")
    def validate_paths(self) -> "Qualification":
        """Write only repository results and use persistent external references."""
        for path, prefix in (
            (self.output_dir, ("outputs", "analysis")),
            (self.reference_directory, ("data", "external")),
        ):
            if path.is_absolute() or ".." in path.parts or path.parts[:2] != prefix:
                raise ValueError("native qualification path has the wrong artifact role")
        return self


def _features(batch: Any, shape: tuple[int, int]) -> np.ndarray[Any, Any]:
    result = np.empty(shape, np.float16)
    batch.observe_selfplay_into(result)
    return result


def qualify(config: Qualification) -> None:
    """Require identical buffers, actions, states, replay and repeated-parent forks."""
    experiment, state = validated_run(
        config.run, seed=config.seed, games_per_opponent=2 * config.games, role="selection"
    )
    if core.runtime_kind != "neural-selfplay-only-v1" or hasattr(core, "ParallelBatch"):
        raise ValueError("core must expose only callback-free self-play construction")
    if (
        hasattr(core.SelfPlayBatch, "teacher_into")
        or core.parallel_spec() != baseline.parallel_spec()
    ):
        raise ValueError("core callback boundary or observation specification differs")
    torch.set_num_threads(4)
    torch.cuda.set_device(torch.device(config.device))
    actor, _ = load_member(experiment, state, config.member, torch.device(config.device))
    actor.eval()
    layout = actor.layout
    if layout.network.architecture not in {"grounded-v1", "grounded-v2"} or layout.capacity != 1:
        raise ValueError("this core audit requires a grounded single-turn policy")
    config.output_dir.mkdir(parents=True, exist_ok=False)
    source = source_identity()
    with tarfile.open(config.output_dir / "source.tar.gz", "w:gz") as archive:
        for name in source["files"]:
            archive.add(name, arcname=name, recursive=False)
    seeds = list(range(config.seed, config.seed + config.games))
    common = (experiment.environment, seeds, [0] * config.games)
    tail = (experiment.unit_limit, 4, list(layout.observation.quantities))
    batch = core.SelfPlayBatch(*common, *tail)
    control = baseline.ParallelBatch(*common, [], [], [], *tail)
    engines = [core.Engine(seed, experiment.environment) for seed in seeds]
    reference = MirrorReference(config.reference_directory, experiment.environment, seeds)
    sessions = [
        core.ContractSession(experiment.environment, experiment.unit_limit)
        for _ in range(2 * config.games)
    ]
    runtime = ActorRuntime(actor, 2 * config.games, sample=True, precision=experiment.precision)
    shape = (2 * config.games, layout.observation.features)
    histories: list[list[Any]] = [[] for _ in seeds]
    fork_checks = replay_checks = 0
    torch.manual_seed(config.seed)
    for turn in range(layout.observation.turns):
        observations = reference.observations(engines)
        for row, (observation, session) in enumerate(zip(observations, sessions, strict=True)):
            lane, seat = divmod(row, 2)
            if batch.observation(lane, seat) != engines[lane].observation(seat):
                raise ValueError(f"core batch state differs at {turn}:{row}")
            if control.observation(lane, seat) != batch.observation(lane, seat):
                raise ValueError(f"legacy batch state differs at {turn}:{row}")
            session.update(observation)
            session.observe_into(runtime.host[row : row + 1].numpy())
        expected = runtime.host.numpy()
        if not np.array_equal(_features(batch, shape), expected) or not np.array_equal(
            _features(control, shape), expected
        ):
            raise ValueError(f"core/baseline/public-observation features differ at {turn}")
        runtime.act(turn)
        plans = runtime.selected.numpy()
        actions = []
        for row, session in enumerate(sessions):
            session.set_program(plans[row : row + 1], 1, tail[-1])
            actions.append(session.program_action())
        if turn == min(96, layout.observation.turns // 2):
            replay = core.SelfPlayBatch(*common, *tail)
            replay.replay_prefixes(histories)
            if not np.array_equal(_features(replay, shape), expected):
                raise ValueError("replayed core history differs from continuous self-play")
            for lane in range(config.games):
                for seat in (0, 1):
                    if replay.observation(lane, seat) != batch.observation(lane, seat):
                        raise ValueError("replayed core full state differs")
            replay_checks = config.games
            parents = np.asarray([0, config.games - 1, 0, 1], dtype=np.int64)
            forks: list[Any] = [batch.fork(parents), control.fork(parents)]
            rows = np.asarray([2 * parent + seat for parent in parents for seat in (0, 1)])
            for fork in forks:
                if not np.array_equal(_features(fork, (len(rows), shape[1])), expected[rows]):
                    raise ValueError("forked core/legacy visible history differs")
                fork.advance_programs(np.ascontiguousarray(plans[rows]), 1, 1, True)
            for lane in range(len(parents)):
                for seat in (0, 1):
                    if forks[0].observation(lane, seat) != forks[1].observation(lane, seat):
                        raise ValueError("forked core/legacy next states differ")
            fork_checks = len(parents)
        batch.advance_programs(plans, 1, 1, True)
        control.advance_programs(plans, 1, 1, True)
        for lane, engine in enumerate(engines):
            pair = actions[2 * lane : 2 * lane + 2]
            engine.step(*pair)
            reference.games[lane].step(pair)
            histories[lane].append(pair)
    reference.observations(engines)
    for lane, engine in enumerate(engines):
        for seat in (0, 1):
            if batch.observation(lane, seat) != engine.observation(seat) or (
                control.observation(lane, seat) != batch.observation(lane, seat)
            ):
                raise ValueError("final core/baseline/official states differ")
    if batch.completed_games != config.games or not np.array_equal(batch.cash(), control.cash()):
        raise ValueError("core and baseline did not finish with identical cash")
    if source_identity() != source:
        raise ValueError("qualification source changed during execution")
    write_json(
        config.output_dir / "report.json",
        {
            "configuration": config.model_dump(mode="json"),
            "source": source,
            "source_archive_sha256": digest(config.output_dir / "source.tar.gz"),
            "baseline_native_sha256": digest(Path(baseline.__file__)),
            "checkpoint_sha256": state["members"][config.member],
            "feature_rows_checked": 2 * config.games * layout.observation.turns,
            "forked_lanes_checked": fork_checks,
            "replayed_lanes_checked": replay_checks,
            "official_reference": reference.report(),
            "cash": batch.cash().tolist(),
            "matched": True,
        },
    )


@hydra.main(
    version_base=None,
    config_path=str(Path(__file__).resolve().parents[3] / "configs"),
    config_name="native_core_qualification",
)
def main(configuration: DictConfig) -> None:
    """Resolve the exact model and separately reserved audit seeds."""
    qualify(Qualification.model_validate(OmegaConf.to_container(configuration.audit, resolve=True)))


if __name__ == "__main__":
    main()
