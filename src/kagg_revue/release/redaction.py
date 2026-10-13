"""Remove build-machine paths without changing executable model payloads."""

import io
import pickletools
import re
import struct
import zipfile

PRIVATE_PATH = re.compile(r"/(?:root|home/[^/\s]+|Users/[^/\s]+)/[^\s\"'`<>),;\x00]+")


def redact_text(value: str) -> str:
    """Replace host paths with package-relative or anonymous locations."""

    def replacement(match: re.Match[str]) -> str:
        path = match.group()
        for marker in ("/src/", "/site-packages/"):
            if marker in path:
                return marker.strip("/") + "/" + path.split(marker, 1)[1]
        return "local/" + path.rsplit("/", 1)[-1]

    return PRIVATE_PATH.sub(replacement, value)


def redact_debug_pickle(data: bytes) -> bytes:
    """Rewrite string opcodes without executing pickle instructions."""
    operations = list(pickletools.genops(data))
    if any(op.name == "FRAME" for op, _, _ in operations):
        raise ValueError("framed debug pickles require a separate reviewed implementation")
    result = bytearray()
    for index, (opcode, value, start) in enumerate(operations):
        end = operations[index + 1][2] if index + 1 < len(operations) else len(data)
        if isinstance(value, str) and redact_text(value) != value:
            if opcode.name not in {"BINUNICODE", "SHORT_BINUNICODE", "BINUNICODE8"}:
                raise ValueError("unsupported private-path string opcode")
            encoded = redact_text(value).encode("utf-8")
            result.extend(b"X" + struct.pack("<I", len(encoded)) + encoded)
        else:
            result.extend(data[start:end])
    return bytes(result)


def redact_actor(data: bytes) -> tuple[bytes, int]:
    """Change only TorchScript debug records; retain every other member verbatim."""
    destination = io.BytesIO()
    changes = 0
    with zipfile.ZipFile(io.BytesIO(data)) as source, zipfile.ZipFile(destination, "w") as target:
        for member in source.infolist():
            content = source.read(member)
            updated = (
                redact_debug_pickle(content) if member.filename.endswith(".debug_pkl") else content
            )
            changes += updated != content
            target.writestr(member, updated)
    return destination.getvalue(), changes


def redact_elf(data: bytes) -> tuple[bytes, int]:
    """Erase unused old RPATH strings after verifying dynamic references."""
    if data[:6] != b"\x7fELF\x02\x01":
        raise ValueError("only little-endian ELF64 is supported")
    offset = struct.unpack_from("<Q", data, 40)[0]
    size, count, names_index = struct.unpack_from("<HHH", data, 58)
    sections = [struct.unpack_from("<IIQQQQIIQQ", data, offset + i * size) for i in range(count)]
    names_header = sections[names_index]
    names = data[names_header[4] : names_header[4] + names_header[5]]
    named = {names[h[0] :].split(b"\0", 1)[0].decode(): h for h in sections}
    strings = named[".dynstr"]
    references: set[int] = set()
    dynamic = named[".dynamic"]
    for position in range(dynamic[4], dynamic[4] + dynamic[5], dynamic[9]):
        tag, value = struct.unpack_from("<qQ", data, position)
        if tag in {15, 29}:
            raise ValueError("refusing an ELF with a live RPATH or RUNPATH")
        if tag in {1, 14}:
            references.add(value)
    symbols = named[".dynsym"]
    for position in range(symbols[4], symbols[4] + symbols[5], symbols[9]):
        references.add(struct.unpack_from("<I", data, position)[0])
    result = bytearray(data)
    changes = 0
    pattern = re.compile(rb"/(?:root|home/[^/\x00]+)/[^\x00]+")
    for match in pattern.finditer(data):
        start, end = match.span()
        if not strings[4] <= start < end <= strings[4] + strings[5]:
            raise ValueError("private ELF path outside the reviewed dynamic string table")
        if any(start <= strings[4] + ref < end for ref in references):
            raise ValueError("private ELF path is referenced by a dynamic symbol or library")
        result[start:end] = b"\0" * (end - start)
        changes += 1
    return bytes(result), changes
