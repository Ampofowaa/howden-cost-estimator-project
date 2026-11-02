"""Model acceptance checks independent of terminal prompts and display strings.

Inputs use numeric validators shared with the Shiny app. Expected values are literal
worked results, not recalculated using the formulas under test.
"""

from decimal import Decimal

import pytest

from pmi_estimator.results import calculate_scenario
from pmi_estimator.validation import (
    validate_employee_cost,
    validate_employee_count,
    validate_pmi_budget,
    validate_renewal_change,
    validate_take_up,
)


@pytest.mark.parametrize(
    "budget, current, eligible, take_up, cost, renewal, expected",
    [
        pytest.param(
            "120000",
            "80",
            "40",
            "75",
            "1000",
            "20",
            {
                "additional_enrolment": "30",
                "total_coverage": "110",
                "unit_cost": "1200",
                "expected_cost": "132000",
                "balance": "-12000",
                "capacity": "100",
                "additional_places": "20",
                "full_cost": "144000",
                "full_balance": "-24000",
                "existing_cost": "96000",
                "existing_balance": "24000",
                "additional_enrolment_gap": "10",
            },
            id="central-worked-example",
        ),
        pytest.param(
            "90000",
            "80",
            "40",
            "75",
            "1200",
            "0",
            {
                "existing_cost": "96000",
                "existing_balance": "-6000",
                "additional_places": "0",
                "expected_cost": "132000",
                "additional_enrolment_gap": "30",
            },
            id="existing-cover-unaffordable",
        ),
        pytest.param(
            "132000",
            "80",
            "40",
            "75",
            "1200",
            "0",
            {
                "total_coverage": "110",
                "expected_cost": "132000",
                "balance": "0",
                "capacity": "110",
                "additional_enrolment_gap": "0",
            },
            id="exact-budget-match",
        ),
        pytest.param(
            "10000",
            "0",
            "3",
            "50",
            "1000",
            "0",
            {
                "additional_enrolment": "1.5",
                "total_coverage": "1.5",
                "expected_cost": "1500",
                "additional_places": "3",
                "additional_enrolment_gap": "0",
            },
            id="fractional-expected-enrolment",
        ),
        pytest.param(
            "200000",
            "80",
            "40",
            "75",
            "1000",
            "0",
            {
                "capacity": "200",
                "additional_places": "40",
                "balance": "90000",
                "additional_enrolment_gap": "0",
            },
            id="capacity-exceeds-eligible-population",
        ),
        pytest.param(
            "120000",
            "80",
            "40",
            "0",
            "1000",
            "0",
            {
                "additional_enrolment": "0",
                "total_coverage": "80",
                "expected_cost": "80000",
                "full_cost": "120000",
            },
            id="zero-take-up",
        ),
        pytest.param(
            "120000",
            "80",
            "40",
            "100",
            "1000",
            "0",
            {
                "total_coverage": "120",
                "expected_cost": "120000",
                "full_cost": "120000",
                "balance": "0",
                "full_balance": "0",
            },
            id="full-take-up",
        ),
        pytest.param(
            "120000",
            "80",
            "0",
            "75",
            "1000",
            "0",
            {
                "total_coverage": "80",
                "expected_cost": "80000",
                "full_cost": "80000",
                "additional_places": "0",
                "additional_enrolment_gap": "0",
            },
            id="zero-additional-eligibility",
        ),
        pytest.param(
            "0",
            "80",
            "40",
            "0",
            "1000",
            "0",
            {
                "expected_cost": "80000",
                "existing_cost": "80000",
                "existing_balance": "-80000",
                "capacity": "0",
                "additional_places": "0",
                "full_cost": "120000",
            },
            id="zero-budget-preserves-existing-cover",
        ),
        pytest.param(
            "0.33",
            "0",
            "3",
            "100",
            "0.10",
            "10",
            {
                "unit_cost": "0.11",
                "capacity": "3",
                "expected_cost": "0.33",
                "balance": "0",
            },
            id="exact-decimal-boundary",
        ),
        pytest.param(
            "337.53",
            "2",
            "1",
            "100",
            "100.01",
            "12.5",
            {
                "unit_cost": "112.51125",
                "expected_cost": "337.53375",
                "balance": "-0.00375",
                "capacity": "2",
                "additional_places": "0",
            },
            id="unrounded-cost-and-sub-penny-shortfall",
        ),
        pytest.param(
            "120000",
            "80",
            "40",
            "75",
            "1000",
            "-10",
            {
                "unit_cost": "900",
                "expected_cost": "99000",
                "balance": "21000",
                "full_cost": "108000",
                "additional_places": "40",
            },
            id="negative-renewal",
        ),
        pytest.param(
            "120000",
            "80",
            "40",
            "75",
            "1000",
            "10",
            {
                "unit_cost": "1100",
                "expected_cost": "121000",
                "balance": "-1000",
                "capacity": "109",
                "additional_places": "29",
                "full_cost": "132000",
                "full_balance": "-12000",
                "additional_enrolment_gap": "1",
            },
            id="lower-worked-scenario",
        ),
        pytest.param(
            "120000",
            "80",
            "40",
            "75",
            "1000",
            "30",
            {
                "unit_cost": "1300",
                "expected_cost": "143000",
                "balance": "-23000",
                "capacity": "92",
                "additional_places": "12",
                "full_cost": "156000",
                "full_balance": "-36000",
                "additional_enrolment_gap": "18",
            },
            id="upper-worked-scenario",
        ),
    ],
)
def test_reference_results(
    budget: str,
    current: str,
    eligible: str,
    take_up: str,
    cost: str,
    renewal: str,
    expected: dict[str, str],
) -> None:
    """Validated inputs produce literal reference outcomes independently of the UI."""
    result = calculate_scenario(
        annual_budget=validate_pmi_budget(float(budget)),
        current_annual_unit_cost=validate_employee_cost(float(cost)),
        current_covered_employees=validate_employee_count(float(current)),
        additional_eligible_employees=validate_employee_count(float(eligible)),
        take_up_percent=validate_take_up(float(take_up)),
        renewal_percent=validate_renewal_change(float(renewal)),
    )
    for field, value in expected.items():
        assert getattr(result, field) == Decimal(value), field
    assert result.existing_cover_unaffordable == (result.existing_balance < 0)
    assert isinstance(result.capacity, int)
    assert isinstance(result.additional_places, int)
    assert isinstance(result.expected_cost, Decimal)
