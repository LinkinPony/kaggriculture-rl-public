"""Fixed-shape policy inference and causal device-to-environment handshakes."""

import math
import time
from typing import Literal

import torch
from torch import Tensor

from kagg_revue.policy.capture import GraphCapture
from kagg_revue.policy.memory.policy import MemoryPolicy, RecurrentExecution
from kagg_revue.policy.spatial.model import Policy


class ActorRuntime:
    """One fixed-shape graph; only the selected contract returns to the native loop."""

    def __init__(
        self,
        policy: Policy,
        count: int,
        *,
        sample: bool,
        temperature: float = 1.0,
        dynamic_temperature: bool = False,
        precision: Literal["bf16", "fp32"] = "bf16",
        bf16_reduced_precision_reduction: bool = True,
        compile_inference: bool = False,
    ) -> None:
        """Capture stable inference buffers without retaining graph shape variants."""
        if not math.isfinite(temperature) or temperature < 0:
            raise ValueError("policy temperature must be finite and nonnegative")
        self.policy = policy
        self.temperature = temperature
        self.device = next(policy.parameters()).device
        self.temperature_control = (
            torch.tensor(temperature, device=self.device) if dynamic_temperature else None
        )
        sampling_temperature = (
            self.temperature_control if self.temperature_control is not None else temperature
        )
        if self.device.type == "cuda":
            torch.backends.cuda.matmul.allow_bf16_reduced_precision_reduction = (
                bf16_reduced_precision_reduction
            )
        self.host = torch.empty(
            (count, policy.layout.observation.features),
            dtype=torch.float16,
            pin_memory=self.device.type == "cuda",
        )
        self.observations = self.host.to(self.device)
        self.steps = torch.zeros(count, dtype=torch.long, device=self.device)
        self.selected = torch.empty(
            (count, policy.layout.factors), dtype=torch.long, pin_memory=self.device.type == "cuda"
        )
        self.sample = sample
        self.last_decision: int | None = None
        self.memory = (
            RecurrentExecution(
                policy,
                count,
                self.device,
                torch.bfloat16
                if self.device.type == "cuda" and precision == "bf16"
                else torch.float32,
            )
            if isinstance(policy, MemoryPolicy)
            else None
        )
        self.graph: torch.cuda.CUDAGraph | None = None
        self.capture: GraphCapture | None = None
        started = time.perf_counter()
        policy.eval()
        # Recurrent training compiles bounded components. Inference captures those
        # components in a CUDA graph without rebuilding one enormous Dynamo graph.
        if policy.layout.network.memory_turns:
            compile_inference = False
        operation = self.memory.act if self.memory is not None else policy.act
        act = (
            torch.compile(
                operation, fullgraph=True, dynamic=False, options={"triton.cudagraphs": False}
            )
            if compile_inference
            else operation
        )
        with (
            torch.no_grad(),
            torch.autocast(
                self.device.type,
                dtype=torch.bfloat16,
                enabled=self.device.type == "cuda" and precision == "bf16",
                # Cast parameters inside the graph on every replay. The autocast
                # cache otherwise lends uncaptured buffers that become stale or freed.
                cache_enabled=False,
            ),
        ):
            if self.device.type == "cuda":
                rng = torch.cuda.get_rng_state(self.device)
                self.observations.zero_()
                self.capture = GraphCapture(self.device)
                stream = self.capture.stream
                stream.wait_stream(torch.cuda.current_stream(self.device))
                with torch.cuda.stream(stream):
                    for _ in range(3):
                        act(
                            self.observations,
                            self.steps,
                            sample=sample,
                            temperature=sampling_temperature,
                        )
                torch.cuda.current_stream(self.device).wait_stream(stream)
                self.graph = self.capture.graph
                # cuBLAS workspaces are tied to their capture stream, outside the
                # graph's allocator pool. Separate policy graphs can overlap only
                # when they are captured on their own warmed, nonpooled streams.
                with torch.cuda.graph(self.graph, stream=stream):
                    self.actions, self.log_probabilities = act(
                        self.observations,
                        self.steps,
                        sample=sample,
                        temperature=sampling_temperature,
                    )
                torch.cuda.synchronize(self.device)
                torch.cuda.set_rng_state(rng, self.device)
        if self.memory is not None:
            self.memory.reset()
        reset = getattr(policy, "reset_memory", None)
        if reset is not None:
            reset()
        self.capture_seconds = time.perf_counter() - started

    def set_temperature(self, temperature: float) -> None:
        """Update one resident scalar between complete rollouts without recapturing."""
        if not math.isfinite(temperature) or temperature < 0:
            raise ValueError("policy temperature must be finite and nonnegative")
        if self.temperature_control is None:
            if temperature != self.temperature:
                raise ValueError("changing a captured temperature requires a dynamic runtime")
        else:
            self.temperature_control.fill_(temperature)
        self.temperature = temperature

    def act(self, decision: int, *, synchronize: bool = True) -> tuple[Tensor, Tensor]:
        """Return selected fields after the one causal device synchronization."""
        recurrent = (
            self.memory is not None or getattr(self.policy, "reset_memory", None) is not None
        )
        if recurrent and decision != 0 and self.last_decision != decision - 1:
            raise ValueError("recurrent inference requires contiguous turns from the episode start")
        self.last_decision = decision
        if self.memory is not None and decision == 0:
            self.memory.reset()
        if decision == 0 and (reset := getattr(self.policy, "reset_memory", None)) is not None:
            reset()
        self.observations.copy_(self.host, non_blocking=True)
        self.steps.fill_(decision)
        if self.graph is not None:
            self.graph.replay()
        else:
            with torch.no_grad():
                operation = self.memory.act if self.memory is not None else self.policy.act
                self.actions, self.log_probabilities = operation(
                    self.observations,
                    self.steps,
                    sample=self.sample,
                    temperature=self.temperature_control
                    if self.temperature_control is not None
                    else self.temperature,
                )
        self.selected.copy_(self.actions, non_blocking=self.device.type == "cuda")
        if self.device.type == "cuda" and synchronize:
            torch.cuda.current_stream(self.device).synchronize()
        return self.actions, self.log_probabilities
