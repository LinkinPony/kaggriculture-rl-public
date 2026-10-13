"""Check that privacy edits cannot silently alter model payloads."""

import io
import pickle
import zipfile

import pytest

from kagg_revue.release.redaction import redact_actor, redact_debug_pickle


def test_debug_paths_preserve_pickle_structure_and_shared_references() -> None:
    """Keep range records and memoized references when shortening filenames."""
    path = "/home/example/build/src/kagg_revue/policy/model.py"
    value = (path, [path, 17, "model.forward(x)"])
    result = pickle.loads(redact_debug_pickle(pickle.dumps(value, protocol=2)))
    assert result == (
        "src/kagg_revue/policy/model.py",
        ["src/kagg_revue/policy/model.py", 17, "model.forward(x)"],
    )
    assert result[0] is result[1][0]


def test_actor_keeps_weights_and_executable_code_verbatim() -> None:
    """Only debug metadata may differ inside the reserialized TorchScript ZIP."""
    source = io.BytesIO()
    entries = {
        "actor/data/0": bytes(range(256)),
        "actor/code/model.py": b"def forward(x): return x + 1\n",
        "actor/code/model.py.debug_pkl": pickle.dumps("/home/example/model.py", protocol=2),
    }
    with zipfile.ZipFile(source, "w") as archive:
        for name, content in entries.items():
            archive.writestr(name, content)
    data, count = redact_actor(source.getvalue())
    assert count == 1
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        for name, content in entries.items():
            if not name.endswith(".debug_pkl"):
                assert archive.read(name) == content


def test_framed_pickle_fails_closed() -> None:
    """Reject unsupported framing instead of producing corrupt debug records."""
    with pytest.raises(ValueError, match="framed"):
        redact_debug_pickle(pickle.dumps("/home/example/model.py", protocol=4))
