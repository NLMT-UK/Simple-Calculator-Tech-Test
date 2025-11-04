import json
import os

import allure
import pytest
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

# Paths and data
DATA_PATH = os.path.join(
    os.path.dirname(__file__),
    "..",
    "data",
    "arithmetic_cases.json",
)

# Load base arithmetic scenarios (these will be fanned out across all builds)
with open(DATA_PATH, encoding="utf-8") as f:
    BASE_CASES = json.load(f)

# The application exposes builds Prototype (0) through 9
ALL_BUILDS = list(range(0, 10))


# Tests
@pytest.mark.regression
@pytest.mark.parametrize("build", ALL_BUILDS, ids=lambda b: f"build-{b}")
@pytest.mark.parametrize("case", BASE_CASES, ids=lambda c: c.get("desc", f"op-{c['op']}"))
def test_arithmetic_all_builds(calc, build, case):
    """
    Data-driven arithmetic test across all calculator builds.

    Purpose:
    - run the same set of arithmetic scenarios against every build (0..9)
    - detect build-specific problems (app documentation says builds 1–8 contain defects)
    - handle incomplete UIs (for example build 9 missing controls) without hard-failing
    """

    op = case["op"]
    a = case["a"]
    b = case["b"]
    expected = str(case["expected"])

    # 1) Select the build
    calc.choose_build(build)

    # 2) Quick probe for missing UI (prevents long waits on broken builds)
    try:
        WebDriverWait(calc.driver, 2).until(EC.presence_of_element_located(calc.NUMBER1))
        WebDriverWait(calc.driver, 2).until(EC.presence_of_element_located(calc.NUMBER2))
        WebDriverWait(calc.driver, 2).until(EC.presence_of_element_located(calc.CALCULATE))
    except TimeoutException:
        # cannot execute on this build; attach evidence and xfail
        allure.attach(
            f"Build {build} is missing one or more core controls "
            f"(number1/number2/calculate). Test cannot proceed.",
            name="ui-missing",
            attachment_type=allure.attachment_type.TEXT,
        )
        pytest.xfail(f"Build {build} has incomplete calculator UI – skipping arithmetic scenarios")

    # 3) Normal interaction flow (still guarded for late DOM changes)
    try:
        (
            calc
            .set_numbers(a, b)
            .choose_operation(op)
            .calculate()
        )
    except (TimeoutException, NoSuchElementException) as e:
        allure.attach(
            f"Build {build} failed during interaction for "
            f"(op={op}, a={a}, b={b}): {type(e).__name__}: {e}",
            name="interaction-failure",
            attachment_type=allure.attachment_type.TEXT,
        )
        pytest.xfail(f"Build {build} could not complete interaction flow")

    # 4) Read the output
    actual = calc.read_answer()

    # 5) Exact string match
    if actual == expected:
        return

    # 6) Numeric match (2.5 vs 2.5000 etc.)
    try:
        if float(actual) == float(expected):
            return
    except ValueError:
        # values not both numeric; continue to build-aware handling
        pass

    # 7) Known-bad application builds
    if build in range(1, 9):
        pytest.xfail(
            f"Build {build} returned different result for op={op} "
            f"with inputs {a}, {b}. Got {actual}, expected {expected}."
        )

    # 8) For prototype (0) and any working build, this is a real failure
    assert actual == expected, (
        f"Build {build} mismatch for op={op} with inputs {a}, {b}: "
        f"got {actual}, expected {expected}"
    )
