"""Verify the frozen independent agent on the official competition interpreter."""

import hashlib
import json
from pathlib import Path
from typing import Any

import hydra
import orjson
from omegaconf import DictConfig, OmegaConf

from kagg_revue.artifacts.io import digest, write_json
from kagg_revue.opponents.enterprise.experiment import Panel
from kagg_revue.opponents.public import PublicAgentRuntime, load_public_agent_manifest
from kagg_revue.opponents.research.qualification import _agent


def _verify_game(
    config: Panel, seed: int, seat: int, records: list[dict[str, Any]]
) -> dict[str, Any]:
    """Compare one official game with its saved native result."""
    from importlib import import_module

    make = import_module("kaggle_environments").make
    from kagg_revue.native import _revue_native as native

    if config.source is None:
        raise ValueError("official verification requires an explicit frozen standalone source")
    manifest = load_public_agent_manifest(config.manifest).by_id()
    configuration = dict(native.Engine(seed, {}).configuration)
    source = _agent(config.source, "none")
    opponent = PublicAgentRuntime(manifest["ahmed_v43"], Path.cwd(), configuration)
    fingerprint = hashlib.sha256()
    count = 0

    def act(observation: Any, settings: Any) -> dict[str, Any]:
        nonlocal count
        action: dict[str, Any] = source(dict(observation), dict(settings))
        fingerprint.update(orjson.dumps(action, option=orjson.OPT_SORT_KEYS))
        fingerprint.update(b"\0")
        count += 1
        return action

    def other(observation: Any, _: Any) -> dict[str, Any]:
        return opponent.act(dict(observation))

    environment = make("kaggriculture", configuration={**configuration, "seed": seed})
    final = environment.run([act, other] if seat == 0 else [other, act])[-1]
    if count != 719 or any(state.status != "DONE" for state in final):
        raise RuntimeError("official verification did not complete")
    baseline = next(
        row
        for row in records
        if row["opponent"] == "ahmed_v43" and row["seed"] == seed and row["seat"] == seat
    )
    actual = {
        "cash": float(final[0].observation.farms[seat]["money"]),
        "opponent_cash": float(final[0].observation.farms[1 - seat]["money"]),
        "action_sha256": fingerprint.hexdigest(),
    }
    matches = {field: baseline[field] == value for field, value in actual.items()}
    result = {"seed": seed, "seat": seat, "matches": matches, **actual}
    if not all(matches.values()):
        raise AssertionError(result)
    return result


def verify(config: Panel) -> None:
    """Repeat four declared games and compare complete candidate actions and final cash."""
    if config.source is None:
        raise ValueError("official verification requires an explicit frozen standalone source")
    records = [json.loads(path.read_text()) for path in (config.output / "games").glob("*.json")]
    rows = [
        _verify_game(config, seed, seat, records) for seed in config.seeds[:2] for seat in (0, 1)
    ]
    write_json(
        config.output / "official-verification.json",
        {
            "games": rows,
            "source_sha256": digest(config.source),
            "all_candidate_actions_and_final_cash_exact": True,
            "note": "Verification repeats; excluded from independent strength sample counts.",
        },
    )


@hydra.main(
    version_base=None, config_path="../../../../configs", config_name="enterprise_confirmation"
)
def main(configuration: DictConfig) -> None:
    """Check the declared artifact against the official engine and saved native games."""
    verify(Panel.model_validate(OmegaConf.to_container(configuration.panel, resolve=True)))


if __name__ == "__main__":
    main()
