"""Hardware execution controls, separate from the statistical training budget."""

from typing import Literal

from pydantic import Field, model_validator

from kagg_revue.configuration import FrozenSettings


class Execution(FrozenSettings):
    """Use synchronous GPU shards and bounded CPU pools for one policy."""

    devices: tuple[str, ...] = ("cuda:0", "cuda:1")
    microbatch_rows: int = Field(default=5760, gt=0)
    workers_per_rank: int = Field(default=8, gt=0)
    cpu_threads_per_rank: int = Field(default=2, gt=0)
    compile_inference: bool = True
    fused_loss: bool = True
    pipeline_groups: Literal[1, 2] = 1
    async_checkpoint: bool = False

    @model_validator(mode="after")
    def validate_devices(self) -> "Execution":
        """Require distinct explicit CUDA indices and equal microbatch shards."""
        if (
            not self.devices
            or len(set(self.devices)) != len(self.devices)
            or any(not d.startswith("cuda:") or not d[5:].isdigit() for d in self.devices)
            or self.microbatch_rows % len(self.devices)
        ):
            raise ValueError("execution requires unique CUDA devices and divisible microbatches")
        return self
