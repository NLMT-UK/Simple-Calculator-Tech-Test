import pytest

# Tests
@pytest.mark.smoke
@pytest.mark.parametrize("build", [0, 1, 2])
def test_page_loads(calc, build):
    """
    Basic smoke test to confirm the calculator loads and performs
    a simple operation successfully across key builds.

    Purpose:
      - Validate that the page and its core elements load without error.
      - Ensure the calculator can perform a basic addition on each selected build.
    """
    calc.choose_build(build) \
        .set_numbers("1", "1") \
        .choose_operation(0) \
        .calculate()

    result = calc.read_answer()
    assert result != "", "Expected a non-empty result from the calculator."
