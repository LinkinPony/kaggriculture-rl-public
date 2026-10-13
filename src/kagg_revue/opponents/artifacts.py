"""Archive the existing native opponents and their authenticated route assets."""

import shutil
from pathlib import Path
from typing import Any

from kagg_revue.artifacts.io import digest
from kagg_revue.opponents.native_batch import create_native_opponent_session
from kagg_revue.opponents.portfolios.catalog import ACTIVE_IDS
from kagg_revue.opponents.settings import PublicPopulation

_ASSETS: dict[str, str] = {
    name: f"src/kagg_revue/opponents/portfolios/{name}.json.zlib" for name in ACTIVE_IDS
}


def identity(config: PublicPopulation) -> dict[str, Any]:
    """Validate packaged assets before binding the binary and all selected route data."""
    from kagg_revue.native import _revue_native as native

    for name in config.agents:
        create_native_opponent_session(name, 10)
    binary = Path("src/kagg_revue/native") / Path(native.__file__).name
    names = [str(binary), *(_ASSETS[name] for name in config.agents)]
    return {"backend": "native-cpp", "files": {name: digest(Path(name)) for name in names}}


def archive(directory: Path, config: PublicPopulation) -> dict[str, Any]:
    """Keep original implementations available for exact isolated continuation."""
    result = identity(config)
    for name, expected in result["files"].items():
        target = directory / "script-runtime" / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(name, target)
        if digest(target) != expected:
            raise ValueError("script runtime changed while archiving")
    return {**result, "directory": "script-runtime"}


def materialize(directory: Path, record: dict[str, Any], target: Path) -> None:
    """Restore only hash-bound native and route files within the archived run."""
    for name, expected in record["files"].items():
        path = Path(name)
        source = (directory / record["directory"] / path).resolve()
        if (
            path.is_absolute()
            or ".." in path.parts
            or path.parts[:2] != ("src", "kagg_revue")
            or not source.is_relative_to(directory.resolve())
            or digest(source) != expected
        ):
            raise ValueError("archived script runtime file differs from its declared identity")
        destination = target / path
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
