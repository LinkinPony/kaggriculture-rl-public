"""Strict immutable configuration shared by domain schemas."""

from pydantic import BaseModel, ConfigDict


class FrozenSettings(BaseModel):
    """Reject misspelled experiment controls."""

    model_config = ConfigDict(extra="forbid", frozen=True, allow_inf_nan=False)
