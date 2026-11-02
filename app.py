# Shiny Express interface for comparing three annual PMI renewal scenarios.
#
# Read from top to bottom: page setup, employer inputs, membership assumptions,
# renewal inputs, shared reactive results, then comparison rendering. Each input
# keeps its validation and feedback nearby. Financial formulas belong to
# calculations.py; results.py assembles them into unrounded scenario results.

from decimal import Decimal
from pathlib import Path

from htmltools import Tag
from shiny import reactive
from shiny import ui as core_ui
from shiny.express import input, render, ui

from pmi_estimator.formatting import format_budget_outcome, format_membership
from pmi_estimator.results import ScenarioResult, calculate_scenario
from pmi_estimator.validation import (
    validate_employee_cost,
    validate_employee_count,
    validate_pmi_budget,
    validate_renewal_change,
    validate_retention,
    validate_take_up,
)

# Page styling and interaction support

ui.head_content(core_ui.include_css(Path(__file__).parent / "www" / "styles.css"))

with ui.div(class_="page-header"):
    ui.h1("PMI coverage and budget planner")
    ui.p(
        "Enter your employer's budget and membership figures below to see whether "
        "it can support your expected cover, compared across three renewal "
        "scenarios. These are planning estimates, not an insurer quotation."
    )
    ui.input_action_button(
        "load_example", "Load example figures", class_="btn-outline-secondary btn-sm"
    )


@reactive.effect
@reactive.event(input.load_example, ignore_init=True)
def load_example_figures() -> None:
    """Populate every control with the illustrative worked-example figures."""
    core_ui.update_numeric("pmi_budget", value=120000)
    core_ui.update_numeric("current_covered_employees", value=80)
    core_ui.update_numeric("additional_eligible_employees", value=40)
    core_ui.update_numeric("employee_cost", value=1000)
    core_ui.update_numeric("retention_percent", value=90)
    core_ui.update_numeric("expected_take_up", value=75)
    core_ui.update_numeric("renewal_percent_1", value=10)
    core_ui.update_numeric("renewal_percent_2", value=20)
    core_ui.update_numeric("renewal_percent_3", value=30)


ui.head_content(
    core_ui.tags.script(
        """
        // Mark required fields as touched only after leaving the field.
        document.addEventListener("focusout", function(event) {
            const requiredFields = ["pmi_budget", "current_covered_employees",
                "additional_eligible_employees", "employee_cost",
                "retention_percent", "expected_take_up",
                "renewal_percent_1", "renewal_percent_2", "renewal_percent_3"];
            if (requiredFields.includes(event.target.id) && window.Shiny) {
                Shiny.setInputValue(event.target.id + "_touched", true,
                    {priority: "event"});
            }
        });
        """
    )
)


def field_needs_feedback(field_id: str) -> bool:
    """Keep untouched empty fields quiet; validate entered or blurred fields."""
    if input[field_id]() is not None:
        return True
    touched_id = f"{field_id}_touched"
    return touched_id in input and bool(input[touched_id]())


# Employer details: controls, shared validation and local feedback

ui.h2("Employer details")
ui.p(
    "Enter your employer figures to see the comparison. All four figures are required. "
    "Enter 0 for budget or employee counts "
    "where appropriate; employee cost must be greater than zero."
)


with ui.div(class_="estimator-field"):
    ui.tags.label("Annual PMI budget (£)", for_="pmi_budget", class_="control-label")

    ui.help_text(
        "Total annual amount available for existing and additional employees' cover. "
        "Enter the amount in pounds without the £ sign or commas, with up to "
        "2 decimal places—for example, 120000 or 120000.50."
    )

    # Shiny accepts None for empty fields; its installed type hints require float.
    ui.input_numeric("pmi_budget", None, value=None, min=0, step=0.01)  # type: ignore[arg-type]

    @reactive.calc
    def validated_budget() -> Decimal:
        """Share the validated budget with feedback and future calculations."""
        return validate_pmi_budget(input.pmi_budget())

    @render.text
    def budget_feedback() -> str:
        """Show a field-specific message only when the input is invalid."""
        if not field_needs_feedback("pmi_budget"):
            return ""
        try:
            validated_budget()
            return ""
        except ValueError as error:
            return str(error)


