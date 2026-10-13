"""Hydra-backed controls for periodic CPU export and private Drive uploads."""

from pathlib import Path

from pydantic import Field, model_validator

from kagg_revue.configuration import FrozenSettings
from kagg_revue.native.settings import NativeBuildSettings


class Publishing(FrozenSettings):
    """Separate credentials from persistent, reviewable deployment artifacts."""

    output_dir: Path = Path("outputs/deployment/drive-publisher")
    runs: tuple[Path, ...] = ()
    labels: dict[str, str] = Field(default_factory=dict)
    discover_active: bool = True
    interval_seconds: int = Field(default=1800, ge=60)
    poll_seconds: int = Field(default=30, ge=1)
    retry_seconds: int = Field(default=120, ge=1)
    worker_timeout_seconds: int = Field(default=1200, gt=0)
    upload_timeout_seconds: int = Field(default=600, gt=0)
    temperature: float = Field(default=0.0, ge=0)
    native: NativeBuildSettings
    rclone: Path = Path("/usr/bin/rclone")
    rclone_config: Path = Path.home() / ".config" / "rclone" / "rclone.conf"
    remote: str = Field(default="gdrive", pattern=r"^[a-zA-Z0-9_-]+$")
    folder: str = Field(default="kagg-rl-revue-submissions", pattern=r"^[a-zA-Z0-9_-]+$")
    once: bool = False

    @model_validator(mode="after")
    def validate_paths(self) -> "Publishing":
        """Restrict enumeration and new artifacts to their repository roles."""
        for path, prefix in [
            (self.output_dir, ("outputs", "deployment")),
            *((run, ("outputs", "learning")) for run in self.runs),
        ]:
            if path.is_absolute() or ".." in path.parts or path.parts[:2] != prefix:
                raise ValueError("publisher paths must be relative repository output paths")
            if not path.resolve().is_relative_to(Path(*prefix).resolve()):
                raise ValueError("publisher path escapes its output role through a symlink")
        if self.rclone_config.resolve().is_relative_to(Path.cwd().resolve()):
            raise ValueError("keep Google credentials outside the repository")
        return self
