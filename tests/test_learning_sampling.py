import pytest
import torch

from kagg_revue.policy.spatial.model import sample_categorical


@pytest.mark.parametrize("temperature", [1.0, torch.tensor(1.0)])
@pytest.mark.parametrize("endpoint_kind", ["zero", "infinity"])
def test_exponential_endpoints_cannot_select_masked_fields(monkeypatch, temperature, endpoint_kind):
    # Zero noise on a masked field wins; infinite noise on the only legal field
    # loses to every masked field. Both endpoints must preserve singleton support.
    scores = torch.tensor([[2.0, -1e9, -1e9], [-1e9, 3.0, -1e9]])

    def endpoint(self, *args, **kwargs):
        values = (1.0, 0.0) if endpoint_kind == "zero" else (torch.inf, 1.0)
        return self.copy_(torch.where(scores > -1e9, *values))

    monkeypatch.setattr(torch.Tensor, "exponential_", endpoint)
    torch.testing.assert_close(sample_categorical(scores, temperature), torch.tensor([0, 1]))
