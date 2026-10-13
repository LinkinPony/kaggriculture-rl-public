"""Typing surface for the Hopper conditional CUDA graph helper."""


class ConditionalWhileGraph:
    """One device-controlled while graph around a captured body graph."""

    def __init__(
        self,
        body_graph: int,
        state: int,
        rows: int,
        state_width: int,
    ) -> None: ...

    def launch(self, stream: int) -> None: ...


class ConditionalSwitchWhileGraph:
    """Device while-loop dispatching one active-row batch specialization."""

    def __init__(
        self,
        setup_graph: int,
        variant_graphs: list[int],
        state: int,
        active_count: int,
        rows: int,
        state_width: int,
    ) -> None: ...

    def launch(self, stream: int) -> None: ...


class ConditionalCountSwitchWhileGraph:
    """Device while-loop dispatched by the maximum live candidate count."""

    def __init__(
        self,
        setup_graphs: list[int],
        setup_variant: int,
        variant_graphs: list[int],
        live_count: int,
        continuation_count: int,
        initial_capacity: int,
    ) -> None: ...

    def launch(self, stream: int) -> None: ...
