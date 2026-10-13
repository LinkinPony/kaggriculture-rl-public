"""Measure native policy phases and tail turns independently of GPU or OpenMP waits."""

import hashlib
import json
import os
import time
from pathlib import Path
from typing import Any

import hydra
import orjson
from omegaconf import DictConfig, OmegaConf

from kagg_revue.artifacts.io import digest, write_json
from kagg_revue.native import _revue_native as native
from kagg_revue.opponents.native_batch import create_native_opponent_session


@hydra.main(
    version_base=None, config_path="../../../../configs", config_name="native_policy_profile"
)
def main(configuration: DictConfig) -> None:
    """Keep full decisions and state hashes alongside thread CPU phase measurements."""
    options = configuration.profile
    os.sched_setaffinity(0, {min(os.sched_getaffinity(0))})
    panels = []
    for name in options.opponents:
        records: list[dict[str, Any]] = []
        action_hash, state_hash = hashlib.sha256(), hashlib.sha256()
        for game in range(int(options.games)):
            engine = native.Engine(int(options.seed) + game // 2)
            seat = game % 2
            session = create_native_opponent_session(name, 10)
            session.enable_profiling()
            previous = session.profile()
            for step in range(719):
                started = time.perf_counter()
                action = native.native_opponent_action(engine, seat, session)
                elapsed = time.perf_counter() - started
                current = session.profile()
                phases = {key: current[key] - previous[key] for key in current}
                previous = current
                records.append({"game": game, "step": step, "wall_seconds": elapsed, **phases})
                action_hash.update(orjson.dumps(action, option=orjson.OPT_SORT_KEYS))
                engine.step(action if seat == 0 else {}, action if seat == 1 else {})
                state_hash.update(
                    orjson.dumps(
                        [engine.observation(p) for p in (0, 1)], option=orjson.OPT_SORT_KEYS
                    )
                )
        totals = {
            key: sum(row[key] for row in records)
            for key in records[0]
            if key not in {"game", "step"}
        }
        panel = {
            "opponent": name,
            "totals": totals,
            "actions_sha256": action_hash.hexdigest(),
            "states_sha256": state_hash.hexdigest(),
            "turns": records,
        }
        panels.append(panel)
        print(
            json.dumps({key: value for key, value in panel.items() if key != "turns"}), flush=True
        )
        write_json(
            Path(options.report),
            {
                "configuration": OmegaConf.to_container(options, resolve=True),
                "native_sha256": digest(Path(native.__file__)),
                "panels": panels,
            },
        )


if __name__ == "__main__":
    main()
