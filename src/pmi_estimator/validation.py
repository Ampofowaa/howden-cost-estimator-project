"""Validate numeric values supplied by the PMI planning interface.

Validators accept missing input as None and raise field-specific ValueError
messages. Money returns Decimal without deliberate rounding, counts return int,
and percentages remain percentage points (75 means 75%). Budget may be zero;
employee cost must be positive. Counts must be non-negative whole numbers.
Take-up and retention are in [0, 100]; renewal changes must exceed -100%.
Initial control values belong to app.py, not to validation.
"""

import math
from decimal import Decimal


def validate_pmi_budget(budget: float | None) -> Decimal:
    """Validate a numeric budget and return Decimal without rounding.

    Zero is valid; None represents missing input. Fractions of a penny are
    rejected.
    """
    if budget is None:
        raise ValueError("Annual PMI budget is required.")

    amount = Decimal(str(budget))

    if not amount.is_finite():
        raise ValueError("Annual PMI budget must be finite.")

    if amount < 0:
        raise ValueError("Annual PMI budget must be non-negative.")

    pennies = amount * 100
    if pennies != pennies.to_integral_value():
        raise ValueError("Annual PMI budget must have at most 2 decimal places.")

    return amount


def validate_employee_cost(cost: float | None) -> Decimal:
    """Validate a positive numeric employee cost without rounding.

    Zero is invalid; None represents missing input. Fractions of a penny are
    rejected.
    """
    if cost is None:
        raise ValueError("Annual cost per covered employee is required.")

    amount = Decimal(str(cost))

    if not amount.is_finite():
        raise ValueError("Annual cost per covered employee must be finite.")

    if amount <= 0:
        raise ValueError("Annual cost per covered employee must be greater than zero.")

    pennies = amount * 100
    if pennies != pennies.to_integral_value():
        raise ValueError(
            "Annual cost per covered employee must have at most 2 decimal places."
        )

    return amount


def validate_renewal_change(renewal_change_percent: float | None) -> float:
    """Validate a finite renewal change greater than -100%, without rounding.

    Values are percentage points: 20 means 20%, not 0.20. Negative changes
    above -100% and zero are valid. None represents missing input.
    """
    if renewal_change_percent is None:
        raise ValueError("Renewal change is required.")

    if not math.isfinite(renewal_change_percent):
        raise ValueError("Renewal change must be finite.")

    if renewal_change_percent <= -100:
        raise ValueError("Renewal change must be greater than -100%.")

    return renewal_change_percent


def validate_employee_count(
    count: float | None, *, field_name: str = "Employee count"
) -> int:
    """Validate a non-negative numeric employee count and return int.

    None represents missing input. Fractions are rejected. The field name identifies
    which employee group needs correction in validation messages.
    """
    if count is None:
        raise ValueError(f"{field_name} is required.")

    if not math.isfinite(count):
        raise ValueError(f"{field_name} must be finite.")

    if count < 0:
        raise ValueError(f"{field_name} must be non-negative.")

    if count != int(count):
        raise ValueError(f"{field_name} must be a whole number.")

    return int(count)


def validate_take_up(take_up_percent: float | None) -> float:
    """Validate a finite take-up percentage from 0 to 100, without rounding.

    Values are percentage points: 50 means 50%, not 0.50. Fractional
    percentages are valid. None represents missing input.
    """
    if take_up_percent is None:
        raise ValueError("Expected take-up is required.")

    if not math.isfinite(take_up_percent):
        raise ValueError("Expected take-up must be finite.")

    if not 0 <= take_up_percent <= 100:
        raise ValueError("Expected take-up must be between 0 and 100%.")

    return take_up_percent


def validate_retention(retention_percent: float | None) -> float:
    """Validate finite retention from 0 to 100 percentage points, without rounding.

    None represents missing input; 100 means all current members stay.
    Fractional percentages are valid.
    """
    if retention_percent is None:
        raise ValueError("Expected retention is required.")
    if not math.isfinite(retention_percent):
        raise ValueError("Expected retention must be finite.")
    if not 0 <= retention_percent <= 100:
        raise ValueError("Expected retention must be between 0 and 100%.")
    return retention_percent
