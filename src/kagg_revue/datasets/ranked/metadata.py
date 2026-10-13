"""Read small provenance headers without decoding complete replay trajectories."""

import codecs
import gzip
import json
import re
import zipfile
from pathlib import Path
from typing import Any


def replay_header(path: Path, member: str | None = None) -> dict[str, Any]:
    """Extract official replay identity and statuses from the bounded JSON prefix."""
    if member:
        with zipfile.ZipFile(path) as archive, archive.open(member) as stream:
            raw = stream.read(65536)
    else:
        with gzip.open(path, "rb") as stream:
            raw = stream.read(65536)
    prefix = codecs.getincrementaldecoder("utf-8")().decode(raw, final=False)
    fields = {}
    for name in ("info", "statuses"):
        match = re.search(r'"' + name + r'"\s*:\s*', prefix)
        if match is None:
            raise ValueError(f"replay lacks {name} in its metadata prefix: {path}:{member}")
        fields[name] = json.JSONDecoder().raw_decode(prefix[match.end() :])[0]
    expected = int(Path(member).stem if member else path.name.split(".")[0])
    if int(fields["info"]["EpisodeId"]) != expected:
        raise ValueError("replay identity differs from its filename or archive member")
    return fields
