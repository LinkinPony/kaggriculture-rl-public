"""Conditional imitation diagnostics that separate rare choices from common fields."""

from typing import Any

import torch
from torch import Tensor

from kagg_revue.learning.pretraining.statistics import DOMAINS, domain_slices

MARKET_NAMES = (
    "STOP",
    "SKIP",
    "SELL:WHEAT",
    "SELL:CARROT",
    "SELL:TOMATO",
    "SELL:STRAWBERRY",
    "SELL:MELON",
    "SELL:EGG",
    "SELL:MILK",
    "SELL:WOOL",
    "SELL:FERTILIZER",
    "BUY_SEED:WHEAT",
    "BUY_SEED:CARROT",
    "BUY_SEED:TOMATO",
    "BUY_SEED:STRAWBERRY",
    "BUY_SEED:MELON",
    "BUY_PRODUCT:WHEAT",
    "BUY_PRODUCT:FERTILIZER",
    "BUY_ANIMAL:GOOSE",
    "BUY_ANIMAL:COW",
    "BUY_ANIMAL:SHEEP",
    "HIRE",
    "BUY_LAND",
)
UNIT_NAMES = {
    30: "PLANT:WHEAT",
    31: "PLANT:CARROT",
    32: "PLANT:TOMATO",
    33: "PLANT:STRAWBERRY",
    34: "PLANT:MELON",
    35: "WATER",
    36: "HARVEST",
    37: "FERTILIZE",
    38: "DIG",
    39: "BUILD_COOP",
    40: "BUILD_PASTURE",
    41: "FEED",
    42: "COLLECT_FERTILIZER",
    43: "CARE",
}
TOTAL_NAMES = ("count", "nll_sum", "correct", "teacher_probability_sum", "entropy_sum")


def totals(logits: Tensor, actions: Tensor, fields: Tensor, units: int) -> dict[str, list[float]]:
    """Sum metrics under teacher prefixes, retaining all legal alternatives in entropy."""
    logs = logits.float().log_softmax(-1)
    selected = logs.gather(-1, actions[..., None]).squeeze(-1)
    entropy = -(logs.exp() * logs).sum(-1)
    correct = (logs.argmax(-1) == actions).float()
    values = torch.stack((torch.ones_like(selected), -selected, correct, selected.exp(), entropy))
    active = fields.bool()
    output: dict[str, Tensor] = {}

    def add(name: str, section: slice, mask: Tensor) -> None:
        output[name] = (values[:, :, section] * mask[None]).sum((1, 2))

    for name, section in zip(DOMAINS, domain_slices(units, compact=False), strict=True):
        mask = active[:, section]
        add(name, section, mask)
        multiple = (logits[:, section] > -1e8).sum(-1) > 1
        add(f"{name}/multiple_choices", section, mask & multiple)
    work = units * 8
    for token, name in enumerate(MARKET_NAMES):
        section = slice(work, None, 2)
        mask = active[:, section] & (actions[:, section] == token)
        add(f"market/{name}", section, mask)
        quantity = slice(work + 1, None, 2)
        add(f"quantity/{name}", quantity, mask & active[:, quantity])
    section = slice(1, work, 8)
    for token, name in UNIT_NAMES.items():
        add(f"unit/{name}", section, active[:, section] & (actions[:, section] == token))
    return {key: value.double().cpu().tolist() for key, value in output.items()}


def aggregate(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Publish both field-weighted and teacher-specific summaries from additive counts."""
    combined: dict[str, list[float]] = {}
    for row in rows:
        for key, values in row["totals"].items():
            previous = combined.setdefault(key, [0.0] * len(TOTAL_NAMES))
            combined[key] = [a + b for a, b in zip(previous, values, strict=True)]
    return {
        key: {
            "count": int(values[0]),
            "nll": values[1] / values[0],
            "accuracy": values[2] / values[0],
            "teacher_probability": values[3] / values[0],
            "entropy": values[4] / values[0],
        }
        for key, values in combined.items()
        if values[0]
    }
