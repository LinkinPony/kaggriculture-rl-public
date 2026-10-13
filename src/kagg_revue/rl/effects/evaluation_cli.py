"""Hydra entry point for atomic-effect closed-loop evaluation."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any, cast

from hydra import compose, initialize_config_dir
from omegaconf import OmegaConf

from kagg_revue.rl.effects.evaluation_config import EffectEvaluationAppSettings


def repository_root() -> Path:
    """Return the checkout containing this command."""
    return Path(__file__).resolve().parents[4]


def load_settings(overrides: list[str]) -> EffectEvaluationAppSettings:
    """Compose and validate one tracked effect evaluation profile."""
    root = repository_root()
    with initialize_config_dir(version_base=None, config_dir=str(root / "configs")):
        composed = compose(
            config_name="effect_policy_evaluation_config",
            overrides=overrides,
        )
    payload = OmegaConf.to_container(composed, resolve=True)
    return EffectEvaluationAppSettings.model_validate(cast(dict[str, Any], payload))


def main() -> None:
    """Evaluate the authenticated BC checkpoint on paired complete matches."""
    settings = load_settings(sys.argv[1:]).effect_policy_evaluation
    if settings.device.startswith("cuda"):
        os.environ.setdefault("PYTORCH_CUDA_ALLOC_CONF", "expandable_segments:True")
        os.environ.setdefault(
            "TORCHINDUCTOR_CACHE_DIR",
            str(repository_root() / "tmp" / "torchinductor_effect_evaluation"),
        )
    from kagg_revue.rl.effects.evaluate import evaluate_effect_checkpoint

    result = evaluate_effect_checkpoint(settings, repository_root())
    print(json.dumps(result, indent=2, sort_keys=True, default=str))


if __name__ == "__main__":
    main()
