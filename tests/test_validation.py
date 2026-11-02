"""Numeric validator boundaries, output types and field-specific messages."""

from decimal import Decimal

import pytest

from pmi_estimator.validation import (
    validate_employee_cost,
    validate_employee_count,
    validate_pmi_budget,
    validate_renewal_change,
    validate_take_up,
)


@pytest.mark.parametrize(
    "budget, expected",
    [
        (0, "0"),
        (0.0, "0"),
        (120000, "120000"),
        (120000.50, "120000.50"),
        (0.01, "0.01"),
        (0.29, "0.29"),
    ],
)
def test_numeric_budget_accepts_valid_amounts(budget: float, expected: str) -> None:
    """Allow zero and preserve penny amounts without float artefacts."""
    result = validate_pmi_budget(budget)
    assert isinstance(result, Decimal)
    assert result == Decimal(expected)


@pytest.mark.parametrize(
    "budget, message",
    [
        (None, "required"),
        (-1, "non-negative"),
        (-0.01, "non-negative"),
        (12.345, "at most 2 decimal places"),
        (0.001, "at most 2 decimal places"),
        (float("nan"), "finite"),
        (float("inf"), "finite"),
        (float("-inf"), "finite"),
    ],
)
def test_numeric_budget_rejects_invalid_amounts(
    budget: float | None, message: str
) -> None:
    """Report invalid numeric inputs rather than rounding or accepting them."""
    with pytest.raises(ValueError, match=message):
        validate_pmi_budget(budget)


@pytest.mark.parametrize(
    "cost, expected",
    [(0.01, "0.01"), (0.29, "0.29"), (1000, "1000"), (1000.50, "1000.50")],
)
def test_numeric_employee_cost_accepts_valid_amounts(
    cost: float, expected: str
) -> None:
    """Preserve positive penny amounts as Decimal, including the minimum."""
    result = validate_employee_cost(cost)
    assert isinstance(result, Decimal)
    assert result == Decimal(expected)


@pytest.mark.parametrize(
    "cost, message",
    [
        (None, "required"),
        (0, "greater than zero"),
        (-1, "greater than zero"),
        (12.345, "at most 2 decimal places"),
        (0.001, "at most 2 decimal places"),
        (float("nan"), "finite"),
        (float("inf"), "finite"),
        (float("-inf"), "finite"),
    ],
)
def test_numeric_employee_cost_rejects_invalid_amounts(
    cost: float | None, message: str
) -> None:
    """Reject missing, non-positive, non-finite and sub-penny costs."""
    with pytest.raises(ValueError, match=message):
        validate_employee_cost(cost)


@pytest.mark.parametrize("renewal", [0, 10, 150, -10, -99.99, 0.5, 12.345])
def test_numeric_renewal_accepts_valid_changes(renewal: float) -> None:
    """Preserve percentage points, reductions and fractional percentages."""
    assert validate_renewal_change(renewal) == renewal


@pytest.mark.parametrize(
    "renewal, message",
    [
        (None, "required"),
        (-100, "greater than -100%"),
        (-100.01, "greater than -100%"),
        (float("nan"), "finite"),
        (float("inf"), "finite"),
        (float("-inf"), "finite"),
    ],
)
def test_numeric_renewal_rejects_invalid_changes(
    renewal: float | None, message: str
) -> None:
    """Reject missing, non-finite and out-of-range renewal assumptions."""
    with pytest.raises(ValueError, match=message):
        validate_renewal_change(renewal)


@pytest.mark.parametrize(
    "count, expected",
    [(0, 0), (0.0, 0), (5, 5), (5.0, 5), (1000, 1000)],
)
def test_numeric_employee_count_accepts_whole_values(
    count: float, expected: int
) -> None:
    """Accept whole-valued numeric inputs and return an actual integer."""
    result = validate_employee_count(count)
    assert result == expected
    assert isinstance(result, int)


@pytest.mark.parametrize(
    "count, message",
    [
        (None, "required"),
        (-1, "non-negative"),
        (-0.5, "non-negative"),
        (5.7, "whole number"),
        (0.5, "whole number"),
        (float("nan"), "finite"),
        (float("inf"), "finite"),
        (float("-inf"), "finite"),
    ],
)
def test_numeric_employee_count_rejects_invalid_values(
    count: float | None, message: str
) -> None:
    """Reject fractional counts without truncation and report invalid inputs."""
    with pytest.raises(ValueError, match=message):
        validate_employee_count(count)


@pytest.mark.parametrize(
    "field_name",
    ["Currently covered employees", "Additional employees eligible for cover"],
)
@pytest.mark.parametrize(
    "count, reason",
    [
        (None, "is required."),
        (-1, "must be non-negative."),
        (1.5, "must be a whole number."),
        (float("inf"), "must be finite."),
    ],
)
def test_numeric_employee_count_errors_identify_the_field(
    field_name: str, count: float | None, reason: str
) -> None:
    """Both employee groups receive messages naming the affected field."""
    with pytest.raises(ValueError) as error:
        validate_employee_count(count, field_name=field_name)
    assert str(error.value) == f"{field_name} {reason}"


@pytest.mark.parametrize("take_up", [0, 50, 100, 0.5])
def test_numeric_take_up_accepts_valid_percentages(take_up: float) -> None:
    """Accept inclusive boundaries and preserve fractional percentage points."""
    assert validate_take_up(take_up) == take_up


@pytest.mark.parametrize(
    "take_up, message",
    [
        (None, "required"),
        (-0.01, "between 0 and 100%"),
        (100.01, "between 0 and 100%"),
        (float("nan"), "finite"),
        (float("inf"), "finite"),
        (float("-inf"), "finite"),
    ],
)
def test_numeric_take_up_rejects_invalid_percentages(
    take_up: float | None, message: str
) -> None:
    """Reject missing, non-finite and out-of-range take-up assumptions."""
    with pytest.raises(ValueError, match=message):
        validate_take_up(take_up)
