"""Independent recurrent state and action-prefix terminal value prediction."""

from torch import Tensor

from kagg_revue.learning.optimization.prefix import PrefixCritic
from kagg_revue.policy.contracts import ContractLayout
from kagg_revue.policy.grounded.encoder import ContextEncoder
from kagg_revue.policy.memory.scene import SceneMemory
from kagg_revue.policy.memory.temporal import MemoryState


class MemoryCritic(PrefixCritic):
    """Use an independent memory without consuming the current action in state values."""

    def __init__(self, layout: ContractLayout) -> None:
        """Retain the established exclusive action-prefix head."""
        super().__init__(layout)
        self.memory = SceneMemory(layout.network.critic_width, layout.network)

    def sequence(
        self,
        observations: Tensor,
        steps: Tensor,
        state: MemoryState,
        actions: Tensor,
        fields: Tensor,
    ) -> tuple[Tensor, Tensor, MemoryState]:
        """Predict each pre-choice value from causal observations and action prefixes."""
        turns, batch = observations.shape[:2]
        assert isinstance(self.entity_encoder, ContextEncoder)
        encoded, valid = self.entity_encoder.tokens(observations.flatten(0, 1))
        encoded, next_state = self.memory(
            encoded.reshape(turns, batch, *encoded.shape[1:]),
            valid.reshape(turns, batch, -1),
            state,
            steps,
        )
        value, prefixes = self.prefixes_encoded(
            encoded.flatten(0, 1),
            actions.flatten(0, 1),
            fields.flatten(0, 1),
        )
        return value.reshape(turns, batch), prefixes.reshape(turns, batch, -1), next_state
