from __future__ import annotations

from selenium.common.exceptions import (
    NoAlertPresentException,
    NoSuchElementException,
    TimeoutException,
)
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select, WebDriverWait

from src.utils.waits import wait_clickable, wait_visible


class CalculatorPage:
    """
    Page Object for the TestSheepNZ Basic Calculator.

    This page is intentionally unstable across builds (0–9), so this
    object is defensive:
      - detects when key controls are missing,
      - reads results from the normal answer field or from page text,
      - captures alert text when the app triggers a JS alert.
    """

    URL: str | None = None  # set by the test fixture when calling .open(...)

    # Core element locators
    SELECT_BUILD = (By.CSS_SELECTOR, "#selectBuild")
    NUMBER1 = (By.CSS_SELECTOR, "#number1Field")
    NUMBER2 = (By.CSS_SELECTOR, "#number2Field")
    OPERATION = (By.CSS_SELECTOR, "#selectOperationDropdown")
    CALCULATE = (By.CSS_SELECTOR, "#calculateButton")
    ANSWER = (By.CSS_SELECTOR, "#numberAnswerField")
    INTEGER_ONLY = (By.CSS_SELECTOR, "#integerSelect")

    # Fallback locator for inline error text
    PAGE_BODY = (By.TAG_NAME, "body")

    def __init__(self, driver: WebDriver) -> None:
        self.driver = driver
        self._last_alert_text: str | None = None  # stores alert text if any appear

    # Navigation #
    def open(self, base_url: str) -> "CalculatorPage":
        """
        Open the calculator page and wait until it is ready.
        Retries once on TimeoutException due to intermittent site slowness.
        """
        try:
            self.driver.get(base_url)
        except TimeoutException:
            self.driver.get(base_url)

        wait_visible(self.driver, self.SELECT_BUILD)
        return self

    # Helpers #
    def is_calculator_complete(self) -> bool:
        """
        Return False if any essential inputs/buttons are missing (e.g. build 9).
        Allows tests to xfail early instead of failing on missing elements.
        """
        try:
            self.driver.find_element(*self.NUMBER1)
            self.driver.find_element(*self.NUMBER2)
            self.driver.find_element(*self.CALCULATE)
            return True
        except NoSuchElementException:
            return False

    # Interactions
    def choose_build(self, build_value: int | str) -> "CalculatorPage":
        """Select a calculator build from the dropdown."""
        select = Select(wait_visible(self.driver, self.SELECT_BUILD))
        select.select_by_value(str(build_value))
        return self

    def set_numbers(self, a: str, b: str) -> "CalculatorPage":
        """
        Enter the first and second numbers.
        Tests should confirm calculator completeness before calling.
        """
        n1 = wait_visible(self.driver, self.NUMBER1)
        n1.clear()
        n1.send_keys(a)

        n2 = wait_visible(self.driver, self.NUMBER2)
        n2.clear()
        n2.send_keys(b)

        return self

    def choose_operation(self, op_value: int | str) -> "CalculatorPage":
        """
        Select an operation.
        Operation mapping:
            0 = Add
            1 = Subtract
            2 = Multiply
            3 = Divide
            4 = Concatenate
        """
        select = Select(wait_visible(self.driver, self.OPERATION))
        select.select_by_value(str(op_value))
        return self

    def set_integer_only(self, enabled: bool) -> "CalculatorPage":
        """
        Toggle the 'Integers only' checkbox.
        Called only for operations where this option exists.
        """
        checkbox = wait_clickable(self.driver, self.INTEGER_ONLY)
        if checkbox.is_selected() != enabled:
            checkbox.click()
        return self

    # Actions
    def calculate(self) -> "CalculatorPage":
        """
        Click 'Calculate' and handle any resulting alert.
        Stores alert text for later retrieval.
        """
        btn = wait_clickable(self.driver, self.CALCULATE)
        btn.click()

        try:
            alert = WebDriverWait(self.driver, 5).until(EC.alert_is_present())
            self._last_alert_text = alert.text
            alert.accept()
        except (TimeoutException, NoAlertPresentException):
            self._last_alert_text = None

        return self

    # Result Accessors
    def read_answer(self) -> str:
        """
        Return the calculator output text.

        Resolution order:
          1. captured alert text (if any)
          2. #numberAnswerField value (normal case)
          3. page body text (fallback for broken builds)
        """
        if self._last_alert_text:
            return self._last_alert_text

        try:
            answer_el = wait_visible(self.driver, self.ANSWER)
            return answer_el.get_attribute("value")
        except (TimeoutException, NoSuchElementException):
            pass

        try:
            body = self.driver.find_element(*self.PAGE_BODY)
            return body.text.strip()
        except Exception:
            return ""
