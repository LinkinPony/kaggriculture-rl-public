"""Recover literal embedded submissions without running downloaded notebook cells."""

import ast
import base64
import gzip
import hashlib
import io
import json
import tarfile
from pathlib import Path
from typing import Any

from kagg_revue.artifacts.io import digest, write_json
from kagg_revue.opponents.portfolios.extraction import Literals


class Payloads(Literals):
    """Extend data-only decoding for notebook packaging, never arbitrary expressions."""

    def value(self, node: ast.expr) -> Any:
        """Accept compressed bytes and literal joins used by public submission bundles."""
        if isinstance(node, ast.Call) and not node.keywords:
            name = ast.unparse(node.func)
            if len(node.args) == 1:
                if name == "gzip.decompress":
                    return gzip.decompress(self.value(node.args[0]))
                if name == "base64.b64decode":
                    argument = self.value(node.args[0])
                    return base64.b64decode(
                        b"".join(argument.split())
                        if isinstance(argument, bytes)
                        else "".join(argument.split()),
                        validate=True,
                    )
                if isinstance(node.func, ast.Attribute) and node.func.attr == "join":
                    separator = ast.literal_eval(node.func.value)
                    if isinstance(separator, str | bytes):
                        return separator.join(self.value(node.args[0]))
        return super().value(node)


def _archive(payload: bytes, destination: Path) -> bytes:
    """Read bounded regular bundle members without extracting paths or links."""
    (destination / "submission.tar.gz").write_bytes(payload)
    with tarfile.open(fileobj=io.BytesIO(payload), mode="r:*") as archive:
        for member in archive.getmembers():
            path = Path(member.name)
            if not member.isfile() or len(path.parts) != 1 or member.size > 8_000_000:
                raise ValueError("submission bundle contains an unsupported member")
            stream = archive.extractfile(member)
            assert stream is not None
            (destination / path.name).write_bytes(stream.read())
    return (destination / "main.py").read_bytes()


def extract(notebook: Path, destination: Path) -> dict[str, Any]:
    """Freeze exact source and its packaging provenance, rejecting conflicting payloads."""
    destination.mkdir(parents=True, exist_ok=False)
    source: bytes | None = None
    expected: set[str] = set()
    method = ""
    for cell in json.loads(notebook.read_text())["cells"]:
        if cell["cell_type"] != "code":
            continue
        text = "".join(cell["source"])
        if text.startswith("%%writefile main.py\n"):
            source = text.split("\n", 1)[1].encode()
            method = "literal writefile"
            continue
        try:
            values = Payloads(text)
        except SyntaxError:
            continue  # Diagnostic cells can use a newer Python grammar.
        for name in ("EXPECTED_MAIN_SHA256", "EXPECTED_SHA256"):
            if name in values.assignments:
                value = values.named(name)
                if isinstance(value, str) and len(value) == 64:
                    expected.add(value)
        if source is not None:
            continue
        for name in ("SOURCE_BYTES", "source_bytes"):
            if name not in values.assignments:
                continue
            try:
                value = values.named(name)
            except (ValueError, KeyError, TypeError):
                continue
            if isinstance(value, bytes):
                source, method = value, f"static {name}"
                break
        if source is not None:
            continue
        for name in ("ARCHIVE_BYTES", "ARCHIVE_B64", "_PAYLOAD"):
            if name not in values.assignments:
                continue
            payload = values.named(name)
            if name == "ARCHIVE_B64":
                payload = base64.b64decode(payload, validate=True)
            if name == "_PAYLOAD":
                import zlib

                source = zlib.decompress(base64.b64decode(payload, validate=True))
            else:
                source = _archive(payload, destination)
            method = f"static {name}"
            break
    if source is None:
        raise ValueError("no supported embedded main.py payload")
    fingerprint = hashlib.sha256(source).hexdigest()
    if expected and fingerprint not in expected:
        raise ValueError(f"source digest {fingerprint} differs from notebook's declared digest")
    ast.parse(source)
    (destination / "main.py").write_bytes(source)
    report = {
        "notebook": str(notebook),
        "notebook_sha256": digest(notebook),
        "source_sha256": fingerprint,
        "declared_sha256": sorted(expected),
        "method": method,
        "notebook_cells_executed": False,
        "files": {path.name: digest(path) for path in sorted(destination.iterdir())},
    }
    write_json(destination / "extraction.json", report)
    return report
