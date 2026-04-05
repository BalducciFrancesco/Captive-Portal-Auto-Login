from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.webdriver import WebDriver as ChromeDriver
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.firefox.webdriver import WebDriver as FirefoxDriver
from selenium.webdriver.remote.webdriver import WebDriver
from tenacity import retry, stop_after_attempt, wait_fixed
from modules.settings import before_sleep, conf, give_up, log_attempt


@retry(
    stop=stop_after_attempt(conf.retry_attempts),
    wait=wait_fixed(conf.retry_delay),
    reraise=True,
    before=log_attempt,
    before_sleep=before_sleep(f"Failed attempt to initialize browser and navigate to captive URL."),
    retry_error_callback=give_up(f"Unable to initialize browser and navigate to captive URL. Please check your browser and driver paths in the configuration file, as well as your network connection.")
)
def init_browser(captive_url: str) -> WebDriver:
    options = (ChromeOptions() if conf.browser_kind == "chrome" else FirefoxOptions())
    options.binary_location = conf.browser_path
    options.add_argument("--disable-chrome-captive-portal-detector")
    options.add_argument("--ignore-certificate-errors")
    options.add_argument("--ignore-ssl-errors=yes")
    options.add_argument("--allow-running-insecure-content")
    options.set_capability("acceptInsecureCerts", True)
    if conf.headless:
        options.add_argument("--headless")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")


    if conf.browser_kind == "firefox":
        service = FirefoxService(executable_path=conf.driver_path) if conf.driver_path else FirefoxService()
        driver = FirefoxDriver(service=service, options=options)    # type: ignore
    elif conf.browser_kind == "chrome":
        service = ChromeService(executable_path=conf.driver_path) if conf.driver_path else ChromeService()
        driver = ChromeDriver(service=service, options=options)     # type: ignore

    driver.set_page_load_timeout(conf.retry_timeout)

    # Connect to the captive portal URL to trigger the login page
    driver.get(captive_url)

    return driver