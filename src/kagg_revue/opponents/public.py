"""Hash-verified loading of frozen public notebook opponents."""

from __future__ import annotations

import hashlib
import importlib.util
import inspect
import itertools
import sys
from collections.abc import Callable, Mapping
from pathlib import Path
from types import ModuleType
from typing import Any, Literal, cast

from pydantic import BaseModel, ConfigDict, Field, field_validator

_BUFFER_SIZE = 1024 * 1024
_MODULE_COUNTER = itertools.count()
_VERIFIED_FILES: dict[tuple[Path, str], tuple[int, int]] = {}
RawAgent = Callable[..., Any]


class _StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class PublicAgentRecord(_StrictModel):
    """Identity and provenance for one runnable notebook artifact."""

    agent_id: str = Field(pattern=r"^[a-z0-9_]+$")
    notebook_ref: str
    notebook_id: int = Field(gt=0)
    notebook_url: str
    main_path: Path
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    entrypoint: Literal["agent", "last_callable"] = "agent"
    files: dict[str, str] = Field(default_factory=dict)
    evidence_level: Literal[
        "official_public_score",
        "notebook_self_report",
        "title_claim",
        "unverified",
    ]
    evidence_note: str

    @field_validator("files")
    @classmethod
    def validate_files(cls, value: dict[str, str]) -> dict[str, str]:
        """Bind sibling dependencies without permitting paths outside the bundle."""
        for name, fingerprint in value.items():
            if (
                not name
                or Path(name).name != name
                or name in {".", ".."}
                or len(fingerprint) != 64
                or any(character not in "0123456789abcdef" for character in fingerprint)
            ):
                raise ValueError("public companion files require basenames and SHA-256 hashes")
        return value

    @field_validator("notebook_url")
    @classmethod
    def validate_notebook_url(cls, value: str) -> str:
        """Keep provenance on the expected public Kaggle surface."""
        if not value.startswith("https://www.kaggle.com/code/"):
            raise ValueError("notebook_url must be a public Kaggle notebook URL")
        return value


class RejectedArtifact(_StrictModel):
    """Downloaded notebook that did not expose a runnable agent artifact."""

    notebook_ref: str
    reason: str


class PublicAgentManifest(_StrictModel):
    """Acquisition manifest for a frozen public-agent panel."""

    schema_version: Literal[1] = 1
    retrieved_at: str
    retrieval: dict[str, str]
    agents: tuple[PublicAgentRecord, ...]
    rejected: tuple[RejectedArtifact, ...] = ()

    @field_validator("agents")
    @classmethod
    def validate_unique_agent_ids(
        cls,
        value: tuple[PublicAgentRecord, ...],
    ) -> tuple[PublicAgentRecord, ...]:
        """Reject ambiguous identities before any experiment starts."""
        agent_ids = [record.agent_id for record in value]
        if len(agent_ids) != len(set(agent_ids)):
            raise ValueError("agent_id values must be unique")
        return value

    def by_id(self) -> dict[str, PublicAgentRecord]:
        """Index records by their stable local identity."""
        return {record.agent_id: record for record in self.agents}


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(_BUFFER_SIZE):
            digest.update(chunk)
    return digest.hexdigest()


def load_public_agent_manifest(path: Path) -> PublicAgentManifest:
    """Parse one manifest without resolving or importing its artifacts."""
    return PublicAgentManifest.model_validate_json(path.read_text(encoding="utf-8"))


def resolve_public_agent_path(record: PublicAgentRecord, repository_root: Path) -> Path:
    """Resolve and authenticate an external agent file inside ``data/external``."""
    path = record.main_path
    resolved = (path if path.is_absolute() else repository_root / path).resolve()
    external_root = (repository_root / "data" / "external").resolve()
    if not resolved.is_relative_to(external_root):
        raise ValueError(f"public agent must be stored under {external_root}: {resolved}")
    if not resolved.is_file():
        raise FileNotFoundError(f"public agent artifact does not exist: {resolved}")
    _verify_file(resolved, record.sha256, record.agent_id)
    for name, expected in record.files.items():
        companion = (resolved.parent / name).resolve()
        if companion.parent != resolved.parent:
            raise ValueError("public companion file escapes its source bundle")
        _verify_file(companion, expected, f"{record.agent_id}/{name}")
    return resolved


def _verify_file(path: Path, expected: str, label: str) -> None:
    stat = path.stat()
    cache_key = (path, expected)
    identity = (stat.st_mtime_ns, stat.st_size)
    if _VERIFIED_FILES.get(cache_key) != identity:
        actual_sha256 = _sha256_file(path)
        if actual_sha256 != expected:
            raise ValueError(
                f"public agent hash mismatch for {label}: expected {expected}, got {actual_sha256}"
            )
        _VERIFIED_FILES[cache_key] = identity


def _load_module(path: Path, record: PublicAgentRecord) -> ModuleType:
    module_name = f"_revue_public_{record.agent_id}_{record.sha256[:12]}_{next(_MODULE_COUNTER)}"
    specification = importlib.util.spec_from_file_location(module_name, path)
    if specification is None or specification.loader is None:
        raise ImportError(f"could not create import specification for {path}")
    module = importlib.util.module_from_spec(specification)
    sys.modules[module_name] = module
    try:
        specification.loader.exec_module(module)
    finally:
        sys.modules.pop(module_name, None)
    return module


def _accepts_configuration(function: RawAgent) -> bool:
    try:
        inspect.signature(function).bind({}, {})
    except TypeError:
        try:
            inspect.signature(function).bind({})
        except TypeError as error:
            raise TypeError("agent entrypoint accepts neither (obs) nor (obs, config)") from error
        return False
    return True


class PublicAgentRuntime:
    """Fresh episode-local instance of one external notebook entrypoint."""

    def __init__(
        self,
        record: PublicAgentRecord,
        repository_root: Path,
        configuration: Mapping[str, Any],
    ) -> None:
        """Verify and import the artifact, isolating its module globals per game."""
        path = resolve_public_agent_path(record, repository_root)
        module = _load_module(path, record)
        function = (
            [value for value in vars(module).values() if callable(value)][-1]
            if record.entrypoint == "last_callable"
            else getattr(module, "agent", None)
        )
        if not callable(function):
            raise AttributeError(f"{record.agent_id} does not expose callable agent")
        self.record = record
        self._function = cast(RawAgent, function)
        self._configuration = dict(configuration)
        self._accepts_config = _accepts_configuration(self._function)

    def act(self, observation: Mapping[str, Any]) -> dict[str, Any]:
        """Call the public agent and enforce the official mapping boundary."""
        copied_observation = dict(observation)
        if self._accepts_config:
            raw_action = self._function(copied_observation, self._configuration)
        else:
            raw_action = self._function(copied_observation)
        if not isinstance(raw_action, Mapping):
            raise TypeError(
                f"{self.record.agent_id} returned {type(raw_action).__name__}, expected mapping"
            )
        return dict(raw_action)


__all__ = [
    "PublicAgentManifest",
    "PublicAgentRecord",
    "PublicAgentRuntime",
    "load_public_agent_manifest",
    "resolve_public_agent_path",
]
