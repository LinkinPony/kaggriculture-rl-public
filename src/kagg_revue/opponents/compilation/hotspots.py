"""Profile generated native functions on complete games before writing typed replacements."""

import json
import os
from pathlib import Path
from typing import Any

import hydra
from omegaconf import DictConfig

from kagg_revue.artifacts.io import digest, write_json
from kagg_revue.native import _revue_native as native
from kagg_revue.opponents.native_batch import create_native_opponent_session


@hydra.main(
    version_base=None, config_path="../../../../configs", config_name="native_policy_profile"
)
def main(configuration: DictConfig) -> None:
    """Keep profiling opt-in and separate from wall-clock throughput measurements."""
    if "KAGG_NATIVE_FUNCTION_PROFILE" not in os.environ:
        raise ValueError("set KAGG_NATIVE_FUNCTION_PROFILE before loading the native module")
    options = configuration.profile
    panels: list[dict[str, Any]] = []
    for name in options.opponents:
        for game in range(int(options.games)):
            engine = native.Engine(int(options.seed) + game // 2)
            session = create_native_opponent_session(name, 10)
            native.native_compiled_function_profile()
            for _ in range(719):
                action = native.native_opponent_action(engine, game % 2, session)
                engine.step(action if game % 2 == 0 else {}, action if game % 2 else {})
            rows = sorted(
                native.native_compiled_function_profile(),
                key=lambda row: row["self_seconds"],
                reverse=True,
            )
            panels.append({"opponent": name, "game": game, "functions": rows})
            print(json.dumps({"opponent": name, "game": game, "functions": rows[:15]}), flush=True)
            write_json(
                Path(options.report),
                {"binary_sha256": digest(Path(native.__file__)), "panels": panels},
            )


if __name__ == "__main__":
    main()
