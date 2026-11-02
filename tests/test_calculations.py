"""Verify cost estimator calculations using validated inputs."""

from decimal import Decimal

import pytest

from pmi_estimator.calculations import (
    calculate_affordable_additional_places,
    calculate_annual_cost,
    calculate_budget_balance,
    calculate_expected_additional_enrolment,
    calculate_expected_total_coverage,
    calculate_full_take_up_cost,
    calculate_scenario_annual_unit_cost,
    calculate_total_affordable_capacity,
)
from pmi_estimator.validation import (
    validate_employee_cost,
    validate_pmi_budget,
    validate_renewal_change,
)


@pytest.mark.parametrize(
    "current_members, eligible, unit_cost, expected",
    [
        pytest.param(0, 0, "1200", "0", id="both-counts-zero"),
        pytest.param(200, 0, "1200", "240000", id="existing-members-only"),
        pytest.param(0, 50, "1200", "60000", id="additional-members-only"),
        pytest.param(200, 50, "1200", "300000", id="all-eligible-members"),
        pytest.param(2, 1, "112.51125", "337.53375", id="unrounded-unit-cost"),
    ],
)
def test_full_take_up_cost(
    current_members: int, eligible: int, unit_cost: str, expected: str
) -> None:
    """Include every eligible member and preserve decimal costs without rounding."""
    result = calculate_full_take_up_cost(current_members, eligible, Decimal(unit_cost))
    assert isinstance(result, Decimal)
    assert result == Decimal(expected)


@pytest.mark.parametrize("take_up_percent", [0.0, 25.0, 100.0])
def test_full_take_up_cost_against_expected_cost(take_up_percent: float) -> None:
    """Full cost remains fixed; expected cost matches it only at 100% take-up."""
    additional = calculate_expected_additional_enrolment(50, take_up_percent)
    coverage = calculate_expected_total_coverage(200, additional)
    unit_cost = calculate_scenario_annual_unit_cost(Decimal(1000), 20.0)
    expected_cost = calculate_annual_cost(coverage, unit_cost)
    full_cost = calculate_full_take_up_cost(200, 50, unit_cost)

    assert full_cost == Decimal(300000)
    if take_up_percent == 100:
        assert expected_cost == full_cost
    else:
        assert expected_cost < full_cost


@pytest.mark.parametrize(
    "eligible, capacity, current_members, expected",
    [
        pytest.param(50, 100, 200, 0, id="existing-members-exceed-capacity"),
        pytest.param(50, 200, 200, 0, id="existing-members-use-capacity"),
        pytest.param(50, 220, 200, 20, id="limited-spare-capacity"),
        pytest.param(50, 300, 200, 50, id="capped-at-eligible-population"),
        pytest.param(50, 250, 200, 50, id="exactly-funds-eligible-population"),
        pytest.param(0, 300, 200, 0, id="no-additional-eligible-employees"),
        pytest.param(50, 20, 0, 20, id="no-existing-members"),
        pytest.param(50, 0, 0, 0, id="zero-capacity"),
    ],
)
def test_affordable_additional_places(
    eligible: int, capacity: int, current_members: int, expected: int
) -> None:
    """Keep additional places between zero and the eligible population."""
    result = calculate_affordable_additional_places(eligible, capacity, current_members)
    assert result == expected
    assert isinstance(result, int)


def test_decimal_input_to_capacity_pipeline() -> None:
    """Keep a decimal renewal cost exact through to whole-member capacity."""
    budget = validate_pmi_budget(0.33)
    cost = validate_employee_cost(0.10)
    renewal = validate_renewal_change(10)
    renewed_cost = calculate_scenario_annual_unit_cost(cost, renewal)
    assert renewed_cost == Decimal("0.11")
    assert calculate_total_affordable_capacity(budget, renewed_cost) == 3


@pytest.mark.parametrize(
    "budget, cost, expected",
    [
        pytest.param(1000.0, 800.0, 200.0, id="surplus"),
        pytest.param(1000.0, 1200.0, -200.0, id="overspend"),
        pytest.param(1000.0, 1000.0, 0.0, id="balanced"),
        pytest.param(0.0, 200.0, -200.0, id="zero-budget"),
        pytest.param(1000.0, 0.0, 1000.0, id="zero-cost"),
        pytest.param(0.0, 0.0, 0.0, id="both-zero"),
        pytest.param(1000.0, 999.125, 0.875, id="unrounded-balance"),
    ],
)
def test_budget_balance(budget: float, cost: float, expected: float) -> None:
    """Preserve surplus and overspend signs, zero boundaries and precision."""
    assert calculate_budget_balance(
        Decimal(str(budget)), Decimal(str(cost))
    ) == Decimal(str(expected))


