"""Stable precision at sharp policy and replay boundaries."""

from collections.abc import Callable
from functools import wraps
from typing import ParamSpec, TypeVar

import torch

_P = ParamSpec("_P")
_R = TypeVar("_R")


def full_precision(function: Callable[_P, _R]) -> Callable[_P, _R]:
    """Keep sharp pointer distributions stable across rollout and learner shapes."""

    @wraps(function)
    def wrapped(*args: _P.args, **kwargs: _P.kwargs) -> _R:
        # Autocast stores the previous thread state on the context instance.
        # Sharing a decorator's instance races when rollout threads overlap.
        with torch.autocast("cuda", enabled=False):
            return function(*args, **kwargs)

    return wrapped