with ui.div(class_="estimator-field"):
    ui.tags.label(
        "Currently covered employees",
        for_="current_covered_employees",
        class_="control-label",
    )

    ui.help_text(
        "Enter the number of employees currently covered by your PMI plan. "
        "Use a whole number greater than or equal to zero."
    )

    ui.input_numeric("current_covered_employees", None, value=None, min=0, step=1)  # type: ignore[arg-type]

    @reactive.calc
    def validated_currently_covered_count() -> int:
        """Share the validated current covered employees count."""
        return validate_employee_count(
            input.current_covered_employees(), field_name="Currently covered employees"
        )

    @render.text
    def currently_covered_count_feedback() -> str:
        """Show a field-specific message only when the input is invalid."""
        if not field_needs_feedback("current_covered_employees"):
            return ""
        try:
            validated_currently_covered_count()
            return ""
        except ValueError as error:
            return str(error)


with ui.div(class_="estimator-field"):
    ui.tags.label(
        "Additional employees eligible for cover",
        for_="additional_eligible_employees",
        class_="control-label",
    )

    ui.help_text(
        "Employees who could join next year, excluding those already covered. "
        "Enter everyone eligible, not just those you expect to join; the take-up "
        "percentage estimates how many join. Use a whole number, including zero."
    )

    ui.input_numeric("additional_eligible_employees", None, value=None, min=0, step=1)  # type: ignore[arg-type]

    @reactive.calc
    def validated_additional_eligible_count() -> int:
        """Share the validated additional eligible employees count."""
        return validate_employee_count(
            input.additional_eligible_employees(),
            field_name="Additional employees eligible for cover",
        )

    @render.text
    def additional_eligible_count_feedback() -> str:
        """Show a field-specific message only when the input is invalid."""
        if not field_needs_feedback("additional_eligible_employees"):
            return ""
        try:
            validated_additional_eligible_count()
            return ""
        except ValueError as error:
            return str(error)


with ui.div(class_="estimator-field"):
    ui.tags.label(
        "Current annual cost per covered employee (£)",
        for_="employee_cost",
        class_="control-label",
    )

    ui.help_text(
        "Enter the current annual cost to your organisation for one covered employee, "
        "including any taxes or fees paid within the PMI budget. "
        "Enter the amount in pounds without the £ sign or commas—for example, 1000 "
        "or 1000.50. Use an amount greater than zero, with up to 2 decimal places."
    )

    ui.help_text("The app adds no separate taxes or fees to the cost you enter.")

    ui.input_numeric("employee_cost", None, value=None, min=0.01, step=0.01)  # type: ignore[arg-type]

    @reactive.calc
    def validated_employee_cost() -> Decimal:
        """Share the validated employee cost without display formatting."""
        return validate_employee_cost(input.employee_cost())

    @render.text
    def employee_cost_feedback() -> str:
        """Show a field-specific message only when the input is invalid."""
        if not field_needs_feedback("employee_cost"):
            return ""
        try:
            validated_employee_cost()
            return ""
        except ValueError as error:
            return str(error)


# Membership assumptions: the exact fields drive calculations; sliders mirror them.

ui.h2("Membership assumptions")
ui.p(
    "Enter both percentages using assumptions appropriate to this employer. Both are required."
)


