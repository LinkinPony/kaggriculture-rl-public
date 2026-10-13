from __future__ import annotations

import random
from pathlib import Path

import numpy as np
import pytest
import torch

from kagg_revue.policy.capability import CapabilitySelector, CapabilitySelectorArchitecture
from kagg_revue.rl.capabilities.checkpoint import (
    build_capability_checkpoint,
    capture_capability_rng_state,
    restore_capability_checkpoint,
)
from kagg_revue.rl.capabilities.contract import CapabilityVersionContract


class _SyntheticVersions:
    @staticmethod
    def contract() -> CapabilityVersionContract:
        return CapabilityVersionContract(
            proposal_version="synthetic-proposal",
            search_version="synthetic-search",
            executor_version="synthetic-executor",
        )


class _SyntheticSettings:
    updates = 7
    versions = _SyntheticVersions()
    devices: tuple[str, ...] = ()

    @staticmethod
    def checkpoint_contract() -> dict[str, object]:
        return {"objective": "synthetic-terminal-outcome"}


def _selector() -> CapabilitySelector:
    return CapabilitySelector(
        CapabilitySelectorArchitecture(
            state_width=6,
            model_width=8,
            feedforward_width=12,
            mode_tokens=3,
            integer_vocab_sizes=(5, 4),
            edit_value_features=2,
            candidate_features=3,
            search_features=0,
        )
    )


def _random_streams() -> tuple[
    random.Random,
    np.random.Generator,
    dict[str, torch.Generator],
]:
    return (
        random.Random(11),
        np.random.default_rng(13),
        {
            "proposal": torch.Generator().manual_seed(17),
            "selector": torch.Generator().manual_seed(19),
        },
    )


def _sample_streams(
    randomizer: random.Random,
    numpy_generator: np.random.Generator,
    generators: dict[str, torch.Generator],
) -> tuple[float, ...]:
    return (
        random.random(),
        float(np.random.random()),
        float(torch.rand(()).item()),
        randomizer.random(),
        float(numpy_generator.random()),
        float(torch.rand((), generator=generators["proposal"]).item()),
        float(torch.rand((), generator=generators["selector"]).item()),
    )


def test_capability_checkpoint_restores_complete_endpoint(tmp_path: Path) -> None:
    random.seed(2)
    np.random.seed(3)
    torch.manual_seed(5)
    model = _selector()
    target = _selector()
    target.load_state_dict(model.state_dict())
    optimizer = torch.optim.AdamW(model.parameters(), lr=0.01)
    optimizer.zero_grad(set_to_none=True)
    sum(parameter.square().sum() for parameter in model.parameters()).backward()
    optimizer.step()
    expected_model = {name: value.detach().clone() for name, value in model.state_dict().items()}
    expected_target = {name: value.detach().clone() for name, value in target.state_dict().items()}
    randomizer, numpy_generator, generators = _random_streams()
    rng_state = capture_capability_rng_state(randomizer, numpy_generator, generators)
    payload = build_capability_checkpoint(
        model,
        target,
        optimizer,
        completed_update=2,
        target_update=1,
        settings=_SyntheticSettings(),  # type: ignore[arg-type]
        source_revision="a" * 40,
        artifact_identities={"population": "synthetic-population"},
        rng_state=rng_state,
    )
    checkpoint = tmp_path / "checkpoint.pt"
    torch.save(payload, checkpoint)
    expected_random = _sample_streams(randomizer, numpy_generator, generators)

    for parameter in model.parameters():
        parameter.data.zero_()
    for parameter in target.parameters():
        parameter.data.fill_(1.0)
    random.seed(23)
    np.random.seed(29)
    torch.manual_seed(31)
    randomizer, numpy_generator, generators = _random_streams()
    resume = restore_capability_checkpoint(
        checkpoint,
        model,
        target,
        optimizer,
        _SyntheticSettings(),  # type: ignore[arg-type]
        source_revision="a" * 40,
        artifact_identities={"population": "synthetic-population"},
        randomizer=randomizer,
        numpy_generator=numpy_generator,
        torch_generators=generators,
    )

    assert resume.start_update == 3
    assert resume.target_update == 1
    assert all(
        torch.equal(model.state_dict()[name], value) for name, value in expected_model.items()
    )
    assert all(
        torch.equal(target.state_dict()[name], value) for name, value in expected_target.items()
    )
    assert optimizer.state
    assert _sample_streams(randomizer, numpy_generator, generators) == expected_random


def test_capability_checkpoint_rejects_missing_target_state(tmp_path: Path) -> None:
    model = _selector()
    target = _selector()
    optimizer = torch.optim.AdamW(model.parameters())
    randomizer, numpy_generator, generators = _random_streams()
    payload = build_capability_checkpoint(
        model,
        target,
        optimizer,
        completed_update=0,
        target_update=0,
        settings=_SyntheticSettings(),  # type: ignore[arg-type]
        source_revision="b" * 40,
        artifact_identities={"population": "synthetic-population"},
        rng_state=capture_capability_rng_state(randomizer, numpy_generator, generators),
    )
    payload.pop("target_state")
    checkpoint = tmp_path / "incomplete.pt"
    torch.save(payload, checkpoint)

    with pytest.raises(ValueError, match="complete v1 mapping"):
        restore_capability_checkpoint(
            checkpoint,
            model,
            target,
            optimizer,
            _SyntheticSettings(),  # type: ignore[arg-type]
            source_revision="b" * 40,
            artifact_identities={"population": "synthetic-population"},
            randomizer=randomizer,
            numpy_generator=numpy_generator,
            torch_generators=generators,
        )
