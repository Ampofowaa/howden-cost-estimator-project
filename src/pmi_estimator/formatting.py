"""Turn unrounded model values into display text without changing calculations.

Membership keeps fractional estimates. Budget outcomes distinguish exact balance
from sub-penny surpluses or shortfalls that ordinary currency formatting hides.
"""

from decimal import Decimal


def format_membership(membership: Decimal) -> str:
    """Display a membership estimate without rounding or trailing zeros."""
    text = f"{membership:,f}"
    if "." in text:
        return text.rstrip("0").rstrip(".")
    return text


def format_budget_outcome(balance: Decimal) -> str:
    """Describe the budget outcome in plain language without hiding small gaps."""
    if balance == 0:
        return "Estimated cost matches your budget"
    if abs(balance) < Decimal("0.01"):
        if balance < 0:
            return "Less than £0.01 over budget"
        return "Less than £0.01 budget remaining"
    if balance < 0:
        return f"£{abs(balance):,.2f} over budget"
    return f"£{balance:,.2f} budget remaining"
