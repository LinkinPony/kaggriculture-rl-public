"""Portable native extension compilation and ELF identity checks."""

import os
import re
import shutil
import subprocess
import tempfile
from collections.abc import Mapping
from pathlib import Path

import pybind11

from kagg_revue.artifacts.io import digest as sha256_file


def _command(command: list[str], *, environment: Mapping[str, str] | None = None) -> None:
    subprocess.run(command, check=True, env=environment)


def _interpreter_value(interpreter: Path, expression: str) -> str:
    return subprocess.run(
        [str(interpreter), "-c", f"import sysconfig; print({expression})"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def _python_config_overlay(interpreter: Path, build_dir: Path) -> Path | None:
    """Copy Debian's multiarch pyconfig header outside the compiler sysroot."""
    config_header = Path(
        _interpreter_value(interpreter, "sysconfig.get_config_h_filename()")
    ).resolve()
    multiarch = _interpreter_value(
        interpreter,
        "sysconfig.get_config_var('MULTIARCH') or ''",
    )
    if not config_header.is_file():
        raise FileNotFoundError(f"Python configuration header is absent: {config_header}")
    if not multiarch:
        return None
    multiarch_header = (
        config_header.parent.parent / multiarch / config_header.parent.name / config_header.name
    )
    if not multiarch_header.is_file():
        return None
    overlay = build_dir / "python-config-overlay"
    destination = overlay / multiarch / config_header.parent.name / config_header.name
    destination.parent.mkdir(parents=True)
    shutil.copy2(multiarch_header, destination)
    return overlay


def _version_key(value: str) -> tuple[int, ...]:
    return tuple(int(part) for part in value.split("."))


def _audit_elf(path: Path, max_glibc: str) -> dict[str, object]:
    """Reject host-specific dynamic links and too-new glibc symbol versions."""
    dynamic = subprocess.run(
        ["readelf", "-d", str(path)],
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    forbidden = ("libstdc++.so", "libgcc_s.so", "libgomp.so")
    linked_forbidden = [library for library in forbidden if library in dynamic]
    if linked_forbidden:
        raise RuntimeError(
            f"submission native extension has nonportable runtime links: {linked_forbidden}"
        )
    if "(RPATH)" in dynamic or "(RUNPATH)" in dynamic:
        raise RuntimeError("submission native extension contains a build-host search path")
    needed = sorted(set(re.findall(r"Shared library: \[([^]]+)]", dynamic)))
    version_info = subprocess.run(
        ["readelf", "--version-info", str(path)],
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    glibc_versions = sorted(
        set(re.findall(r"Name: GLIBC_(\d+(?:\.\d+)+)\b", version_info)),
        key=_version_key,
    )
    incompatible = [
        version for version in glibc_versions if _version_key(version) > _version_key(max_glibc)
    ]
    if incompatible:
        raise RuntimeError(
            f"submission native extension requires unsupported glibc versions: {incompatible}"
        )
    symbols = subprocess.run(
        ["nm", "--dynamic", "--defined-only", str(path)],
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    locale_symbols = [
        line.split()[-1]
        for line in symbols.splitlines()
        if line.split()
        and line.split()[-1].startswith(("_ZNSt6locale", "_ZNSt8ios_base", "_ZNKSt7codecvt"))
    ]
    if locale_symbols:
        raise RuntimeError("static C++ locale symbols must be isolated from other Python modules")
    return {
        "needed_libraries": needed,
        "required_glibc_versions": glibc_versions,
        "maximum_allowed_glibc": max_glibc,
        "has_runtime_search_path": False,
        "exported_locale_symbols": locale_symbols,
    }


def _build_native(
    repository_root: Path,
    package_root: Path,
    interpreter: Path,
    compiler: Path,
    patchelf: Path,
    max_glibc: str,
    jobs: int,
    *,
    deployment: bool = False,
) -> dict[str, object]:
    """Build one Python ABI, optionally restricting sources to observation execution."""
    interpreter = interpreter.resolve()
    compiler = compiler.resolve()
    patchelf = patchelf.resolve()
    if not interpreter.is_file() or not os.access(interpreter, os.X_OK):
        raise FileNotFoundError(f"native build interpreter is not executable: {interpreter}")
    if not compiler.is_file() or not os.access(compiler, os.X_OK):
        raise FileNotFoundError(f"native build compiler is not executable: {compiler}")
    if not patchelf.is_file() or not os.access(patchelf, os.X_OK):
        raise FileNotFoundError(f"native build patchelf is not executable: {patchelf}")
    suffix = _interpreter_value(interpreter, "sysconfig.get_config_var('EXT_SUFFIX')")
    abi = _interpreter_value(interpreter, "sysconfig.get_config_var('SOABI')")
    version = subprocess.run(
        [str(interpreter), "-c", "import platform; print(platform.python_version())"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    if not suffix.startswith(".") or not abi:
        raise ValueError(f"cannot resolve native extension ABI for {interpreter}")

    temporary_root = repository_root / "tmp"
    temporary_root.mkdir(exist_ok=True)
    target = "_revue_observation" if deployment else "_revue_native"
    source = repository_root / "src" / "kagg_revue" / "native" / "csrc"
    if deployment:
        source = source / "deployment"
    with tempfile.TemporaryDirectory(prefix=f"submission-native-{abi}-", dir=temporary_root) as raw:
        build_dir = Path(raw)
        config_overlay = _python_config_overlay(interpreter, build_dir)
        command = [
            "cmake",
            "-S",
            str(source),
            "-B",
            str(build_dir),
            "-DCMAKE_BUILD_TYPE=Release",
            f"-Dpybind11_DIR={pybind11.get_cmake_dir()}",
            f"-DPython_EXECUTABLE={interpreter}",
            f"-DCMAKE_CXX_COMPILER={compiler}",
            "-DREVUE_STATIC_CXX_RUNTIME=ON",
        ]
        if not deployment:
            command.append("-DREVUE_ENABLE_OPENMP=OFF")
        if config_overlay is not None:
            command.append(f"-DCMAKE_CXX_FLAGS=-I{config_overlay}")
        if shutil.which("ninja"):
            command.append("-GNinja")
        _command(command)
        _command(
            [
                "cmake",
                "--build",
                str(build_dir),
                "--target",
                target,
                "--parallel",
                str(jobs),
            ]
        )
        built = build_dir / f"{target}{suffix}"
        if not built.is_file():
            raise FileNotFoundError(f"native build did not produce {built.name}")
        destination = package_root / "src" / "kagg_revue" / "native" / built.name
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(built, destination)

    _command([str(patchelf), "--remove-rpath", str(destination)])
    elf = _audit_elf(destination, max_glibc)

    environment = dict(os.environ)
    environment["PYTHONPATH"] = str(package_root / "src")
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    _command(
        [
            str(interpreter),
            "-c",
            (
                f"from kagg_revue.native import {target} as n; "
                + (
                    "assert n.feature_version == 'grounded-unit-support-v1'"
                    if deployment
                    else "assert n.actor_encoder_spec(); assert n.action_codec_spec()"
                )
            ),
        ],
        environment=environment,
    )
    return {
        "archive_path": destination.relative_to(package_root).as_posix(),
        "python_abi": abi,
        "python_version": version,
        "sha256": sha256_file(destination),
        "size_bytes": destination.stat().st_size,
        "cxx_runtime": "static",
        "openmp": False,
        "toolchain": {
            "compiler_path": str(compiler),
            "compiler_sha256": sha256_file(compiler),
            "compiler_version": subprocess.run(
                [str(compiler), "--version"],
                check=True,
                capture_output=True,
                text=True,
            ).stdout.splitlines()[0],
            "sysroot": subprocess.run(
                [str(compiler), "-print-sysroot"],
                check=True,
                capture_output=True,
                text=True,
            ).stdout.strip(),
            "patchelf_path": str(patchelf),
            "patchelf_sha256": sha256_file(patchelf),
            "patchelf_version": subprocess.run(
                [str(patchelf), "--version"],
                check=True,
                capture_output=True,
                text=True,
            ).stdout.strip(),
        },
        "elf": elf,
    }
