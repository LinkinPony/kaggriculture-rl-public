"""Compare recorded opening procurement under the same legal opposing trade."""

import gzip
from copy import deepcopy
from pathlib import Path
from typing import Any

import hydra
import orjson
from omegaconf import DictConfig, OmegaConf

from kagg_revue.artifacts.io import digest, write_json
from kagg_revue.native import _revue_core as native


@hydra.main(version_base=None, config_path="../../../../configs", config_name="coverage_stress")
def main(config: DictConfig) -> None:
    """Measure two-turn purchase completion, without claiming counterfactual wins."""
    reference_path = Path(config.reference)
    reference = orjson.loads(reference_path.read_bytes())
    profiles = []
    cases = []
    for specification in config.profiles:
        path = Path(specification.path)
        content = path.read_bytes()
        replay = orjson.loads(gzip.decompress(content) if path.suffix == ".gz" else content)
        prefix = [replay["steps"][t + 1][int(specification.seat)]["action"] for t in range(2)]
        profiles.append(
            {
                "name": specification.name,
                "path": str(path),
                "sha256": digest(path),
                "recorded_seat": int(specification.seat),
                "prefix": prefix,
            }
        )
        for seat in (0, 1):
            for quantity in range(int(config.maximum_quantity) + 1):
                engine = native.Engine(reference["info"]["seed"], reference["configuration"])
                orders: list[dict[str, Any]] = []
                for turn in range(2):
                    opposing = deepcopy(reference["steps"][turn + 1][0]["action"])
                    if turn == 0:
                        if quantity == 0:
                            opposing["market"] = opposing["market"][2:]
                        else:
                            opposing["market"][0][2] = quantity
                    actions: list[Any] = [None, None]
                    actions[seat], actions[1 - seat] = prefix[turn], opposing
                    trace = engine.step_with_trace(*actions)
                    orders.extend(
                        o
                        for o in trace["market_trace"]
                        if o["player"] == seat
                        and o["requested"]
                        and o["requested"][0] == "BUY_ANIMAL"
                    )
                cases.append(
                    {
                        "profile": specification.name,
                        "seat": seat,
                        "opposing_wheat": quantity,
                        "cash_after_two": engine.observation(seat)["farms"][seat]["money"],
                        "animal_orders": orders,
                        "all_animal_orders_filled": all(
                            o["committed"] == o["requested"][2] for o in orders
                        ),
                    }
                )
    write_json(
        Path(config.output),
        {
            "config": OmegaConf.to_container(config, resolve=True),
            "profiles": profiles,
            "reference_sha256": digest(reference_path),
            "cases": cases,
            "scope": "Frozen recorded first two actions, same initial environment, both seats. "
            "Opponent is the observed ymg opening with only its first wheat quantity changed. "
            "This measures purchase completion; teachers are frozen and no match is completed.",
        },
    )
    print(f"Completed {len(cases)} two-turn cases", flush=True)


if __name__ == "__main__":
    main()
