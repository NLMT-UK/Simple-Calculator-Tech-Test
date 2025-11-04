import pytest

# Constants
# Prototype (build 0) is stable; builds 1–8 contain intentional defects per the app description.
# Build 9 is included for completeness and validation of missing controls.
ALL_BUILDS = list(range(0, 10))


# Tests
@pytest.mark.build
@pytest.mark.parametrize("build", ALL_BUILDS)
@pytest.mark.parametrize(
    "op, a, b, expected",
    [
        (0, "10", "5", "15"),  # Add
        (1, "10", "5", "5"),   # Subtract
        (2, "10", "5", "50"),  # Multiply
        (3, "10", "5", "2"),   # Divide (integer-only mode)
    ],
)
def test_integer_only_flag(calc, build, op, a, b, expected):
    """
    Verify that arithmetic operations behave correctly when
    'Integers Only' mode is enabled across all builds.

    Known issue:
      - Some builds will return incorrect results or fail to calculate.
    """
    calc.choose_build(build) \
        .set_integer_only(True) \
        .set_numbers(a, b) \
        .choose_operation(op) \
        .calculate()

    assert calc.read_answer() == expected


@pytest.mark.build
@pytest.mark.parametrize("build", ALL_BUILDS)
def test_concatenate_ignores_integer_toggle(calc, build):
    """
    Verify that the 'Integers Only' checkbox is ignored when using
    the 'Concatenate' operation.

    This confirms that string concatenation remains unaffected
    by numeric mode toggles across all builds.
    """
    calc.choose_build(build) \
        .set_integer_only(True) \
        .set_numbers("13", "2") \
        .choose_operation(4) \
        .calculate()

    assert calc.read_answer() == "132"
