"""Pure calculations for annual PMI coverage, cost and affordability.

Callers supply validated inputs from validation.py. These functions perform no
terminal I/O and do not repeat input validation. Money and fractional expected
membership use Decimal; whole-member counts and capacities use int. Percentage
arguments use percentage points (20 means 20%) and are converted to Decimal
before arithmetic. Decimal operations use Python's current decimal context;
"without rounding" below means no deliberate display or penny rounding,
not unlimited arithmetic precision.

The same renewed annual unit cost applies to existing and additional members.
The budget funds all cover. The supplied unit cost includes all employer costs
being modelled; no separate taxes, fees or contributions are added here.

Expected costing preserves fractional enrolment. Full take-up includes every
additional eligible employee, regardless of the take-up assumption. Costs are
not rounded to pennies here; presentation formats money to two decimal places.
Only affordable capacity is rounded down to whole people. Additional places
are capped at the eligible population and cannot be negative.

Expected costs and retention-based additional places use assumed retention.
Full-cover costs and conservative additional places reserve all current members.
Retention-based places depend on forecast departures actually happening.
A positive budget balance means surplus; a negative balance means shortfall.
"""

from decimal import ROUND_FLOOR, Decimal

# Expected membership


def calculate_expected_additional_enrolment(
    additional_eligible_employees: int,
    take_up_percent: float,
) -> Decimal:
    """Return expected additional enrolments without whole-person rounding.

    Args:
        additional_eligible_employees: Validated non-negative eligible employee count.
        take_up_percent: Validated percentage from 0 to 100 inclusive;
            supply 25 for 25 percent, rather than 0.25.
    """
    return additional_eligible_employees * (Decimal(str(take_up_percent)) / 100)


def calculate_expected_retained_members(
    currently_covered_count: int, retention_percent: float
) -> Decimal:
    """Apply validated 0-100 percentage-point retention without rounding people."""
    return currently_covered_count * (Decimal(str(retention_percent)) / 100)


def calculate_expected_total_coverage(
    expected_retained_members: Decimal | int,
    expected_additional_enrolment: Decimal,
) -> Decimal:
    """Return expected retained members plus expected new joiners, unrounded.

    Args:
        expected_retained_members: Non-negative expected existing members who
            remain covered. An integer is also accepted for 100% retention.
        expected_additional_enrolment: Non-negative expected additional members.
    """
    return expected_retained_members + expected_additional_enrolment


# Annual costs and budget balance


def calculate_scenario_annual_unit_cost(
    current_annual_unit_cost: Decimal,
    renewal_change_percent: float,
) -> Decimal:
    """Return the annual unit cost after a renewal change, without rounding.

    Args:
        current_annual_unit_cost: Validated finite, positive annual employer
            cost per covered employee.
        renewal_change_percent: Validated finite renewal change above -100%;
            supply 25 for 25 percent, rather than 0.25.
    """
    return current_annual_unit_cost * (1 + Decimal(str(renewal_change_percent)) / 100)


def calculate_annual_cost(
    covered_membership: Decimal,
    scenario_annual_unit_cost: Decimal,
) -> Decimal:
    """Return annual cost for the supplied membership without penny rounding.

    The caller chooses the population: existing members only, expected total
    membership, or everyone eligible. This function does not add members or
    apply take-up; it multiplies the supplied membership by annual unit cost.

    Args:
        covered_membership: Finite, non-negative membership to cost. Expected
            membership may be fractional; convert whole counts to Decimal.
        scenario_annual_unit_cost: Finite, positive annual employer cost per
            covered employee after the scenario renewal change.
    """
    return covered_membership * scenario_annual_unit_cost


def calculate_budget_balance(
    annual_budget: Decimal,
    annual_cost: Decimal,
) -> Decimal:
    """Return budget balance without rounding.

    Positive means surplus, negative means overspend, and zero means balanced.

    Args:
        annual_budget: Finite, non-negative annual budget.
        annual_cost: Finite, non-negative annual cost for the comparison,
            such as expected, existing-cover or full-take-up cost.
    """
    return annual_budget - annual_cost


# Whole-person affordability limits


def calculate_total_affordable_capacity(
    annual_budget: Decimal,
    scenario_annual_unit_cost: Decimal,
) -> int:
    """Return the maximum whole members the budget can fund in total.

    This ceiling applies to existing and additional members together. It can
    be below existing membership or above the available eligible population;
    it does not change how many existing members remain in cost estimates.

    Use Decimal amounts throughout the cost pipeline to avoid
    binary floating-point division understating capacity at exact boundaries.
    Round down only when converting capacity to whole members.

    Args:
        annual_budget: Validated finite, non-negative annual budget.
        scenario_annual_unit_cost: Finite, positive scenario annual unit cost
            calculated from a validated employee cost and renewal percentage.
    """

    return int(
        (annual_budget / scenario_annual_unit_cost).to_integral_value(
            rounding=ROUND_FLOOR
        )
    )


def calculate_affordable_additional_places(
    additional_eligible_employees: int,
    total_affordable_capacity: int,
    current_covered_employees: int,
) -> int:
    """Return affordable additional places capped at the eligible population.

    Return zero when existing membership uses or exceeds total capacity.

    Args:
        additional_eligible_employees: Validated non-negative whole-number
            count of additional employees becoming eligible.
        total_affordable_capacity: Computed non-negative whole-member capacity.
        current_covered_employees: Validated non-negative whole-number count
            of currently covered employees.
    """

    return min(
        additional_eligible_employees,
        max(0, total_affordable_capacity - current_covered_employees),
    )


def calculate_retention_based_additional_places(
    annual_budget: Decimal,
    expected_retained_members: Decimal,
    scenario_annual_unit_cost: Decimal,
    additional_eligible_employees: int,
) -> int:
    """Return whole additional places after expected retained-member cost.

    Subtract unrounded retained-cover cost before dividing by unit cost and
    rounding down. Fractional retained members must not be rounded first.
    Cap at additional eligibility and return zero if no budget remains.
    Inputs must be validated; these places depend on the retention forecast.
    """
    retained_cost = calculate_annual_cost(
        expected_retained_members, scenario_annual_unit_cost
    )
    remaining_budget = max(Decimal(0), annual_budget - retained_cost)
    capacity = calculate_total_affordable_capacity(
        remaining_budget, scenario_annual_unit_cost
    )
    return min(additional_eligible_employees, capacity)


# Full-cover comparison


def calculate_full_take_up_cost(
    current_covered_employees: int,
    additional_eligible_employees: int,
    scenario_annual_unit_cost: Decimal,
) -> Decimal:
    """Return annual cost at 100% retention and take-up, without rounding.

    Include all existing members and additional eligible employees,
    regardless of expected take-up or available budget.

    Args:
        current_covered_employees: Validated non-negative whole-number count
            of currently covered employees.
        additional_eligible_employees: Validated non-negative whole-number
            count of additional employees becoming eligible.
        scenario_annual_unit_cost: Finite, positive scenario annual unit cost
            calculated from a validated employee cost and renewal percentage.
    """

    return (
        current_covered_employees + additional_eligible_employees
    ) * scenario_annual_unit_cost
