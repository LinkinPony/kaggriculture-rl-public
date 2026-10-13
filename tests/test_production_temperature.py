import math

import pytest
import torch

from kagg_revue.production.model import Policy, log_probabilities, sample_categorical
from kagg_revue.production.runtime import ActorRuntime
from kagg_revue.production.temperature import log_cosine_temperature
from test_production_work import _layout


def test_temperature_has_greedy_warmup_inclusive_endpoints_and_reproducible_resume() -> None:
    def temperature(update: int) -> float:
        return log_cosine_temperature(update, greedy_updates=2, end_update=11, start=0.07, stop=0.8)

    uninterrupted = [temperature(update) for update in range(1, 16)]
    assert uninterrupted[:2] == [0.0, 0.0]
    assert temperature(3) == pytest.approx(0.07)
    assert temperature(7) == pytest.approx(math.sqrt(0.07 * 0.8))
    assert temperature(11) == temperature(15) == 0.8
    assert all(a <= b for a, b in zip(uninterrupted, uninterrupted[1:], strict=False))
    resumed = [temperature(update) for update in range(8, 16)]
    assert resumed == uninterrupted[7:]
    with pytest.raises(ValueError):
        log_cosine_temperature(1, greedy_updates=2, end_update=3, start=0.1, stop=1.0)
    with pytest.raises(ValueError):
        log_cosine_temperature(1, greedy_updates=0, end_update=3, start=0.0, stop=1.0)


def test_zero_temperature_is_a_point_mass_and_live_temperature_matches_likelihood() -> None:
    logits = torch.tensor([[0.2, 0.2, -0.7], [-0.5, 0.1, 0.4]])
    for temperature in (0.0, torch.tensor(0.0)):
        selected = sample_categorical(logits, temperature)
        assert torch.equal(selected, logits.argmax(-1))
        assert not log_probabilities(logits, selected, temperature).any()
        assert torch.isneginf(log_probabilities(logits, (selected + 1) % 3, temperature)).all()
    repeated = torch.tensor([1.0, 3.0]).log().expand(16000, -1)
    control = torch.tensor(0.25)
    for temperature in (0.25, 0.8):
        control.fill_(temperature)
        with torch.random.fork_rng(devices=[]):
            torch.manual_seed(7)
            actions = sample_categorical(repeated, control)
        expected = (repeated[0] / temperature).softmax(-1)
        observed = torch.bincount(actions, minlength=2).float() / len(actions)
        torch.testing.assert_close(observed, expected, atol=0.01, rtol=0)
        torch.testing.assert_close(
            log_probabilities(repeated, actions, control).exp(), expected[actions]
        )


@pytest.mark.skipif(not torch.cuda.is_available(), reason="live temperature requires CUDA capture")
def test_one_cuda_graph_tracks_temperature_and_replays_conditional_behavior() -> None:
    policy = Policy.from_layout(_layout()).cuda()
    for parameter in policy.parameters():
        torch.nn.init.normal_(parameter, std=0.05)
    runtime = ActorRuntime(policy, 3, sample=True, temperature=0.0, dynamic_temperature=True)
    runtime.host.copy_(torch.randn_like(runtime.host))
    graph = runtime.graph
    control_address = runtime.temperature_control.data_ptr()
    for temperature in (0.0, 0.13, 0.8, 0.0):
        runtime.set_temperature(temperature)
        with torch.no_grad(), torch.autocast("cuda", dtype=torch.bfloat16, cache_enabled=False):
            chosen, actual = runtime.act(0)
            if temperature == 0:
                greedy, _ = policy.act(runtime.observations, runtime.steps, sample=False)
                torch.testing.assert_close(chosen, greedy)
                assert not actual.any()
            else:
                expected = log_probabilities(
                    policy(runtime.observations, runtime.steps, chosen), chosen, temperature
                )
                torch.testing.assert_close(actual, expected, atol=3e-4, rtol=3e-4)
        assert runtime.graph is graph
        assert runtime.temperature_control.data_ptr() == control_address
