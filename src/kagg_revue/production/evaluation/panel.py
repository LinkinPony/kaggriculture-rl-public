"""Complete paired native matches on the direct outcome surface."""

import time
from typing import Any

import numpy as np
import torch

from kagg_revue.artifacts.io import digest, write_json
from kagg_revue.evaluation.neural import NeuralMatches
from kagg_revue.policy.checkpoints import load_policy
from kagg_revue.policy.spatial.model import Policy
from kagg_revue.production.artifacts import provenance
from kagg_revue.production.config import Settings
from kagg_revue.production.evaluation.matches import ScriptMatches


def _script_panel(
    settings: Settings, policy: Policy, seed: int, *, sample: bool = False
) -> dict[str, Any]:
    """Evaluate an exact actor against the unchanged notebook strength ladder."""
    device = next(policy.parameters()).device
    devices = [device.index] if device.type == "cuda" and device.index is not None else []
    with torch.random.fork_rng(devices=devices):
        torch.manual_seed(settings.seed + seed)
        result = ScriptMatches(settings, policy, sample=sample).run(seed)
    result["temperature"] = settings.ppo.temperature if sample else None
    return result


def panel(settings: Settings, policy: Policy, seed: int, *, sample: bool = False) -> dict[str, Any]:
    """Evaluate balanced frozen opponents without requiring any script or teacher.

    Neural opponents play reactively from their own observations on both seats.
    Checkpoint hashes identify opponents in paired comparisons. Each invocation
    restores the caller's RNG, including random initialization during loading.
    """
    if not settings.evaluation_policies:
        return _script_panel(settings, policy, seed, sample=sample)
    count = len(settings.opponents) + len(settings.evaluation_policies)
    per_opponent = settings.evaluation_games // count
    if per_opponent % 2 or per_opponent * count != settings.evaluation_games:
        raise ValueError("evaluation must balance every opponent and both seats")
    device = next(policy.parameters()).device
    devices = [device.index] if device.type == "cuda" and device.index is not None else []
    started = time.perf_counter()
    panels = []
    identities = []
    seen = set()
    with torch.random.fork_rng(devices=devices):
        if settings.opponents:
            scripts = settings.model_copy(
                update={"evaluation_games": per_opponent * len(settings.opponents)}
            )
            panels.append(_script_panel(scripts, policy, seed, sample=sample))
        neural = settings.model_copy(update={"evaluation_games": per_opponent})
        for path in settings.evaluation_policies:
            fingerprint = digest(path)
            if fingerprint in seen:
                raise ValueError("evaluation checkpoints must have distinct content identities")
            seen.add(fingerprint)
            opponent, payload = load_policy(path, device)
            del payload
            opponent.eval().requires_grad_(False)
            torch.manual_seed(settings.seed + seed)
            matches = NeuralMatches(neural, policy, opponent, sample=sample)
            result = matches.run(seed)
            for game in result["games"]:
                game["opponent"] = f"policy:{fingerprint}"
            panels.append(result)
            identities.append({"path": str(path), "sha256": fingerprint})
            del matches, opponent
    games = [game for result in panels for game in result["games"]]
    cash = np.array([game["cash"] for game in games])
    opponent_cash = np.array([game["opponent_cash"] for game in games])
    outcomes = np.array([game["outcome"] for game in games])
    elapsed = time.perf_counter() - started
    return {
        "games": games,
        "wins": int((outcomes > 0).sum()),
        "ties": int((outcomes == 0).sum()),
        "losses": int((outcomes < 0).sum()),
        "mean_cash": float(cash.mean()),
        "median_cash": float(np.median(cash)),
        "p10_cash": float(np.quantile(cash, 0.1)),
        "mean_cash_difference": float((cash - opponent_cash).mean()),
        "sample": sample,
        "temperature": settings.ppo.temperature if sample else None,
        "evaluation_policies": identities,
        "timing": {"elapsed_seconds": elapsed, "physical_games_per_second": len(games) / elapsed},
        "deployment_budget_qualified": False,
    }


def evaluate(settings: Settings) -> None:
    """Write an artifact-bound confirmation panel for an explicit checkpoint."""
    if settings.checkpoint is None:
        raise ValueError("evaluation requires an explicit checkpoint")
    device = torch.device(settings.devices[0])
    if device.type == "cuda":
        torch.cuda.set_device(device)
    torch.set_num_threads(settings.cpu_threads)
    policy, _ = load_policy(settings.checkpoint, device)
    result = panel(settings, policy, settings.confirmation_seed, sample=settings.evaluation_sample)
    result["checkpoint"] = {"path": str(settings.checkpoint), "sha256": digest(settings.checkpoint)}
    write_json(settings.output_dir / "source.json", provenance(settings))
    write_json(settings.output_dir / "resolved-config.json", settings.model_dump(mode="json"))
    write_json(settings.output_dir / "confirmation.json", result)
    print({key: value for key, value in result.items() if key != "games"}, flush=True)
