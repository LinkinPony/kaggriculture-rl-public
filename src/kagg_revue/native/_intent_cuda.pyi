"""Typing surface for fused canonical-intent CUDA kernels."""


class IntentTransactionKernels:
    """Fixed-address candidate and transition kernels for one collector."""

    def __init__(
        self,
        pointers: dict[str, int],
        dimensions: dict[str, int],
    ) -> None: ...

    def candidates(self, stream: int, capacity: int) -> None: ...

    def transition(
        self,
        stream: int,
        candidate_fields: int,
        selected: int,
        log_probability: int,
        value: int,
    ) -> None: ...
