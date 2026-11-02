# PMI coverage and budget estimator

A one-page Shiny for Python app comparing PMI coverage, cost and
affordability across three renewal scenarios. This README is for
colleagues reviewing or extending the code — end-user guidance lives in
the app's own labels and help text.

## Setup and run

```powershell
uv sync
uv run shiny run --reload --launch-browser app.py
```

`uv sync` installs the reusable `pmi_estimator` package in editable mode,
so source edits are picked up without reinstalling. Run it after pulling a
packaging change, then restart any already-running Shiny server.

## Project structure

```text
app.py                        Shiny Express entry point
www/styles.css                Browser styling
src/pmi_estimator/
    __init__.py               Package overview
    calculations.py           Pure financial formulas
    results.py                Scenario assembly and result data
    validation.py             Numeric validation
    formatting.py             Display text
tests/                        Model, validation and formatting checks
pyproject.toml                Dependencies, build and tool configuration
uv.lock                       Locked dependencies
```

`app.py` is the sole application entry point; the wheel built by
`uv build --wheel` distributes only the reusable `pmi_estimator` package.
Import reusable code with names such as
`from pmi_estimator.results import calculate_scenario`; tests use the
installed package, so no manual `PYTHONPATH` configuration is needed.

For a code walkthrough, start with `validation.py`, then `calculations.py`,
`results.py`, `formatting.py` and finally `app.py`. The app follows the page
order; each input keeps its validation and feedback nearby. Its shared
reactive `scenario_results()` calls `results.calculate_scenario()` for each
renewal change; both tables and warnings read the returned values.

## Inputs

| Input | Type | Required | Notes |
|---|---|---|---|
| Annual PMI budget (£) | Decimal, ≥ 0 | Yes | Funds existing and additional cover |
| Currently covered employees | Whole count, ≥ 0 | Yes | |
| Additional employees eligible for cover | Whole count, ≥ 0 | Yes | Excludes those already covered |
| Current annual cost per covered employee (£) | Decimal, > 0 | Yes | No separate taxes/fees are added |
| Expected retention (%) | 0–100, step 0.01 | Yes | Applies only to current members |
| Expected take-up (%) | 0–100, step 0.01 | Yes | Applies only to additional eligible employees |
| Three renewal changes (%) | > -100, no maximum | Yes (all three) | Scenario identity and entry order are preserved, including duplicates |

All fields start blank. Zero is valid for budget, employee counts and
renewal change. Employee cost must be positive; renewal change must
exceed -100%. Results appear only once every input is valid.

## Model summary

- Expected retained members = current members × retention / 100.
- Expected total membership = retained members + expected additional
  joiners (take-up applies only to the additional group). Membership stays
  fractional; only affordable headcounts are floored.
- Full cover assumes 100% retention and 100% take-up regardless of the
  selected assumptions, using the selected renewal change.
- Additional affordability has two views: reserving expected retained
  members (depends on forecast departures happening), and reserving all
  current members (conservative, retention-independent). Both floor to
  whole people and cap at eligibility.

Worked example: 80 current members at 90% retention, 40 eligible at 75%
take-up, £1,000 unit cost, 10% renewal, £120,000 budget → 102 expected
members, £112,200 forecast cost, £7,800 remaining, £132,000 full-cover
cost, 37 additional places at expected retention, 29 if all current
members stay.

## Assumptions and limitations

- Results are illustrative planning estimates, not an insurer quotation.
- The same renewed annual unit cost applies to existing and additional
  members; it is not prorated for joining or leaving dates within the year.
- Entered renewal changes are user-supplied assumptions, not app
  recommendations or market forecasts.
- Total affordable capacity (uncapped by eligibility) is retained in the
  model but omitted from the compact UI.

Shared formulas live in `calculations.py`, scenario assembly in
`results.py`, validation in `validation.py`, and display formatting in
`formatting.py`.

## Checks

```powershell
uv run pytest -q
uv run ruff format .
uv run ruff check .
uv run mypy .
```

Save Python files as UTF-8 without a byte-order mark so Shiny Express can
parse them.

## Code conventions

Descriptive snake_case names, type annotations and short docstrings
explaining purpose and important contracts. Section comments in longer
files; comments explain non-obvious decisions rather than narrating each
statement. Keep financial formulas separate from Shiny and display text.
Tests use descriptive names and literal reference outcomes where
practical.
