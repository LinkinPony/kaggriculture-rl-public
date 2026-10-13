"""Summaries that distinguish per-turn sums from active-field averages."""

from typing import Any

import torch
from torch import Tensor


def distribution(values: Tensor) -> dict[str, float]:
    """Report quantiles of a finite, nonempty diagnostic sample."""
    values = values.double().flatten()
    if not values.numel() or not bool(torch.isfinite(values).all()):
        raise ValueError("diagnostic values must be nonempty and finite")
    quantiles = torch.quantile(values, torch.tensor([0.5, 0.9, 0.95, 0.99], dtype=torch.float64))
    return dict(
        mean=float(values.mean()),
        median=float(quantiles[0]),
        p90=float(quantiles[1]),
        p95=float(quantiles[2]),
        p99=float(quantiles[3]),
        maximum=float(values.max()),
    )


def summarize(data: dict[str, Tensor], work_factors: int) -> dict[str, Any]:
    """Keep all active choices, including deterministic choices, in the denominator."""
    fields = data["fields"].bool()
    kl = data["exact_kl"]
    delta = data["log_ratio"]
    numeric = data["unchanged_log_ratio"]
    sampled = delta.expm1() - delta
    unchanged = numeric.expm1() - numeric
    live_delta = delta + numeric
    categories = torch.arange(fields.shape[-1])
    groups = {
        "unit_target": (categories < work_factors) & (categories % 8 == 0),
        "unit_operation": (categories < work_factors) & (categories % 8 == 1),
        "unit_quantity": (categories < work_factors) & (categories % 8 == 2),
        "market_operation": (categories >= work_factors) & ((categories - work_factors) % 2 == 0),
        "market_quantity": (categories >= work_factors) & ((categories - work_factors) % 2 == 1),
    }
    result: dict[str, Any] = {
        "turns": fields.shape[0],
        "trajectories": fields.shape[1],
        "active_fields_per_turn": distribution(fields.sum(-1)),
        "exact_kl_per_turn": distribution((kl * fields).sum(-1)),
        "exact_kl_per_active_field": distribution(kl[fields]),
        "sampled_kl_per_turn": distribution((sampled * fields).sum(-1)),
        "unchanged_replay_kl_per_turn": distribution((unchanged * fields).sum(-1)),
        "online_to_after_sampled_kl_per_turn": distribution(
            ((live_delta.expm1() - live_delta) * fields).sum(-1)
        ),
        "entropy_before_per_turn": distribution((data["entropy_before"] * fields).sum(-1)),
        "entropy_after_per_turn": distribution((data["entropy_after"] * fields).sum(-1)),
        "total_variation_per_field": distribution(data["tv"][fields]),
        "absolute_sampled_log_ratio": distribution(delta[fields].abs()),
        "sampled_ratio_outside_10pct": float(
            ((delta[fields].exp() < 0.9) | (delta[fields].exp() > 1.1)).float().mean()
        ),
        "greedy_choice_change_fraction": float(data["greedy_changed"][fields].float().mean()),
        "groups": {},
    }
    rows = (kl * fields).sum(-1).flatten()
    result["top_1pct_turns_kl_share"] = float(
        rows.topk(max(1, len(rows) // 100)).values.sum() / rows.sum().clamp_min(1e-30)
    )
    result["per_trajectory_exact_kl"] = (kl * fields).sum((0, 2)).tolist()
    result["periods"] = {
        f"{start}-{min(start + 120, len(fields)) - 1}": float(
            (kl[start : start + 120] * fields[start : start + 120]).sum(-1).mean()
        )
        for start in range(0, len(fields), 120)
    }
    for name, columns in groups.items():
        selected = fields & columns
        if not bool(selected.any()):
            continue
        result["groups"][name] = {
            "active_count": int(selected.sum()),
            "exact_kl_per_field": distribution(kl[selected]),
            "exact_kl_contribution_per_turn": float((kl * selected).sum(-1).mean()),
            "entropy_per_field": float(data["entropy_before"][selected].mean()),
            "total_variation_per_field": distribution(data["tv"][selected]),
            "ratio_outside_10pct": float(
                ((delta[selected].exp() < 0.9) | (delta[selected].exp() > 1.1)).float().mean()
            ),
        }
    if "support_size" in data:
        multiple = fields & (data["support_size"] > 1)
        result["multiple_choices"] = {
            "fraction_of_active_fields": float(multiple.sum() / fields.sum()),
            "maximum_probability_at_least_099": float(
                (data["maximum_probability"][multiple] >= 0.99).float().mean()
            ),
            "maximum_probability_at_least_0999": float(
                (data["maximum_probability"][multiple] >= 0.999).float().mean()
            ),
        }
    result["uncertain_fields"] = {}
    for threshold in (0.1, 0.5):
        selected = fields & (data["entropy_before"] >= threshold)
        if not bool(selected.any()):
            continue
        ratios = delta[selected].exp()
        result["uncertain_fields"][str(threshold)] = {
            "fraction_of_active_fields": float(selected.sum() / fields.sum()),
            "fraction_of_kl": float((kl * selected).sum() / (kl * fields).sum().clamp_min(1e-30)),
            "mean_total_variation": float(data["tv"][selected].mean()),
            "ratio_outside_10pct": float(((ratios < 0.9) | (ratios > 1.1)).float().mean()),
        }
    return result
