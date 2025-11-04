import os
from dotenv import load_dotenv

from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.firefox.service import Service as FirefoxService

from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.firefox import GeckoDriverManager


"""
web.py
Utility module for creating and configuring Selenium WebDriver instances.

Loads environment variables from a .env file to allow flexible configuration
for browser type, headless mode, and target base URL.
"""

# Configuration
load_dotenv()

BASE_URL = os.getenv("BASE_URL", "https://testsheepnz.github.io/BasicCalculator.html")
BROWSER = os.getenv("BROWSER", "chrome").lower()
HEADLESS = os.getenv("HEADLESS", "true").lower() in {"1", "true", "yes"}


# Driver creation
def create_driver():
    """
    Create and return a configured WebDriver instance based on environment settings.

    Supports Chrome and Firefox.
    Defaults:
      - Chrome in headless mode
      - 1280x900 window size
      - Page load strategy set to 'eager' for faster returns from driver.get(...)

    Returns:
        WebDriver: a ready-to-use Selenium WebDriver instance.
    """
    if BROWSER == "chrome":
        options = ChromeOptions()
        options.page_load_strategy = "eager"  # improves test speed by not waiting for full page load

        if HEADLESS:
            options.add_argument("--headless=new")  # use new headless mode for stability
        options.add_argument("--window-size=1280,900")

        service = ChromeService(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)

    elif BROWSER == "firefox":
        options = FirefoxOptions()
        if HEADLESS:
            options.add_argument("-headless")

        service = FirefoxService(GeckoDriverManager().install())
        driver = webdriver.Firefox(service=service, options=options)

    else:
        raise RuntimeError(f"Unsupported browser: {BROWSER}")

    # Set a reasonable page load timeout (in seconds)
    driver.set_page_load_timeout(30)
    return driver
