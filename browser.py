import logging as log
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.webdriver import WebDriver as ChromeDriver
from selenium.common.exceptions import WebDriverException

def get_browser(config):
    """
    Initializes and returns a Chrome browser instance based on the provided configuration.
    """
    options = Options()
    if config.getboolean("headless"):
        options.add_argument("--headless")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
    
    if chrome_path := config.get("chrome_path"):
        options.binary_location = chrome_path

    try:
        driver = ChromeDriver(options=options)
        driver.set_page_load_timeout(config.getint("get_timeout", 15))
        login_url = config["url"] or config["fallback_trigger_url"]
        driver.get(login_url)
        log.info(f"Navigated to: {login_url}")
        return driver
    except (WebDriverException, KeyError) as e:
        log.error(f"Failed to initialize or navigate with Chrome driver: {e}")
        return None
