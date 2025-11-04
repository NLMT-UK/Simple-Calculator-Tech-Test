from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Default explicit wait timeout (seconds)
DEFAULT_TIMEOUT = 5


# Waits
def wait_visible(driver, locator, timeout: int = DEFAULT_TIMEOUT):
    """
    Wait until the element located by 'locator' is visible on the page.

    Args:
        driver: Selenium WebDriver instance.
        locator: Tuple (By.<METHOD>, "selector") identifying the element.
        timeout: Maximum time (in seconds) to wait before raising TimeoutException.

    Returns:
        WebElement once it becomes visible.
    """
    return WebDriverWait(driver, timeout).until(
        EC.visibility_of_element_located(locator)
    )


def wait_clickable(driver, locator, timeout: int = DEFAULT_TIMEOUT):
    """
    Wait until the element located by 'locator' is clickable.

    Args:
        driver: Selenium WebDriver instance.
        locator: Tuple (By.<METHOD>, "selector") identifying the element.
        timeout: Maximum time (in seconds) to wait before raising TimeoutException.

    Returns:
        WebElement once it becomes clickable.
    """
    return WebDriverWait(driver, timeout).until(
        EC.element_to_be_clickable(locator)
    )