with ui.div(class_="estimator-field"):
    ui.tags.label(
        "Expected retention of currently covered employees (%)",
        for_="retention_percent",
        class_="control-label",
    )
    ui.help_text(
        "Percentage of current members you expect to remain covered next year. "
        "Enter 100 if you expect everyone to stay. "
        "A lower figure assumes some members leave cover. "
        "The extra employees you can afford under this forecast depend on those "
        "departures happening."
    )
    ui.help_text(
        "Enter a percentage from 0 to 100; decimals are allowed. "
        "A slider appears after a valid entry so you can adjust your assumption."
    )
    with ui.panel_conditional(
        "input.retention_percent != null && Number.isFinite(input.retention_percent)"
        " && input.retention_percent >= 0 && input.retention_percent <= 100"
    ):
        ui.input_slider(
            "retention_slider", None, min=0, max=100, value=100, step=0.01, ticks=False
        )
    ui.input_numeric(
        "retention_percent",
        "Exact retention (%)",
        value=None,  # type: ignore[arg-type]
        min=0,
        max=100,
        step=0.01,
    )

    @reactive.effect
    @reactive.event(input.retention_slider, ignore_init=True, ignore_none=False)
    def retention_slider_to_number() -> None:
        """A slider change replaces the exact value with the selected percentage."""
        selected_percent = input.retention_slider()
        if input.retention_percent() != selected_percent:
            core_ui.update_numeric("retention_percent", value=selected_percent)

    @reactive.effect
    @reactive.event(input.retention_percent, ignore_init=True, ignore_none=False)
    def retention_number_to_slider() -> None:
        """Update the slider only for a valid exact value; preserve invalid edits."""
        try:
            selected_percent = validate_retention(input.retention_percent())
        except ValueError:
            return
        if input.retention_slider() != selected_percent:
            core_ui.update_slider("retention_slider", value=selected_percent)

    @reactive.calc
    def validated_retention_percent() -> float:
        """Share validated retention in percentage points."""
        return validate_retention(input.retention_percent())

    @render.text
    def retention_feedback() -> str:
        """Show retention errors beside the assumption."""
        if not field_needs_feedback("retention_percent"):
            return ""
        try:
            validated_retention_percent()
            return ""
        except ValueError as error:
            return str(error)


with ui.div(class_="estimator-field"):
    ui.tags.label(
        "Expected take-up among additional eligible employees (%)",
        for_="expected_take_up",
        class_="control-label",
    )

    ui.help_text(
        "Percentage of additional eligible employees expected to join. "
        "Current members are estimated separately using retention. "
        "Enter a percentage from 0 to 100; decimals are allowed. "
        "A slider appears after a valid entry so you can adjust your assumption."
    )

    with ui.panel_conditional(
        "input.expected_take_up != null && Number.isFinite(input.expected_take_up)"
        " && input.expected_take_up >= 0 && input.expected_take_up <= 100"
    ):
        ui.input_slider(
            "take_up_slider", None, min=0, max=100, value=75, step=0.01, ticks=False
        )
    ui.input_numeric(
        "expected_take_up",
        "Exact take-up (%)",
        value=None,  # type: ignore[arg-type]
        min=0,
        max=100,
        step=0.01,
    )

    @reactive.effect
    @reactive.event(input.take_up_slider, ignore_init=True, ignore_none=False)
    def take_up_slider_to_number() -> None:
        """Share slider changes with the exact take-up field."""
        selected_percent = input.take_up_slider()
        if input.expected_take_up() != selected_percent:
            core_ui.update_numeric("expected_take_up", value=selected_percent)

    @reactive.effect
    @reactive.event(input.expected_take_up, ignore_init=True, ignore_none=False)
    def take_up_number_to_slider() -> None:
        """Keep valid exact values in sync without discarding invalid entries."""
        try:
            selected_percent = validate_take_up(input.expected_take_up())
        except ValueError:
            return
        if input.take_up_slider() != selected_percent:
            core_ui.update_slider("take_up_slider", value=selected_percent)

    @reactive.calc
    def validated_take_up_percent() -> float:
        """Share the validated expected take-up percentage."""
        return validate_take_up(input.expected_take_up())

    @render.text
    def take_up_feedback() -> str:
        """Show a field-specific message only when the input is invalid."""
        if not field_needs_feedback("expected_take_up"):
            return ""
        try:
            validated_take_up_percent()
            return ""
        except ValueError as error:
            return str(error)


# Renewal scenarios: preserve entry order, including duplicate percentages.

ui.h2("Renewal assumptions")
ui.p(
    "Enter three annual employee cost changes to compare. All three are required. "
    "Use assumptions appropriate to this employer; these are not market forecasts."
)
ui.help_text(
    "For example, 10 means a 10% increase and -10 means a 10% reduction; "
    "enter 0 for no change. Each change must be greater than -100%. "
    "You can enter scenarios in any order, including matching percentages."
)

with ui.div(class_="renewal-grid"):
    for scenario_number in range(1, 4):
        with ui.div(class_="estimator-field"):
            ui.input_numeric(
                f"renewal_percent_{scenario_number}",
                f"Scenario {scenario_number} renewal change (%)",
                value=None,  # type: ignore[arg-type]
                step=0.01,
            )
            core_ui.output_text(f"renewal_{scenario_number}_feedback")


