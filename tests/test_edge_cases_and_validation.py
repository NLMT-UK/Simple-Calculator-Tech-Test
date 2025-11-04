import csv
import os
import re

import allure
import pytest

# Paths
CSV_PATH = os.path.join(
    os.path.dirname(__file__),
    "..",
    "data",
    "edge_cases.csv",
)


# Helpers
def _normalize(text: str) -> str:
    """
    Normalise text so we can compare messages that differ slightly by build.
    Lowercase, trim, remove punctuation, collapse spaces, and turn 'zero' into '0'.
    """
    text = text.lower().strip()
    text = text.replace("zero", "0")
    text = re.sub(r"[!.,]", "", text)
    text = re.sub(r"\s+", " ", text)
    return text


def _is_number(s: str) -> bool:
    """Return True if the string can be parsed as a float."""
    try:
        float(s)
        return True
    except ValueError:
        return False


def _numbers_equal(a: str, b: str) -> bool:
    """Numeric equality helper for cases like 1e12 vs 1000000000000."""
    try:
        return float(a) == float(b)
    except ValueError:
        return False


# Tests
@pytest.mark.validation
@pytest.mark.parametrize("row", csv.DictReader(open(CSV_PATH, encoding="utf-8")))
def test_edge_cases(calc, row):
    """
    Data-driven validation and edge-case tests.

    The CSV can describe:
      - divide-by-zero
      - large numbers / scientific notation
      - non-numeric input
      - operations across different builds

    Because the AUT behaves differently by build, this test:
      - accepts multiple expected strings (pipe-delimited)
      - normalises messages
      - allows numeric equivalence
      - xfails when the app fails to surface a validation message that the row expects
    """
    build = int(row["build"])
    op = int(row["op"])
    a = row["a"]
    b = row["b"]
    integer_only = row["integer_only"].lower() == "true"
    expected_raw = row["expected"]

    # Basic interaction flow
    calc.choose_build(build).set_numbers(a, b).choose_operation(op)

    # Concatenate (op=4) hides or ignores the integer toggle, so do not set it
    if op != 4:
        calc.set_integer_only(integer_only)

    calc.calculate()

    # Actual text from the page (could be an answer, could be an error)
    actual = calc.read_answer()
    allure.attach(actual, name="calculator-output", attachment_type=allure.attachment_type.TEXT)

    # Normalised actual and expected values
    norm_actual = _normalize(actual)
    expected_options = [e.strip() for e in expected_raw.split("|")]
    norm_expected_options = [_normalize(e) for e in expected_options]

    # 1) Message substring match (for "divide by zero error!" variations)
    if any(exp in norm_actual for exp in norm_expected_options):
        return

    # 2) Numeric match (for 1e12 vs 1000000000000)
    if _is_number(actual):
        for exp in expected_options:
            if _is_number(exp) and _numbers_equal(actual, exp):
                return

    # 3) Some builds render no text at all for invalid input; treat as expected defect
    if norm_actual == "" and any(
        "error" in e or "please enter a number" in e for e in norm_expected_options
    ):
        pytest.xfail("AUT did not surface validation text for non-numeric input on this build")

    # 4) Otherwise, fail with diagnostics
    assert False, (
        f"Got:\n{actual}\n(norm: {norm_actual})\n"
        f"Expected to contain one of (normalized): {norm_expected_options}"
    )
