"""Validated settings for the intent-ledger oracle language audit."""

from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, model_validator

from kagg_revue.teacher.config import SubmissionArtifactSettings


class IntentOracleAuditSettings(BaseModel):
    """One bounded exact-submission oracle language audit."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    output_dir: Path
    teacher: SubmissionArtifactSettings
    seeds: tuple[int, ...] = Field(min_length=1)
    required_event_days: tuple[int, ...] = Field(min_length=1)
    require_clean_source: bool
    environment: dict[str, object]

    @model_validator(mode="after")
    def validate_audit(self) -> IntentOracleAuditSettings:
        """Reject escaped outputs and incomplete language panels."""
        path = self.output_dir
        if path.is_absolute() or len(path.parts) < 2 or path.parts[0] != "outputs":
            raise ValueError("intent oracle audit output must be relative under outputs/")
        if ".." in path.parts:
            raise ValueError("intent oracle audit output cannot escape outputs/")
        if len(set(self.seeds)) != len(self.seeds) or min(self.seeds) < 0:
            raise ValueError("intent oracle audit seeds must be unique and non-negative")
        if len(set(self.required_event_days)) != len(self.required_event_days):
            raise ValueError("required event days must be unique")
        for name, lower in {
            "boardSize": 1,
            "episodeSteps": 2,
            "turnsPerDay": 1,
            "maxMarketOrdersPerTurn": 1,
        }.items():
            value = self.environment.get(name)
            if not isinstance(value, int) or isinstance(value, bool) or value < lower:
                raise ValueError(f"intent oracle audit environment {name} is invalid")
        return self


class IntentOracleAuditAppSettings(BaseModel):
    """Hydra root for the oracle language audit."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    intent_ledger_oracle_audit: IntentOracleAuditSettings


__all__ = ["IntentOracleAuditAppSettings", "IntentOracleAuditSettings"]
