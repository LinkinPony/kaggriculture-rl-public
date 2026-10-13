import torch

from kagg_revue.rl.reward import margin_augmented_return, margin_augmented_returns


def test_margin_augmented_return_is_bounded_odd_and_orders_equal_outcomes() -> None:
    cash_differences = torch.tensor([-40.0, -5.0, 0.0, 5.0, 40.0])
    outcomes = torch.sign(cash_differences).to(dtype=torch.int64)

    returns = margin_augmented_returns(
        outcomes,
        cash_differences,
        beta=1.0,
        cash_scale=20.0,
    )

    assert torch.all(returns[1:] > returns[:-1])
    assert torch.all(returns.abs() <= 2.0)
    torch.testing.assert_close(returns, -returns.flip(0))
    assert returns[2] == 0.0
    torch.testing.assert_close(
        torch.tensor(
            margin_augmented_return(
                -1,
                -5.0,
                beta=1.0,
                cash_scale=20.0,
            )
        ),
        returns[1],
    )


def test_margin_augmented_return_rejects_outcome_cash_disagreement() -> None:
    try:
        margin_augmented_return(
            1,
            -1.0,
            beta=1.0,
            cash_scale=2.0,
        )
    except ValueError as error:
        assert "cash-difference sign" in str(error)
    else:
        raise AssertionError("inconsistent terminal outcome was accepted")
