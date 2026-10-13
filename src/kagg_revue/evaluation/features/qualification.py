"""Qualify the native v5b extension and strict migration of real recurrent weights."""

import gzip
import importlib.util
import json
from dataclasses import replace
from pathlib import Path
from typing import Any

import hydra
import numpy as np
import torch
from omegaconf import DictConfig, OmegaConf
from torch import Tensor

from kagg_revue.artifacts.io import digest, write_json
from kagg_revue.configuration import FrozenSettings
from kagg_revue.datasets.demonstrations.encoding import encode
from kagg_revue.datasets.observations import ReplayObservations
from kagg_revue.evaluation.features.compatibility import same_memory
from kagg_revue.learning.sequences.critic import MemoryCritic
from kagg_revue.native import _revue_core as native
from kagg_revue.native.derived import VERSION
from kagg_revue.policy.checkpoints import load_policy
from kagg_revue.policy.contracts import ContractLayout
from kagg_revue.policy.grounded.encoder import ContextEncoder
from kagg_revue.policy.grounded.migration import copy_parameters, migrate_policy
from kagg_revue.policy.memory.policy import MemoryPolicy


class Qualification(FrozenSettings):
    """Pin source artifacts and CPU/GPU equivalence checks; no ablations or fitting."""

    checkpoint: Path
    checkpoint_sha256: str
    native: Path
    native_sha256: str
    replay: Path
    replay_sha256: str
    output: Path
    threads: int = 2
    chunk: int = 16


def _observations(config: Qualification, layout: ContractLayout) -> tuple[Tensor, Tensor]:
    replay = json.loads(gzip.decompress(config.replay.read_bytes()))
    expanded, _, _, _ = encode(replay, layout)
    spec = importlib.util.spec_from_file_location("_revue_observation", config.native)
    if spec is None or spec.loader is None:
        raise ValueError("certified v4 encoder cannot be loaded")
    certified = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(certified)
    # Use the exact same insertion-order reconstruction as BC preparation.
    sequences = [ReplayObservations(), ReplayObservations()]
    normalized = [
        [
            {**state, "observation": sequences[seat].update(state["observation"], turn)}
            for seat, state in enumerate(pair)
        ]
        for turn, pair in enumerate(replay["steps"])
    ]
    base = layout.observation
    old = np.empty((2, base.turns, base.features - base.derived_features), np.float16)
    for seat in (0, 1):
        session = certified.ContractSession(replay["configuration"], base.units)
        for turn, pair in enumerate(normalized[:-1]):
            session.update(pair[seat]["observation"])
            session.observe_into(old[seat, turn : turn + 1])
    old = old.transpose(1, 0, 2).copy()
    prefix = old.shape[-1] - base.support_features
    np.testing.assert_array_equal(old[..., :prefix], expanded[..., :prefix])
    np.testing.assert_array_equal(old[..., prefix:], expanded[..., -base.support_features :])
    if not np.isfinite(expanded).all():
        raise ValueError("nonfinite native v5b replay features")
    return torch.from_numpy(old), torch.from_numpy(expanded)


def _compare(
    actors: tuple[MemoryPolicy, MemoryPolicy],
    critics: tuple[MemoryCritic, MemoryCritic],
    observations: tuple[Tensor, Tensor],
    steps: Tensor,
    actor_states: list[Any],
    critic_states: list[Any],
) -> dict[str, Any]:
    actions, logits, memory = [], [], []
    values, prefixes, memories = [], [], []
    fields = []
    for index in range(2):
        selected, scores, updated = actors[index].sequence(
            observations[index], steps, actor_states[index]
        )
        weight = actors[index].field_weights(
            selected.flatten(0, 1), steps, observations[index].flatten(0, 1)
        )[:, None]
        value, prefix, critic_memory = critics[index].sequence(
            observations[index], steps, critic_states[index], selected, weight
        )
        actions.append(selected)
        logits.append(scores)
        memory.append(updated)
        fields.append(weight)
        values.append(value)
        prefixes.append(prefix)
        memories.append(critic_memory)
    checks = {
        "actions": torch.equal(*actions),
        "logits": torch.equal(*logits),
        "fields": torch.equal(*fields),
        "actor_memory": same_memory(*memory),
        "critic_values": torch.equal(*values),
        "critic_prefixes": torch.equal(*prefixes),
        "critic_memory": same_memory(*memories),
    }
    if not all(checks.values()):
        raise ValueError(f"migration changed model outputs at turn {steps[0]}: {checks}")
    actor_states[:] = memory
    critic_states[:] = memories
    return {
        "start": int(steps[0]),
        "length": len(steps),
        "equal": checks,
        "retained_history_turns": int((memory[0].turns >= 0).sum()) // 4,
    }


