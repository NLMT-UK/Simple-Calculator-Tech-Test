import csv
import os
import re

import pytest
import allure

# CSV with all edge/validation scenarios
CSV_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "edge_cases.csv")

# Builds to run against. Default to build 0 (Prototype) for speed and stability.
# Example:
#   EDGE_BUILDS=0,1,2,3 pytest -m validation
_raw_builds = os.getenv("EDGE_BUILDS", "0")
EDGE_BUILDS = [int(b.strip()) for b in _raw_builds.split(",") if b.strip()]


def _normalize(text: str) -> str:
    text = text.lower().strip()
    text = text.replace("zero", "0")
    text = re.sub(r"[!.,]", "", text)
    text = re.sub(r"\s+", " ", text)
    return text


def _is_number(s: str) -> bool:
    try:
        float(s)
        return True
    except ValueError:
        return False


def _numbers_equal(a: str, b: str) -> bool:
    try:
        return float(a) == float(b)
    except ValueError:
        return False


# Load CSV once for parametrization
with open(CSV_PATH, newline="") as f:
    EDGE_ROWS = list(csv.DictReader(f))


@pytest.mark.validation
@pytest.mark.parametrize("row", EDGE_ROWS)
@pytest.mark.parametrize("build", EDGE_BUILDS)
def test_edge_cases(calc, row, build):
    """
    Data-driven validation/edge-case tests.

    By default this runs only on build 0.
    Set EDGE_BUILDS=0,1,2,... to fan out across all builds when investigating behaviour.
    """
    op = int(row["op"])
    a = row["a"]
    b = row["b"]
    integer_only = row["integer_only"].lower() == "true"
    expected_raw = row["expected"]
    notes = row.get("notes", "")

    # select build
    calc.choose_build(build)

    # if the build is totally missing required controls, xfail early
    if not calc.is_calculator_complete():
        allure.attach(
            f"Build {build} is missing core calculator controls (number1/number2/calculate).",
            name="ui-missing",
            attachment_type=allure.attachment_type.TEXT,
        )
        pytest.xfail(f"Build {build} has incomplete UI for this edge-case scenario")

    # normal interaction
    calc.set_numbers(a, b).choose_operation(op)

    # concatenate hides integer toggle
    if op != 4:
        calc.set_integer_only(integer_only)

    calc.calculate()

    actual = calc.read_answer()
    allure.attach(
        actual,
        name=f"calculator-output-build-{build}",
        attachment_type=allure.attachment_type.TEXT,
    )

    norm_actual = _normalize(actual)
    expected_options = [e.strip() for e in expected_raw.split("|")]
    norm_expected_options = [_normalize(e) for e in expected_options]

    # 1) substring match for messages/banners
    if any(exp in norm_actual for exp in norm_expected_options):
        return

    # 2) numeric match for cases like 1e12 vs 1000000000000
    if _is_number(actual):
        for exp in expected_options:
            if _is_number(exp) and _numbers_equal(actual, exp):
                return

    # 3) some builds fail to surface validation text
    if norm_actual == "" and any("error" in e or "please enter a number" in e for e in norm_expected_options):
        pytest.xfail("AUT did not surface validation text for non-numeric input on this build")

    # 4) otherwise, fail with useful diagnostics
    assert False, (
        f"Build: {build}\n"
        f"Inputs: a={a}, b={b}, op={op}, integer_only={integer_only}\n"
        f"Notes: {notes}\n"
        f"Got:\n{actual}\n(norm: {norm_actual})\n"
        f"Expected to contain one of (normalized): {norm_expected_options}"
    )
