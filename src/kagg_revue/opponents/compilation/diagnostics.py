"""Compare controller decisions as well as externally visible policy actions."""

from types import FunctionType
from typing import Any, cast

from kagg_revue.opponents.public import PublicAgentRuntime


def stable(value: Any) -> Any:
    """Remove wall-clock measurements while preserving strategy diagnostics."""
    if isinstance(value, dict):
        return {
            key: stable(item) for key, item in value.items() if not str(key).endswith("planning_ms")
        }
    if isinstance(value, (list, tuple)):
        return [stable(item) for item in value]
    return value


def source_diagnostics(runtime: PublicAgentRuntime) -> dict[str, Any]:
    """Inspect the original module only in offline conformance qualification."""
    namespace = cast(FunctionType, runtime._function).__globals__
    result = {
        key: value
        for key, value in namespace.items()
        if isinstance(value, dict) and key.endswith(("REPORT", "STATS"))
    }
    if "_IMPL" in namespace:
        result["chassis"] = namespace["_IMPL"].chassis.diagnostics
    return cast(dict[str, Any], stable(result))