@pytest.mark.parametrize(
    "eligible_employees, take_up_percent, expected",
    [
        pytest.param(150, 0.0, 0.0, id="no-take-up"),
        pytest.param(150, 100.0, 150.0, id="full-take-up"),
        pytest.param(0, 50.0, 0.0, id="no-eligible-employees"),
        pytest.param(150, 25.0, 37.5, id="fractional-enrolment"),
        pytest.param(200, 0.5, 1.0, id="percentage-not-proportion"),
    ],
)
def test_expected_additional_enrolment(
    eligible_employees: int, take_up_percent: float, expected: float
) -> None:
    """Apply take-up to additional employees and preserve fractional estimates."""
    result = calculate_expected_additional_enrolment(
        eligible_employees, take_up_percent
    )
    assert result == Decimal(str(expected))


@pytest.mark.parametrize(
    "coverage, unit_cost, expected",
    [
        pytest.param(200.0, 1200.0, 240000.0, id="all-covered-members"),
        pytest.param(0.0, 1200.0, 0.0, id="no-covered-members"),
        pytest.param(237.5, 1000.01, 237502.375, id="unrounded-fractional-cost"),
    ],
)
def test_expected_annual_cost(
    coverage: float, unit_cost: float, expected: float
) -> None:
    """Multiply expected member count by unit cost without rounding."""
    assert calculate_annual_cost(
        Decimal(str(coverage)), Decimal(str(unit_cost))
    ) == Decimal(str(expected))


@pytest.mark.parametrize(
    "eligible_employees, take_up_percent",
    [
        pytest.param(0, 50.0, id="zero-additional-eligibility"),
        pytest.param(150, 0.0, id="zero-take-up"),
    ],
)
def test_no_new_enrolment_preserves_existing_members_renewed_cost(
    eligible_employees: int, take_up_percent: float
) -> None:
    """With no joiners, 200 existing members still incur the 20% renewed cost."""
    additional_enrolment = calculate_expected_additional_enrolment(
        eligible_employees, take_up_percent
    )
    coverage = calculate_expected_total_coverage(200, additional_enrolment)
    unit_cost = calculate_scenario_annual_unit_cost(Decimal("1000.0"), 20.0)

    assert calculate_annual_cost(
        Decimal(str(coverage)), Decimal(str(unit_cost))
    ) == Decimal(240000)


@pytest.mark.parametrize(
    "current_cost, renewal_percent, expected",
    [
        pytest.param(1000.0, 20.0, 1200.0, id="price-increase"),
        pytest.param(1000.0, 0.0, 1000.0, id="no-change"),
        pytest.param(1000.0, -10.0, 900.0, id="price-reduction"),
        pytest.param(1000.0, -99.0, 10.0, id="large-reduction"),
        pytest.param(1000.0, 150.0, 2500.0, id="increase-above-100-percent"),
        pytest.param(100.01, 12.5, 112.51125, id="preserve-unrounded-cost"),
    ],
)
def test_scenario_annual_unit_cost(
    current_cost: float, renewal_percent: float, expected: float
) -> None:
    """Apply renewal percentages to unit cost, preserving unrounded estimates."""
    result = calculate_scenario_annual_unit_cost(
        Decimal(str(current_cost)), renewal_percent
    )
    assert result == Decimal(str(expected))


@pytest.mark.parametrize(
    "current_covered_employees, additional_enrolment, expected",
    [
        pytest.param(0, 0.0, 0.0, id="both-zero"),
        pytest.param(0, 37.5, 37.5, id="no-current-members"),
        pytest.param(200, 0.0, 200.0, id="no-additional-enrolment"),
        pytest.param(200, 37.5, 237.5, id="fractional-total-coverage"),
    ],
)
def test_expected_total_coverage(
    current_covered_employees: int,
    additional_enrolment: float,
    expected: float,
) -> None:
    """Add current and expected additional members without rounding the result."""
    result = calculate_expected_total_coverage(
        current_covered_employees, Decimal(str(additional_enrolment))
    )
    assert result == Decimal(str(expected))


@pytest.mark.parametrize(
    "budget, unit_cost, expected",
    [
        pytest.param(0.0, 100.0, 0, id="zero-budget"),
        pytest.param(99.0, 100.0, 0, id="below-one-member"),
        pytest.param(1000.0, 100.0, 10, id="exact-capacity"),
        pytest.param(1099.0, 100.0, 10, id="round-down"),
        pytest.param(0.3, 0.1, 3, id="exact-decimal-boundary"),
        pytest.param(0.29, 0.1, 2, id="below-decimal-boundary"),
        pytest.param(0.31, 0.1, 3, id="above-decimal-boundary"),
        pytest.param(1000.0, 112.51125, 8, id="unrounded-unit-cost"),
    ],
)
def test_total_affordable_capacity(
    budget: float, unit_cost: float, expected: int
) -> None:
    """Return whole-member capacity without rounding up or losing exact boundaries."""
    result = calculate_total_affordable_capacity(
        Decimal(str(budget)), Decimal(str(unit_cost))
    )
    assert result == expected
    assert isinstance(result, int)
