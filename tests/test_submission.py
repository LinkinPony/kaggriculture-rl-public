import sys
from pathlib import Path

from kagg_revue.submission.agent import _plain
from kagg_revue.submission.package import _ENTRYPOINT


def test_plain_normalizes_only_lossless_integral_floats() -> None:
    value = {
        "money": 3000.0,
        "price": 25.0,
        "chance": 0.005,
        "nested": [1.0, 1.5],
    }

    normalized = _plain(value)

    assert normalized == {
        "money": 3000,
        "price": 25,
        "chance": 0.005,
        "nested": [1, 1.5],
    }


def test_entrypoint_supports_kaggle_raw_execution() -> None:
    repository_root = Path(__file__).resolve().parents[1]
    environment: dict[str, object] = {}
    original_sys_path = sys.path.copy()
    try:
        sys.path.append(str(repository_root))
        exec(compile(_ENTRYPOINT, "main.py", "exec"), environment)  # noqa: S102
    finally:
        sys.path[:] = original_sys_path

    callables = [value for value in environment.values() if callable(value)]

    assert callables[-1] is environment["agent"]
