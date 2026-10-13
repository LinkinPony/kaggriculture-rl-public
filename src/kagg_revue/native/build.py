"""Build the official self-play core; select legacy targets explicitly when needed."""

import json
import os
import shutil
import subprocess
import sys
import sysconfig
from pathlib import Path
from typing import Literal

import hydra
import pybind11
from omegaconf import DictConfig, OmegaConf
from pydantic import Field

from kagg_revue.artifacts.io import digest, write_json
from kagg_revue.configuration import FrozenSettings

PACKAGE_DIR = Path(__file__).resolve().parent
CSRC_DIR = PACKAGE_DIR / "csrc"
REPO_ROOT = PACKAGE_DIR.parents[2]


class Build(FrozenSettings):
    """Choose the new CPU rules core or the explicitly retained legacy extensions."""

    target: Literal["core", "legacy"] = "core"
    jobs: int = Field(default=min(16, os.cpu_count() or 1), gt=0, le=64)


def _source_files() -> dict[str, str]:
    names = subprocess.check_output(["rg", "--files", str(CSRC_DIR)], text=True).splitlines()
    return {
        str(Path(name).relative_to(REPO_ROOT)): digest(Path(name))
        for name in sorted(names)
        if Path(name).suffix in {".cpp", ".hpp", ".h", ".inc", ".cu", ".cuh"}
        or Path(name).name == "CMakeLists.txt"
    }


def build(config: Build | None = None) -> Path:
    """Compile selected sources and atomically install only their named modules."""
    config = config or Build()
    source_files = _source_files()
    build_dir = REPO_ROOT / "tmp" / "native-build" / config.target
    source = CSRC_DIR / "core" if config.target == "core" else CSRC_DIR
    configure = [
        "cmake",
        "-S",
        str(source),
        "-B",
        str(build_dir),
        "-DCMAKE_BUILD_TYPE=Release",
        "-DCMAKE_EXPORT_COMPILE_COMMANDS=ON",
        f"-Dpybind11_DIR={pybind11.get_cmake_dir()}",
        f"-DPython_EXECUTABLE={sys.executable}",
    ]
    if shutil.which("ninja"):
        configure.append("-GNinja")
    subprocess.run(configure, check=True)
    subprocess.run(["cmake", "--build", str(build_dir), "--parallel", str(config.jobs)], check=True)
    if _source_files() != source_files:
        raise ValueError("native sources changed during compilation; refusing to install")
    suffix = sysconfig.get_config_var("EXT_SUFFIX")
    modules = (
        ("_revue_core",)
        if config.target == "core"
        else ("_revue_native", "_program_cuda", "_intent_cuda")
    )
    targets = []
    for module in modules:
        built = build_dir / f"{module}{suffix}"
        target = PACKAGE_DIR / built.name
        temporary = target.with_name(f".{target.name}.tmp")
        shutil.copy2(built, temporary)
        temporary.replace(target)
        targets.append(target)
    commands = json.loads((build_dir / "compile_commands.json").read_text())
    sources = sorted({str(Path(row["file"]).resolve().relative_to(REPO_ROOT)) for row in commands})
    write_json(
        REPO_ROOT / "outputs" / "native" / config.target / "build.json",
        {
            "configuration": config.model_dump(mode="json"),
            "python": sys.executable,
            "sources": {name: digest(REPO_ROOT / name) for name in sources},
            "native_source_snapshot": source_files,
            "modules": {path.name: digest(path) for path in targets},
            "compile_commands": commands,
        },
    )
    return targets[0]


@hydra.main(version_base=None, config_path=str(REPO_ROOT / "configs"), config_name="native_build")
def main(configuration: DictConfig) -> None:
    """Resolve the source target before compiling or replacing any module."""
    config = Build.model_validate(OmegaConf.to_container(configuration.build, resolve=True))
    print(build(config))


if __name__ == "__main__":
    main()
