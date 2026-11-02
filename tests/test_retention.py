"""Compare retention-based places with reserving cover for all current members."""

from decimal import Decimal

import pytest

from pmi_estimator.calculations import (
    calculate_expected_retained_members,
    calculate_retention_based_additional_places,
)
from pmi_estimator.results import calculate_scenario
from pmi_estimator.validation import validate_retention


@pytest.mark.parametrize("value", [0, 90, 100, 87.5])
def test_valid_retention(value: float) -> None:
    assert validate_retention(value) == value


@pytest.mark.parametrize(
    "value, message",
    [
        (None, "required"),
        (-0.01, "between 0 and 100"),
        (100.01, "between 0 and 100"),
        (float("nan"), "finite"),
        (float("inf"), "finite"),
        (float("-inf"), "finite"),
    ],
)
def test_invalid_retention(value: float | None, message: str) -> None:
    with pytest.raises(ValueError, match=message):
        validate_retention(value)


@pytest.mark.parametrize(
    "count, percent, expected",
    [(80, 100, "80"), (80, 90, "72"), (80, 0, "0"), (3, 50, "1.5"), (0, 90, "0")],
)
def test_retained_members(count: int, percent: float, expected: str) -> None:
    assert calculate_expected_retained_members(count, percent) == Decimal(expected)


@pytest.mark.parametrize(
    "retention, retained, total, cost, balance, retention_places",
    [
        (100, "80", "110", "121000", "-1000", 29),
        (90, "72", "102", "112200", "7800", 37),
        (0, "0", "30", "33000", "87000", 40),
        (87.5, "70", "100", "110000", "10000", 39),
    ],
)
def test_retention_scenario_reference_results(
    retention: float,
    retained: str,
    total: str,
    cost: str,
    balance: str,
    retention_places: int,
) -> None:
    result = calculate_scenario(
        annual_budget=Decimal(120000),
        current_annual_unit_cost=Decimal(1000),
        current_covered_employees=80,
        additional_eligible_employees=40,
        take_up_percent=75,
        renewal_percent=10,
        retention_percent=retention,
    )
    assert result.retained_members == Decimal(retained)
    assert result.total_coverage == Decimal(total)
    assert result.expected_cost == Decimal(cost)
    assert result.balance == Decimal(balance)
    # Conservative places reserve everyone; forecast-based places may increase.
    assert result.retention_based_additional_places == retention_places
    assert result.retained_cost == Decimal(retained) * Decimal(1100)
    assert result.retention_based_enrolment_gap == (
        Decimal(1) if retention == 100 else Decimal(0)
    )
    assert result.capacity == 109
    assert result.additional_places == 29
    assert result.additional_enrolment_gap == Decimal(1)
    assert result.full_cost == Decimal(132000)
    assert result.full_balance == Decimal(-12000)
    assert result.existing_cost == Decimal(88000)


def test_fractional_retention_and_zero_take_up() -> None:
    result = calculate_scenario(
        annual_budget=Decimal(2000),
        current_annual_unit_cost=Decimal("100.01"),
        current_covered_employees=3,
        additional_eligible_employees=2,
        take_up_percent=0,
        renewal_percent=0,
        retention_percent=50,
    )
    assert result.retained_members == Decimal("1.5")
    assert result.total_coverage == Decimal("1.5")
    assert result.expected_cost == Decimal("150.015")
    assert result.full_cost == Decimal("500.05")


def test_zero_budget_and_zero_retention_preserve_full_cover_warning() -> None:
    result = calculate_scenario(
        annual_budget=Decimal(0),
        current_annual_unit_cost=Decimal(1000),
        current_covered_employees=80,
        additional_eligible_employees=0,
        take_up_percent=0,
        renewal_percent=0,
        retention_percent=0,
    )
    assert result.expected_cost == 0
    assert result.full_cost == 80000
    assert result.existing_cover_unaffordable
    assert result.capacity == 0
    assert result.additional_places == 0


@pytest.mark.parametrize(
    "budget, retained, unit_cost, eligible, expected",
    [
        ("275", "1.5", "100", 10, 1),
        ("250", "1.5", "100", 10, 1),
        ("249.99", "1.5", "100", 10, 0),
        ("150", "1.5", "100", 10, 0),
        ("100", "1.5", "100", 10, 0),
        ("0", "0", "100", 10, 0),
        ("1000", "0", "100", 3, 3),
        ("1000", "0", "100", 0, 0),
        ("0.33", "1", "0.11", 10, 2),
    ],
)
def test_retention_based_places_boundaries(
    budget: str, retained: str, unit_cost: str, eligible: int, expected: int
) -> None:
    """Reserve unrounded retained cost before flooring and capping new places."""
    places = calculate_retention_based_additional_places(
        Decimal(budget), Decimal(retained), Decimal(unit_cost), eligible
    )
    assert places == expected
    assert isinstance(places, int)


def test_expected_retention_can_fund_places_when_full_retention_cannot() -> None:
    result = calculate_scenario(
        annual_budget=Decimal(80000),
        current_annual_unit_cost=Decimal(1000),
        current_covered_employees=80,
        additional_eligible_employees=40,
        take_up_percent=25,
        renewal_percent=10,
        retention_percent=50,
    )
    assert result.existing_cover_unaffordable
    assert result.additional_places == 0
    assert result.retained_cost == 44000
    assert result.retained_balance == 36000
    assert result.retention_based_additional_places == 32
    assert result.retention_based_enrolment_gap == 0


def test_retained_cover_exceeding_budget_has_no_forecast_places() -> None:
    result = calculate_scenario(
        annual_budget=Decimal(1000),
        current_annual_unit_cost=Decimal(1000),
        current_covered_employees=80,
        additional_eligible_employees=40,
        take_up_percent=75,
        renewal_percent=0,
        retention_percent=90,
    )
    assert result.retained_balance == -71000
    assert result.retention_based_additional_places == 0
    assert result.retention_based_enrolment_gap == 30