def validated_scenario_renewal(scenario_number: int) -> float:
    """Identify the scenario when reporting a renewal validation error."""
    try:
        return validate_renewal_change(input[f"renewal_percent_{scenario_number}"]())
    except ValueError as error:
        raise ValueError(f"Scenario {scenario_number}: {error}") from error


def renewal_feedback(scenario_number: int) -> str:
    """Keep untouched renewal fields quiet and show local correction messages."""
    if not field_needs_feedback(f"renewal_percent_{scenario_number}"):
        return ""
    try:
        validated_scenario_renewal(scenario_number)
        return ""
    except ValueError as error:
        return str(error)


with ui.hold():  # Output containers are already beside the renewal inputs above.

    @render.text
    def renewal_1_feedback() -> str:
        return renewal_feedback(1)

    @render.text
    def renewal_2_feedback() -> str:
        return renewal_feedback(2)

    @render.text
    def renewal_3_feedback() -> str:
        return renewal_feedback(3)


# Shared validation and scenario results


@reactive.calc
def validated_renewal_changes() -> tuple[float, ...]:
    """Preserve scenario identity and entry order, including duplicate changes."""
    return tuple(validated_scenario_renewal(number) for number in range(1, 4))


@reactive.calc
def inputs_are_valid() -> bool:
    """Gate all result outputs while keeping field feedback independent."""
    validators = (
        validated_budget,
        validated_currently_covered_count,
        validated_additional_eligible_count,
        validated_employee_cost,
        validated_take_up_percent,
        validated_retention_percent,
        validated_renewal_changes,
    )
    for validator in validators:
        try:
            validator()
        except ValueError:
            return False
    return True


@reactive.calc
def scenario_results() -> tuple[ScenarioResult, ...]:
    """Calculate each renewal scenario once using the shared financial model."""
    return tuple(
        calculate_scenario(
            annual_budget=validated_budget(),
            current_annual_unit_cost=validated_employee_cost(),
            current_covered_employees=validated_currently_covered_count(),
            additional_eligible_employees=validated_additional_eligible_count(),
            take_up_percent=validated_take_up_percent(),
            renewal_percent=renewal_percent,
            retention_percent=validated_retention_percent(),
        )
        for renewal_percent in validated_renewal_changes()
    )


# Comparison rendering

ui.h2("Your results", class_="results-heading")


@render.ui
def results_readiness() -> Tag | None:
    """Explain why estimates are unavailable without repeating field errors."""
    if not inputs_are_valid():
        return core_ui.div(
            "Results will appear once all required fields are valid.",
            class_="results-pending",
        )
    return None


def comparison_table(
    caption: str,
    results: tuple[ScenarioResult, ...],
    rows: list[tuple[str, list[str]]],
) -> Tag:
    """Render consistent scenario headers and accessible scrolling for both tables."""
    return core_ui.div(
        core_ui.tags.table(
            core_ui.tags.caption(caption, class_="visually-hidden"),
            core_ui.tags.thead(
                core_ui.tags.tr(
                    core_ui.tags.th("Result", scope="col"),
                    *[
                        core_ui.tags.th(
                            f"Scenario {number}",
                            core_ui.tags.small(
                                f"{result.renewal_percent:g}% renewal change",
                                class_="d-block fw-normal",
                            ),
                            scope="col",
                        )
                        for number, result in enumerate(results, start=1)
                    ],
                )
            ),
            core_ui.tags.tbody(
                *[
                    core_ui.tags.tr(
                        core_ui.tags.th(label, scope="row"),
                        *[core_ui.tags.td(value) for value in values],
                    )
                    for label, values in rows
                ]
            ),
            class_="table comparison-table",
        ),
        class_="comparison-scroll",
        tabindex="0",
        role="region",
        **{"aria-label": caption},
    )


def forecast_affordability_message(result: ScenarioResult) -> str:
    """Prioritise unaffordable retained cover over an additional-joiner gap."""
    if result.retained_balance < 0:
        return (
            "Cover for current members expected to stay exceeds the budget. "
            "No additional employees are affordable."
        )
    if result.retention_based_enrolment_gap > 0:
        return (
            "Expected joiners exceed additional employees affordable under "
            "expected retention by "
            f"{format_membership(result.retention_based_enrolment_gap)}."
        )
    return "Forecast cover is within budget."


