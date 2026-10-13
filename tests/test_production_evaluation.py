from pathlib import Path

import pytest
import torch
from hydra import compose, initialize_config_dir
from omegaconf import OmegaConf

from kagg_revue.production.artifacts import provenance, save_policy
from kagg_revue.production.config import Settings
from kagg_revue.production.contracts import ContractLayout
from kagg_revue.production.evaluation import panel
from kagg_revue.production.evaluation.comparison import paired_scores
from kagg_revue.production.networks.work import WorkPolicy


def test_neural_panel_preserves_rng_and_routes_real_games_without_teacher(
    tmp_path: Path,
    monkeypatch,
) -> None:
    # An idle actor keeps its bank; a seed buyer spends money.
    # Evaluate both seats against an actual saved neural policy, without data/.
    # Load the tracked Hydra profile so this test needs no experiment artifacts.
    with initialize_config_dir(version_base=None, config_dir=str(Path("configs").resolve())):
        configuration = compose(config_name="production_config", overrides=["production=work"])
    resolved = OmegaConf.to_container(configuration.production, resolve=True)
    assert isinstance(resolved, dict)
    resolved.update(
        checkpoint=Path("unused.pt"),
        devices=["cpu"],
        unit_limit=2,
        width=16,
        decision_interval=2,
        quantity_max=1,
        quantity_extra=[],
        opponents=[],
        evaluation_policies=[tmp_path / "opponent.pt"],
        evaluation_games=4,
        environment={
            "boardSize": 4,
            "episodeSteps": 9,
            "turnsPerDay": 3,
            "maxMarketOrdersPerTurn": 2,
        },
        model={"architecture": "work-v1", "depth": 1, "heads": 2, "time_prior": False},
    )
    settings = Settings.model_validate(resolved)
    actor = WorkPolicy(ContractLayout.resolve(settings)).eval()
    opponent = WorkPolicy(actor.layout).eval()
    with torch.no_grad():
        opponent.market_heads[0][-1].bias[11] = 10
    save_policy(tmp_path / "opponent.pt", opponent, settings)
    before = torch.get_rng_state().clone()
    result = panel(settings, actor, settings.evaluation_seed)
    assert result["wins"] == 4
    assert result["losses"] == result["ties"] == 0
    assert [game["seat"] for game in result["games"]] == [0, 1, 0, 1]
    assert len({game["seed"] for game in result["games"]}) == 2
    assert torch.equal(before, torch.get_rng_state())
    assert result["games"] == panel(settings, actor, settings.evaluation_seed)["games"]
    mixed_settings = settings.model_copy(update={"opponents": ("pass",), "evaluation_games": 8})
    mixed = panel(mixed_settings, actor, settings.evaluation_seed)
    assert (mixed["wins"], mixed["ties"], mixed["losses"]) == (4, 4, 0)
    assert torch.equal(before, torch.get_rng_state())
    # Provenance must not authenticate an unused Kaito teacher on this path.
    settings = settings.model_copy(
        update={
            "ppo": settings.ppo.model_copy(
                update={"population": "self_play", "script_opponents": ()}
            )
        }
    )
    original = Path.read_text

    def read_text(path, *args, **kwargs):
        assert "public-notebooks" not in str(path)
        return original(path, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", read_text)
    identity = provenance(settings)
    assert identity["opponents"] == []
    assert identity["evaluation_policies"] == result["evaluation_policies"]


def test_score_uncertainty_keeps_paired_seats_in_the_same_seed_cluster() -> None:
    games = [
        {"seed": seed, "seat": seat, "opponent": "neural", "outcome": 2 * seat - 1}
        for seed in (11, 19)
        for seat in (0, 1)
    ]
    control = {"games": games}
    candidate = {"games": [{**game, "outcome": -game["outcome"]} for game in reversed(games)]}
    result = paired_scores(control, candidate)
    assert result["better"] == result["worse"] == 2
    assert result["independent_seeds"] == 2
    assert result["seed_cluster_bootstrap_95_interval"] == [0.0, 0.0]
    with pytest.raises(ValueError, match="duplicate"):
        paired_scores(control, {"games": candidate["games"] + candidate["games"]})
