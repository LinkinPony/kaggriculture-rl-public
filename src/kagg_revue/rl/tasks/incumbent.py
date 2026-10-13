"""Authenticated factory for the repository's named research incumbent."""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any, cast

from kagg_revue.bc.dataset import sha256_file
from kagg_revue.bc.evaluate import AgentFactory
from kagg_revue.rl.routes.runtime import RoutePolicyRuntime, load_route_model
from kagg_revue.rl.tasks.config import TaskIncumbentSettings


class _RouteIncumbentAgent:
    """Adapt seat-scoped route diagnostics to the generic match protocol."""

    def __init__(self, runtime: RoutePolicyRuntime) -> None:
        self._runtime = runtime
        self._seat = 0

    def act(self, observation: Mapping[str, Any]) -> dict[str, Any]:
        """Forward one official observation and remember its seat."""
        self._seat = int(observation.get("player", 0) or 0)
        return self._runtime.act(observation)

    def diagnostics(self) -> dict[str, int | str]:
        """Return diagnostics for the seat exercised by this match."""
        return self._runtime.diagnostics(self._seat)


def resolve_incumbent(
    settings: TaskIncumbentSettings,
    root: Path,
) -> TaskIncumbentSettings:
    """Resolve all incumbent artifacts against one repository checkout."""

    def resolve(path: Path) -> Path:
        return path.resolve() if path.is_absolute() else (root / path).resolve()

    return settings.model_copy(
        update={
            "checkpoint": resolve(settings.checkpoint),
            "confirmation_report": resolve(settings.confirmation_report),
            "runtime_audit_report": resolve(settings.runtime_audit_report),
        }
    )


def _report(path: Path, expected_sha256: str, name: str) -> Mapping[str, Any]:
    if not path.is_file() or sha256_file(path) != expected_sha256:
        raise ValueError(f"named incumbent {name} identity differs")
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, Mapping):
        raise ValueError(f"named incumbent {name} is not a mapping")
    return cast(Mapping[str, Any], raw)


def incumbent_identity(settings: TaskIncumbentSettings) -> dict[str, object]:
    """Verify checkpoint, confirmation, and official-time evidence as one identity."""
    if (
        not settings.checkpoint.is_file()
        or sha256_file(settings.checkpoint) != settings.checkpoint_sha256
    ):
        raise ValueError("named incumbent checkpoint identity differs")
    confirmation = _report(
        settings.confirmation_report,
        settings.confirmation_sha256,
        "confirmation report",
    )
    reports = confirmation.get("checkpoint_reports")
    if not isinstance(reports, Sequence) or isinstance(reports, (str, bytes)):
        raise ValueError("named incumbent confirmation lacks checkpoint reports")
    confirmed = False
    source_revision: object = None
    for raw in reports:
        if not isinstance(raw, Mapping):
            continue
        checkpoint = raw.get("checkpoint")
        policy = raw.get("policy")
        if (
            isinstance(checkpoint, Mapping)
            and isinstance(policy, Mapping)
            and checkpoint.get("sha256") == settings.checkpoint_sha256
            and float(policy.get("runtime_prior_logit", -1.0))
            == settings.prior_logit
        ):
            confirmed = True
            source_revision = checkpoint.get("source_revision")
            break
    if not confirmed:
        raise ValueError("named incumbent confirmation does not bind its policy")
    audit = _report(
        settings.runtime_audit_report,
        settings.runtime_audit_sha256,
        "runtime audit report",
    )
    audit_checkpoint = audit.get("checkpoint")
    budget = audit.get("official_budget")
    parity = audit.get("parity")
    if (
        not isinstance(audit_checkpoint, Mapping)
        or audit_checkpoint.get("sha256") != settings.checkpoint_sha256
        or float(audit_checkpoint.get("prior_logit", -1.0))
        != settings.prior_logit
        or not isinstance(budget, Mapping)
        or not bool(budget.get("passes"))
        or not isinstance(parity, Mapping)
        or not bool(parity.get("passes"))
    ):
        raise ValueError("named incumbent runtime audit does not bind a passing policy")
    return {
        "kind": settings.kind,
        "checkpoint": {
            "path": str(settings.checkpoint),
            "sha256": settings.checkpoint_sha256,
            "source_revision": source_revision,
        },
        "prior_logit": settings.prior_logit,
        "unit_limit": settings.unit_limit,
        "confirmation_report": {
            "path": str(settings.confirmation_report),
            "sha256": settings.confirmation_sha256,
        },
        "runtime_audit_report": {
            "path": str(settings.runtime_audit_report),
            "sha256": settings.runtime_audit_sha256,
        },
    }


def incumbent_factory(
    settings: TaskIncumbentSettings,
) -> tuple[AgentFactory, dict[str, object]]:
    """Load the frozen model once and create episode-local route executors."""
    identity = incumbent_identity(settings)
    model, _metadata = load_route_model(
        settings.checkpoint,
        prior_logit=settings.prior_logit,
    )

    def factory(configuration: Mapping[str, Any]) -> _RouteIncumbentAgent:
        return _RouteIncumbentAgent(
            RoutePolicyRuntime(
                configuration,
                model,
                unit_limit=settings.unit_limit,
            )
        )

    return factory, identity


__all__ = ["incumbent_factory", "incumbent_identity", "resolve_incumbent"]
