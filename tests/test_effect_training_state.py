import random
from dataclasses import replace
from pathlib import Path

import numpy as np
import pytest
import torch
from torch.optim import AdamW

from kagg_revue.core.backend import load_backend
from kagg_revue.policy.model import ActorArchitecture, TurnPolicyNet
from kagg_revue.policy.vocabulary import CURRENT_ACTIONS
from kagg_revue.rl.effects.checkpoint import (
    capture_rng,
    load_checkpoint,
    restore_rng,
    save_checkpoint,
)
from kagg_revue.rl.effects.config import EffectModelSettings
from kagg_revue.rl.effects.initialization import initialize_effect_model


def _root() -> Path:
    return Path(__file__).resolve().parents[1]


def _write_actor(path: Path) -> None:
    backend = load_backend(_root())
    encoder = backend.actor_encoder_spec()
    codec = backend.action_codec_spec()
    architecture = ActorArchitecture(
        board_shape=(2, int(encoder["board_channels"]), 2, 2),
        unit_shape=(2, 4, int(encoder["unit_feat"])),
        global_features=int(encoder["global_feat"]),
        model_width=16,
        entity_width=8,
        attention_heads=2,
        feedforward_width=32,
        latent_tokens=2,
        scene_layers=0,
        temporal_layers=1,
        action_layers=1,
        max_history=2,
        max_decisions=6,
        unit_action_tokens=int(codec["unit_tokens"]),
        market_action_tokens=len(codec["keys"]) - int(codec["unit_tokens"]),
        maximum_quantity=8,
        derived_fact_version=None,
        turn_fact_features=0,
        prefix_fact_features=0,
        candidate_fact_features=0,
        fact_dropout=0.0,
        strategy_tokens=2,
        strategy_version="gru-v1",
    )
    actor = TurnPolicyNet(architecture)
    torch.save(
        {
            "artifact_version": "turn-policy-actor-v6",
            "action_codec_version": CURRENT_ACTIONS.version,
            "action_keys": tuple(str(value) for value in codec["keys"]),
            "actor_encoder_version": str(encoder["version"]),
            "architecture": architecture.model_dump(mode="json"),
            "derived_fact_version": None,
            "economic_feature_version": None,
            "model_state": actor.state_dict(),
        },
        path,
    )


def test_effect_initialization_and_checkpoint_restore_exact_state(
    tmp_path: Path,
) -> None:
    pytest.importorskip("kagg_revue.native._revue_native")
    backend = load_backend(_root())
    actor_path = tmp_path / "actor.pt"
    _write_actor(actor_path)
    model_settings = EffectModelSettings(
        model_width=16,
        feedforward_width=32,
        attention_heads=2,
        state_layers=1,
        train_turn_encoder=True,
    )
    environment: dict[str, object] = {
        "boardSize": 2,
        "episodeSteps": 3,
        "turnsPerDay": 1,
        "maxMarketOrdersPerTurn": 2,
    }
    model, contract, source = initialize_effect_model(
        actor_path,
        backend,
        environment,
        unit_limit=4,
        settings=model_settings,
        device=torch.device("cpu"),
    )
    assert source["path"] == str(actor_path)
    assert all(parameter.requires_grad for parameter in model.effects.parameters())
    assert all(parameter.requires_grad for parameter in model.actor.scene.parameters())
    assert not any(parameter.requires_grad for parameter in model.actor.action.parameters())
    optimizer = AdamW(
        [parameter for parameter in model.parameters() if parameter.requires_grad],
        lr=1e-4,
    )
    generator = torch.Generator().manual_seed(17)
    randomizer = random.Random(19)
    rng = capture_rng(randomizer, generator, torch.device("cpu"))
    checkpoint = tmp_path / "checkpoint.pt"
    save_checkpoint(
        checkpoint,
        model,
        optimizer,
        update=1,
        contract=contract,
        resolved_config={"objective": "terminal_wdl"},
        source_actor=source,
        source_revision={"revision": "fixture", "worktree_dirty": False},
        opponent_identities={"self_play": {"kind": "current_policy"}},
        population_state={"weights": {"self_play": 1.0}},
        rng_state=rng,
    )

    restored, metadata = load_checkpoint(checkpoint, contract, torch.device("cpu"))
    for name, value in model.state_dict().items():
        torch.testing.assert_close(restored.state_dict()[name], value)
    with pytest.raises(ValueError, match="identity"):
        load_checkpoint(
            checkpoint,
            replace(contract, version="stale-effect-abi"),
            torch.device("cpu"),
        )


def test_effect_rng_restore_replays_all_cpu_streams() -> None:
    torch_state = torch.get_rng_state()
    numpy_state = np.random.get_state()
    try:
        torch.manual_seed(23)
        np.random.seed(29)
        randomizer = random.Random(31)
        generator = torch.Generator().manual_seed(37)
        captured = capture_rng(randomizer, generator, torch.device("cpu"))
        expected = (
            randomizer.random(),
            float(np.random.random()),
            float(torch.rand(())),
            float(torch.rand((), generator=generator)),
        )
        restore_rng(
            captured,
            randomizer,
            generator,
            torch.device("cpu"),
        )
        actual = (
            randomizer.random(),
            float(np.random.random()),
            float(torch.rand(())),
            float(torch.rand((), generator=generator)),
        )
        assert actual == expected
    finally:
        torch.set_rng_state(torch_state)
        np.random.set_state(numpy_state)
