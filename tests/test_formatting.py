"""Display formatting independent of Shiny runtime."""

from decimal import Decimal

import pytest

from pmi_estimator.formatting import format_budget_outcome, format_membership


@pytest.mark.parametrize(
    "value, expected",
    [
        ("1000", "£1,000.00 budget remaining"),
        ("-1000", "£1,000.00 over budget"),
        ("0", "Estimated cost matches your budget"),
        ("0.004", "Less than £0.01 budget remaining"),
        ("-0.005", "Less than £0.01 over budget"),
        ("0.01", "£0.01 budget remaining"),
        ("-0.01", "£0.01 over budget"),
    ],
)
def test_budget_outcome(value: str, expected: str) -> None:
    """Distinguish remaining budget, overspend and exact balance for users."""
    assert format_budget_outcome(Decimal(value)) == expected


@pytest.mark.parametrize(
    "value, expected",
    [
        ("0.00", "0"),
        ("30.00", "30"),
        ("1.50", "1.5"),
        ("1234.5670", "1,234.567"),
        ("1000", "1,000"),
        ("0.000001", "0.000001"),
    ],
)
def test_membership_formatting(value: str, expected: str) -> None:
    """Remove trailing zeros without rounding fractional membership."""
    assert format_membership(Decimal(value)) == expected
