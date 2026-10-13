from kagg_revue.core.observability import numeric_metrics, throughput


def test_numeric_metrics_flattens_only_scalar_values() -> None:
    values = {
        "loss": 1.5,
        "stage": {"rate": 4, "enabled": True},
        "identity": "ignored",
        "seeds": [1, 2],
    }

    assert numeric_metrics(values) == {
        "loss": 1.5,
        "stage/rate": 4.0,
        "stage/enabled": 1.0,
    }


def test_throughput_handles_a_zero_duration() -> None:
    assert throughput(3, 0.0) == 0.0
    assert throughput(3, 1.5) == 2.0
