import os
import platform
from datetime import datetime

import allure
import pytest

from src.pages.calculator_page import CalculatorPage
from src.utils.web import BASE_URL, create_driver


# Allure environment metadata
@pytest.fixture(scope="session", autouse=True)
def write_allure_environment():
    """
    Create reports/allure-results/environment.properties so Allure
    can display environment info (OS, browser, AUT URL, etc.) on the
    overview page.
    """
    os.makedirs("reports/allure-results", exist_ok=True)
    env_path = os.path.join("reports", "allure-results", "environment.properties")

    with open(env_path, "w", encoding="utf-8") as f:
        f.write("ApplicationUnderTest=https://testsheepnz.github.io/BasicCalculator.html\n")
        f.write("TestSuite=Regression & Validation (All Builds)\n")
        f.write(f"OS={platform.system()} {platform.release()}\n")
        f.write("Browser=Chrome (headless)\n")
        f.write("Framework=pytest + Selenium\n")
        f.write("Executor=Local Run\n")


# Selenium fixtures
@pytest.fixture(scope="session")
def driver():
    """
    Create a single WebDriver instance for the session.
    Closed automatically at the end of the test run.
    """
    drv = create_driver()
    yield drv
    drv.quit()


@pytest.fixture(scope="session")
def base_url():
    """
    Expose the base URL so tests can override or parametrize it later if needed.
    """
    return BASE_URL


@pytest.fixture()
def calc(driver, base_url):
    """
    Return a CalculatorPage that has already been opened.
    This is the main fixture used by tests.
    """
    page = CalculatorPage(driver).open(base_url)
    return page


# Evidence capture
@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """
    After each test phase, capture screenshot and HTML when useful.

    We want evidence for:
      - failed tests
      - xfailed tests (pytest reports these as skipped, but with report.wasxfail)
      - xpassed tests
      - setup failures (for example, driver could not load page in time)

    The hook tries to get a driver either directly from the test function
    or via the 'calc' fixture.
    """
    outcome = yield
    report = outcome.get_result()

    # Only Setup and Call phases are relevant
    in_relevant_phase = report.when in ("setup", "call")

    # Pytest marks expected xfail as "skipped" with report.wasxfail set
    is_disguised_xfail = report.outcome == "skipped" and hasattr(report, "wasxfail")

    # Real bad outcomes
    is_bad_outcome = report.outcome in ("failed", "xfailed", "xpassed")

    if not (in_relevant_phase and (is_bad_outcome or is_disguised_xfail)):
        return

    # Try to obtain a driver
    driver = item.funcargs.get("driver")
    if not driver:
        calc = item.funcargs.get("calc")
        if calc:
            driver = calc.driver

    if not driver:
        # Test did not use WebDriver; nothing to capture
        return

    # Ensure screenshot directory exists
    screenshot_dir = os.path.join("reports", "screenshots")
    os.makedirs(screenshot_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    test_name = item.name

    # Screenshot
    screenshot_path = os.path.join(screenshot_dir, f"{test_name}-{timestamp}.png")
    try:
        driver.save_screenshot(screenshot_path)
        with open(screenshot_path, "rb") as f:
            allure.attach(
                f.read(),
                name=f"screenshot-{test_name}",
                attachment_type=allure.attachment_type.PNG,
            )
    except Exception:
        # Do not break the test run if screenshot capture fails
        pass

    # Page source
    try:
        html_source = driver.page_source
        allure.attach(
            html_source,
            name=f"page-source-{test_name}",
            attachment_type=allure.attachment_type.HTML,
        )
    except Exception:
        pass
