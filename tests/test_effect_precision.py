"""Precision scopes must restore each rollout thread's own state."""

from concurrent.futures import ThreadPoolExecutor
from threading import Event

import pytest
import torch

from kagg_revue.policy.effects.precision import full_precision


@pytest.mark.skipif(not torch.cuda.is_available(), reason="CUDA autocast state")
def test_full_precision_restores_overlapping_thread_scopes() -> None:
    first_entered = Event()
    second_entered = Event()
    first_exited = Event()

    @full_precision
    def region(first: bool) -> None:
        assert not torch.is_autocast_enabled("cuda")
        if first:
            first_entered.set()
            assert second_entered.wait(5)
        else:
            second_entered.set()
            assert first_exited.wait(5)

    def run_first() -> bool:
        try:
            with torch.autocast("cuda", enabled=True):
                region(True)
                return torch.is_autocast_enabled("cuda")
        finally:
            first_exited.set()

    def run_second() -> bool:
        assert first_entered.wait(5)
        with torch.autocast("cuda", enabled=False):
            region(False)
            return torch.is_autocast_enabled("cuda")

    with ThreadPoolExecutor(max_workers=2) as executor:
        first = executor.submit(run_first)
        second = executor.submit(run_second)
        assert first.result()
        assert not second.result()