def full_cover_affordability_message(
    result: ScenarioResult, eligible_count: int
) -> str:
    """Prioritise unaffordable current cover over the full-cover joiner gap."""
    if result.existing_cover_unaffordable:
        return (
            "Keeping all current members exceeds the budget. "
            "No additional employees are affordable if all current members stay."
        )
    if eligible_count > result.additional_places:
        return (
            "If all current members stay, the budget falls short of covering all additional "
            f"eligible employees by {eligible_count - result.additional_places:,}."
        )
    return "The budget can cover everyone."


@render.ui
def scenario_comparison_output() -> Tag | None:
    """Compare three renewal changes without repeating shared membership figures."""
    if not inputs_are_valid():
        return None

    results = scenario_results()
    membership = results[0]  # Renewal changes cost, not expected membership.
    eligible_count = validated_additional_eligible_count()
    current_count = validated_currently_covered_count()

    forecast_rows = [
        (
            "Annual cost per covered employee after renewal",
            [f"£{result.unit_cost:,.2f}" for result in results],
        ),
        (
            "Forecast annual cost",
            [f"£{result.expected_cost:,.2f}" for result in results],
        ),
        (
            "Forecast budget outcome",
            [format_budget_outcome(result.balance) for result in results],
        ),
        (
            "Additional employees affordable — at your expected retention",
            [f"{result.retention_based_additional_places:,}" for result in results],
        ),
        (
            "Additional employees affordable — if all current members stay",
            [f"{result.additional_places:,}" for result in results],
        ),
    ]
    full_cover_rows = [
        (
            "Annual cost at full cover",
            [f"£{result.full_cost:,.2f}" for result in results],
        ),
        (
            "Full-cover budget outcome",
            [format_budget_outcome(result.full_balance) for result in results],
        ),
    ]

    forecast_checks = [forecast_affordability_message(result) for result in results]
    full_cover_checks = [
        full_cover_affordability_message(result, eligible_count) for result in results
    ]

    # Keep warnings under their scenario in the relevant comparison.
    if any(
        result.retained_balance < 0 or result.retention_based_enrolment_gap > 0
        for result in results
    ):
        forecast_rows.append(("Forecast affordability checks", forecast_checks))
    if any(result.full_balance < 0 for result in results):
        full_cover_rows.append(("Full-cover affordability checks", full_cover_checks))

    return core_ui.div(
        core_ui.h3(
            f"Forecast membership: {format_membership(membership.total_coverage)} employees"
        ),
        core_ui.p(
            f"Based on {membership.retention_percent:g}% retention and "
            f"{validated_take_up_percent():g}% take-up."
        ),
        core_ui.tags.ul(
            core_ui.tags.li(
                "Current members expected to stay: ",
                core_ui.tags.strong(format_membership(membership.retained_members)),
            ),
            core_ui.tags.li(
                "Expected additional joiners: ",
                core_ui.tags.strong(
                    f"{format_membership(membership.additional_enrolment)} "
                    f"of {eligible_count:,} eligible"
                ),
            ),
        ),
        core_ui.p(
            "Forecasts can include fractions because they apply percentages to employee "
            "counts. The same membership forecast applies to all three renewal scenarios.",
            class_="text-muted",
        ),
        core_ui.h3("Compare renewal scenarios"),
        comparison_table(
            "Forecast cost and additional affordability", results, forecast_rows
        ),
        core_ui.h3("Full-cover budget check"),
        core_ui.p(
            "Full cover assumes all current members stay and all additional eligible employees join: "
            f"{current_count + eligible_count:,} employees covered."
        ),
        comparison_table(
            "Full-cover cost and budget outcome", results, full_cover_rows
        ),
        core_ui.h3("Notes and assumptions", class_="results-guide-heading"),
        core_ui.p(
            "The same annual cost per employee applies to everyone. Estimates cover a full "
            "year without adjusting for joining or leaving dates. No separate taxes or fees "
            "are added.",
            class_="text-muted",
        ),
        class_="estimator-results",
    )
