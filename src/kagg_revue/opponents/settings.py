"""Explicit identities for public scripts used as training opponents."""

from pathlib import Path
from typing import Literal

from pydantic import Field, ValidationInfo, model_validator

from kagg_revue.configuration import FrozenSettings
from kagg_revue.opponents.portfolios.catalog import ACTIVE_IDS, ActiveAgentId, RetiredAgentId


class PublicPopulation(FrozenSettings):
    """Bind a whole-game fraction to reviewed, immutable external source files."""

    manifest: Path
    sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    agents: tuple[ActiveAgentId | RetiredAgentId, ...]
    backend: Literal["native-cpp"] = "native-cpp"
    fraction: float = Field(ge=0, lt=1)

    @model_validator(mode="after")
    def validate_source(self, info: ValidationInfo) -> "PublicPopulation":
        """Require repository external artifacts and distinct opponent identities."""
        if (
            self.manifest.is_absolute()
            or ".." in self.manifest.parts
            or self.manifest.parts[:2] != ("data", "external")
            or not self.agents
            or len(set(self.agents)) != len(self.agents)
        ):
            raise ValueError("public opponents require an external manifest and unique agent IDs")
        if any(name not in ACTIVE_IDS for name in self.agents) and not (
            info.context and info.context.get("archived_population")
        ):
            raise ValueError("retired opponents are only accepted when reading a previous protocol")
        return self
