from tenacity import retry, stop_after_attempt, wait_fixed
from modules.settings import before_sleep, give_up, log_attempt
from modules.settings import conf
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.webdriver import WebDriver as ChromeDriver
from tenacity import retry, stop_after_attempt, wait_fixed


@retry(
    stop=stop_after_attempt(conf.retry_attempts),
    wait=wait_fixed(conf.retry_delay),
    reraise=True,
    before=log_attempt,
    before_sleep=before_sleep(f"Failed attempt to initialize browser and navigate to captive URL."),
    retry_error_callback=give_up(f"Unable to initialize browser and navigate to captive URL. Please check your browser and driver paths in the configuration file, as well as your network connection.")
)
def init_browser(captive_url: str) -> ChromeDriver:
    options = Options()
    options.binary_location = conf.browser_path
    options.add_argument("--disable-chrome-captive-portal-detector")
    options.add_argument("--ignore-certificate-errors")
    options.add_argument("--ignore-ssl-errors=yes")
    options.add_argument("--allow-running-insecure-content")
    options.set_capability("acceptInsecureCerts", True)
    service = Service(executable_path=conf.driver_path)

    if conf.headless:
        options.add_argument("--headless")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")

    driver = ChromeDriver(service=service, options=options)
    driver.set_page_load_timeout(conf.retry_timeout)
    driver.get(captive_url)
    return driver
