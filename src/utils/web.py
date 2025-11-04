import os
from dotenv import load_dotenv

from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.firefox.service import Service as FirefoxService

from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.firefox import GeckoDriverManager

# Load environment variables from .env if present
load_dotenv()

# Default environment values
BASE_URL = os.getenv("BASE_URL", "https://testsheepnz.github.io/BasicCalculator.html")
BROWSER = os.getenv("BROWSER", "chrome").lower()
HEADLESS = os.getenv("HEADLESS", "true").lower() in {"1", "true", "yes"}


def create_driver():
    # Chrome setup
    if BROWSER == "chrome":
        options = ChromeOptions()
        options.page_load_strategy = "eager"

        # Run headless if specified
        if HEADLESS:
            options.add_argument("--headless=new")

        # Ubuntu/CI stability flags to prevent 'DevToolsActivePort' errors
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")

        # Consistent window size across environments
        options.add_argument("--window-size=1280,900")

        service = ChromeService(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)

    # Firefox setup
    elif BROWSER == "firefox":
        options = FirefoxOptions()
        if HEADLESS:
            options.add_argument("-headless")

        service = FirefoxService(GeckoDriverManager().install())
        driver = webdriver.Firefox(service=service, options=options)

    # Unsupported browser handling
    else:
        raise RuntimeError(f"Unsupported browser: {BROWSER}")

    # Reasonable timeout to handle public site delays
    driver.set_page_load_timeout(30)
    return driver
