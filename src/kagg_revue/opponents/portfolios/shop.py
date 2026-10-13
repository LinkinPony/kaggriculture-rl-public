"""Extract the frozen Shop Router's four tapes and two public-state decisions."""

import json
from pathlib import Path
from typing import Any


def extract_shop_router(directory: Path) -> dict[str, Any]:
    """Reject unsupported model semantics instead of silently changing the policy."""
    model = json.loads((directory / "model.json").read_text())
    routes = json.loads((directory / "actions.json").read_text())
    expected = {
        "kind": "mmpq_multi_entry_v1",
        "default": 0,
        "stages": [
            {
                "step": 144,
                "tree": {
                    "feature": 23,
                    "threshold": 0.5,
                    "left": {"choice": 0},
                    "right": {"choice": 1},
                },
            },
            {
                "step": 648,
                "tree": {
                    "feature": 71,
                    "threshold": 9888.0,
                    "left": {"choice": 2},
                    "right": {"choice": 3},
                },
            },
        ],
    }
    if model != expected or len(routes) != 4 or any(len(route) != 719 for route in routes):
        raise ValueError("unsupported Shop Router model or incomplete action tapes")
    return {"routes": routes, "model": model}
