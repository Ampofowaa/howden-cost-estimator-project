"""Assemble unrounded scenario results independently of any interface.

Callers validate inputs first. Percentages are percentage points (20 means
20%). Formulas remain in calculations.py; this module connects them without
input/output, display formatting or dependencies on terminal or Shiny code.
"""

from dataclasses import dataclass
from decimal import Decimal

from pmi_estimator.calculations import (
    calculate_affordable_additional_places,
    calculate_annual_cost,
    calculate_budget_balance,
    calculate_expected_additional_enrolment,
    calculate_expected_retained_members,
    calculate_expected_total_coverage,
    calculate_full_take_up_cost,
    calculate_retention_based_additional_places,
    calculate_scenario_annual_unit_cost,
    calculate_total_affordable_capacity,
)


@dataclass(frozen=True)
class ScenarioResult:
    """Named numerical results; negative balances indicate a shortfall.

    Frozen fields prevent a presentation layer from replacing raw amounts
    with rounded values. Scenario names belong to the interface.
    """

    # Renewal assumption and forecast membership/cost.
    renewal_percent: float
    additional_enrolment: Decimal
    total_coverage: Decimal
    unit_cost: Decimal
    expected_cost: Decimal
    balance: Decimal
    # Whole-person affordability and costs when all current members stay.
    capacity: int
    additional_places: int
    full_cost: Decimal
    full_balance: Decimal
    existing_cost: Decimal
    existing_balance: Decimal
    # Selected retention and affordability after reserving expected retained cover.
    retention_percent: float
    retained_members: Decimal
    retained_cost: Decimal
    retained_balance: Decimal
    retention_based_additional_places: int

    @property
    def retention_based_enrolment_gap(self) -> Decimal:
        """Expected joiners above retention-based whole additional places."""
        return max(
            Decimal(0),
            self.additional_enrolment - self.retention_based_additional_places,
        )

    @property
    def existing_cover_unaffordable(self) -> bool:
        """Whether existing cover alone exceeds the annual budget."""
        return self.existing_balance < 0

    @property
    def additional_enrolment_gap(self) -> Decimal:
        """Joiner gap when reserving all current members, or zero."""
        return max(Decimal(0), self.additional_enrolment - self.additional_places)


def calculate_scenario(
    *,
    annual_budget: Decimal,
    current_annual_unit_cost: Decimal,
    current_covered_employees: int,
    additional_eligible_employees: int,
    take_up_percent: float,
    renewal_percent: float,
    retention_percent: float = 100.0,
) -> ScenarioResult:
    """Calculate one scenario from validated inputs, without rounding.

    Budget and counts must be non-negative; unit cost must be positive.
    Take-up and retention must be in [0, 100]; renewal must exceed -100.
    Retention defaults to 100%. Retention-based additional places fund expected
    retained cover first; conservative additional_places reserves all current
    members. Total capacity and full-cover cost do not depend on retention.
    All supplied numbers must be finite. Validation belongs to validation.py.
    """
    # Membership depends on retention and take-up, independently of renewal cost.
    additional_enrolment = calculate_expected_additional_enrolment(
        additional_eligible_employees, take_up_percent
    )
    retained_members = calculate_expected_retained_members(
        current_covered_employees, retention_percent
    )
    total_coverage = calculate_expected_total_coverage(
        retained_members, additional_enrolment
    )
    # Apply the same renewed annual cost to every covered employee.
    unit_cost = calculate_scenario_annual_unit_cost(
        current_annual_unit_cost, renewal_percent
    )
    expected_cost = calculate_annual_cost(
        covered_membership=total_coverage, scenario_annual_unit_cost=unit_cost
    )
    # Reserve all current members for the conservative affordability view.
    capacity = calculate_total_affordable_capacity(annual_budget, unit_cost)
    additional_places = calculate_affordable_additional_places(
        additional_eligible_employees, capacity, current_covered_employees
    )
    full_cost = calculate_full_take_up_cost(
        current_covered_employees, additional_eligible_employees, unit_cost
    )
    existing_cost = calculate_annual_cost(
        covered_membership=Decimal(current_covered_employees),
        scenario_annual_unit_cost=unit_cost,
    )
    # The forecast view reserves unrounded retained cover, allowing for departures.
    retained_cost = calculate_annual_cost(retained_members, unit_cost)
    retention_based_places = calculate_retention_based_additional_places(
        annual_budget, retained_members, unit_cost, additional_eligible_employees
    )
    return ScenarioResult(
        renewal_percent=renewal_percent,
        additional_enrolment=additional_enrolment,
        total_coverage=total_coverage,
        unit_cost=unit_cost,
        expected_cost=expected_cost,
        balance=calculate_budget_balance(annual_budget, expected_cost),
        capacity=capacity,
        additional_places=additional_places,
        full_cost=full_cost,
        full_balance=calculate_budget_balance(annual_budget, full_cost),
        existing_cost=existing_cost,
        existing_balance=calculate_budget_balance(annual_budget, existing_cost),
        retention_percent=retention_percent,
        retained_members=retained_members,
        retained_cost=retained_cost,
        retained_balance=calculate_budget_balance(annual_budget, retained_cost),
        retention_based_additional_places=retention_based_places,
    )
