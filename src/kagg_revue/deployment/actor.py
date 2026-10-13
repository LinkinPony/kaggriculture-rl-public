"""Single-observation CPU export with an explicit deployment temperature."""

import copy
import math
from pathlib import Path

import torch
from torch import Tensor, nn

from kagg_revue.deployment.recurrent import RecurrentActor, empty_inputs
from kagg_revue.policy.grounded.normalization import LayerNorm
from kagg_revue.policy.memory.policy import MemoryPolicy
from kagg_revue.policy.spatial.model import Policy


class SampledActor(nn.Module):
    """Apply sampled or greedy selection to each learned conditional distribution."""

    def __init__(self, policy: Policy, temperature: float = 1.0) -> None:
        """Keep the exact registered model and its learned action biases."""
        super().__init__()
        self.policy = policy
        self.temperature = temperature

    def forward(self, observations: Tensor, steps: Tensor) -> Tensor:
        """Use conditional argmax at zero, otherwise the training Gumbel sampler."""
        return self.policy.act(
            observations,
            steps,
            sample=self.temperature > 0,
            temperature=self.temperature if self.temperature > 0 else 1.0,
        )[0]


def freeze(policy: Policy, path: Path, *, temperature: float = 1.0) -> None:
    """Serialize a batch-one FP32 CPU actor at the requested fixed temperature."""
    if not math.isfinite(temperature) or temperature < 0:
        raise ValueError("deployment temperature must be finite and nonnegative")
    if next(policy.parameters()).device.type != "cpu":
        raise ValueError("CPU export requires a CPU policy")
    observations = torch.zeros((1, policy.layout.observation.features), dtype=torch.float16)
    steps = torch.zeros(1, dtype=torch.long)
    exported = copy.deepcopy(policy).eval()
    for name, module in list(exported.named_modules()):
        if isinstance(module, LayerNorm):
            # The training-only fusion boundary calls the same native LayerNorm.
            # Export its built-in equivalent so a fresh Torch process needs no
            # repository custom-op registration to load or execute this actor.
            assert module.weight is not None
            replacement = nn.LayerNorm(
                module.normalized_shape,
                eps=module.eps,
                device=module.weight.device,
                dtype=module.weight.dtype,
            )
            replacement.load_state_dict(module.state_dict(), strict=True)
            exported.set_submodule(name, replacement.eval())
    with torch.inference_mode():
        # Trace checking draws different randomness; complete trajectory checks
        # compare the serialized actor with eager inference under identical RNG.
        actor: nn.Module
        inputs: tuple[Tensor, ...] = (observations, steps)
        if isinstance(exported, MemoryPolicy):
            actor = RecurrentActor(exported, temperature).eval()
            inputs = (*inputs, *empty_inputs(exported))
        else:
            actor = SampledActor(exported, temperature).eval()
        traced = torch.jit.trace(actor, inputs, check_trace=False)  # type: ignore[no-untyped-call]
        torch.jit.freeze(traced).save(str(path))
