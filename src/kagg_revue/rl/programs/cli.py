"""Hydra command for conditional-program PPO."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any, cast

from hydra import compose, initialize_config_dir
from omegaconf import OmegaConf

from kagg_revue.rl.programs.config import ProgramRlAppSettings, ProgramRlSettings


def repository_root() -> Path:
    """Return the source checkout containing this package."""
    return Path(__file__).resolve().parents[4]


def load_settings(overrides: list[str]) -> ProgramRlSettings:
    """Compose and strongly validate one conditional-program profile."""
    root = repository_root()
    with initialize_config_dir(version_base=None, config_dir=str(root / "configs")):
        composed = compose(
            config_name="conditional_program_rl_config", overrides=overrides
        )
    value = OmegaConf.to_container(composed, resolve=True)
    return ProgramRlAppSettings.model_validate(
        cast(dict[str, Any], value)
    ).conditional_program_rl


def main() -> None:
    """Run long conditional-program PPO or one bounded integration smoke."""
    parser = argparse.ArgumentParser(prog="kagg-revue-program-rl")
    parser.add_argument(
        "command",
        nargs="?",
        default="train",
        choices=("train", "smoke", "benchmark", "evaluate"),
    )
    parser.add_argument("--benchmark-output", type=Path)
    parser.add_argument("--benchmark-warmups", type=int, default=1)
    parser.add_argument("--benchmark-repeats", type=int, default=3)
    parser.add_argument("--check-reference-parity", action="store_true")
    parser.add_argument("--evaluation-output", type=Path)
    parser.add_argument("--checkpoint", type=Path)
    parser.add_argument("--sample", action="store_true")
    arguments, overrides = parser.parse_known_args()
    settings = load_settings(overrides)
    if settings.device.startswith("cuda"):
        os.environ.setdefault("PYTORCH_CUDA_ALLOC_CONF", "expandable_segments:True")
        os.environ.setdefault(
            "TORCHINDUCTOR_COMPILE_THREADS", str(min(48, os.cpu_count() or 1))
        )
    if arguments.command == "benchmark":
        if arguments.benchmark_output is None:
            parser.error("benchmark requires --benchmark-output")
        from kagg_revue.rl.programs.benchmark import benchmark_conditional_program

        result = benchmark_conditional_program(
            settings,
            repository_root(),
            arguments.benchmark_output,
            warmups=arguments.benchmark_warmups,
            repeats=arguments.benchmark_repeats,
            check_reference=arguments.check_reference_parity,
        )
        print(json.dumps(result, indent=2, sort_keys=True, default=str))
        return
    if arguments.command == "evaluate":
        if arguments.evaluation_output is None:
            parser.error("evaluate requires --evaluation-output")
        from kagg_revue.rl.programs.evaluate import evaluate_conditional_program

        result = evaluate_conditional_program(
            settings,
            repository_root(),
            arguments.evaluation_output,
            checkpoint=arguments.checkpoint,
            sample=arguments.sample,
        )
        print(json.dumps(result, indent=2, sort_keys=True, default=str))
        return

    from kagg_revue.rl.programs.train import train_conditional_program

    result = train_conditional_program(
        settings,
        repository_root(),
        smoke=arguments.command == "smoke",
    )
    print(json.dumps(result, indent=2, sort_keys=True, default=str))


if __name__ == "__main__":
    main()