def run(config: Qualification) -> dict[str, Any]:
    """Require exact FP32/BF16 outputs, full memory, and nonzero new-branch gradients."""
    for name in ("checkpoint", "native", "replay"):
        if digest(getattr(config, name)) != getattr(config, f"{name}_sha256"):
            raise ValueError(f"{name} identity changed")
    torch.set_num_threads(config.threads)
    actor, payload = load_policy(config.checkpoint, torch.device("cpu"))
    assert isinstance(actor, MemoryPolicy)
    layout = replace(
        actor.layout,
        observation=replace(
            actor.layout.observation,
            version=VERSION,
            derived_global_features=24,
            derived_board_features=20,
            derived_unit_features=16,
            derived_product_features=96,
        ),
        network=replace(actor.layout.network, derived=True),
    )
    expanded, actor_transfer = migrate_policy(actor, layout)
    assert isinstance(expanded, MemoryPolicy)
    critic, new_critic = MemoryCritic(actor.layout), MemoryCritic(layout)
    critic.load_state_dict(payload["critic"], strict=True)
    critic_transfer = copy_parameters(critic, new_critic, "entity_encoder")
    rows = _observations(config, layout)
    actors, critics = (actor, expanded), (critic, new_critic)
    for model in (*actors, *critics):
        model.eval().requires_grad_(False)
    results = {}
    for name, device, spans in (
        ("cpu_fp32", torch.device("cpu"), [(i, 8) for i in (0, 210, 430, 711)]),
        (
            "cuda_bf16",
            torch.device("cuda:0"),
            [(i, min(config.chunk, 719 - i)) for i in range(0, 719, config.chunk)],
        ),
    ):
        for model in (*actors, *critics):
            model.to(device)
        actor_states = [model.memory.temporal.empty(1, device) for model in actors]
        critic_states = [model.memory.temporal.empty(1, device) for model in critics]
        records = []
        with (
            torch.no_grad(),
            torch.autocast(device.type, dtype=torch.bfloat16, enabled=device.type == "cuda"),
        ):
            for start, length in spans:
                if device.type == "cpu":
                    actor_states = [model.memory.temporal.empty(1, device) for model in actors]
                    critic_states = [model.memory.temporal.empty(1, device) for model in critics]
                data = (
                    rows[0][start : start + length, :1].to(device),
                    rows[1][start : start + length, :1].to(device),
                )
                record = _compare(
                    actors,
                    critics,
                    data,
                    torch.arange(start, start + length, device=device),
                    actor_states,
                    critic_states,
                )
                records.append(record)
                if start % 128 == 0:
                    print(
                        json.dumps({"qualification": name, "turn": start, "equal": True}),
                        flush=True,
                    )
        results[name] = records
    if results["cuda_bf16"][-1]["retained_history_turns"] != layout.network.memory_turns:
        raise ValueError("full recurrent memory was not exercised")
    expanded.cpu()
    assert isinstance(expanded.encoder, ContextEncoder)
    assert expanded.encoder.supplement is not None
    expanded.encoder.supplement.requires_grad_(True)
    _, logits, _ = expanded.sequence(
        rows[1][210:211, :1],
        torch.tensor([210]),
        expanded.memory.temporal.empty(1, torch.device("cpu")),
    )
    logits.log_softmax(-1).amax(-1).mean().backward()  # type: ignore[no-untyped-call]
    gradients = {}
    for name, parameter in expanded.encoder.supplement.named_parameters():
        if (
            parameter.grad is None
            or not bool(torch.isfinite(parameter.grad).all())
            or not bool(parameter.grad.any())
        ):
            raise ValueError(f"supplement gradient missing or nonfinite: {name}")
        gradients[name] = float(parameter.grad.norm())
    report = {
        "passed": True,
        "scope": "Actual native features and actor/critic migration; exact CPU FP32 and "
        "complete-season CUDA BF16 equivalence; no training or ablation.",
        "inputs": config.model_dump(mode="json"),
        "checkpoint_update": payload["update"],
        "target_native_sha256": digest(Path(native.__file__)),
        "legacy_observation_features": actor.layout.observation.features,
        "target_observation_features": layout.observation.features,
        "supplementary_features": layout.observation.derived_features,
        "native_legacy_rows_identical": len(rows[0]) * 2,
        "actor_transfer": actor_transfer,
        "critic_transfer": critic_transfer,
        "checks": results,
        "supplement_gradient_norms": gradients,
    }
    write_json(config.output, report)
    return report


@hydra.main(
    version_base=None,
    config_path="../../../../configs",
    config_name="features_v5b_qualification_20260925",
)
def main(configuration: DictConfig) -> None:
    """Check the pinned production migration before a new BC root is created."""
    config = Qualification.model_validate(OmegaConf.to_container(configuration, resolve=True))
    run(config)
    print(json.dumps({"passed": True, "output": str(config.output)}), flush=True)


if __name__ == "__main__":
    main()
