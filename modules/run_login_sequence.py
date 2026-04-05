from tenacity import retry, stop_after_attempt, wait_fixed
from modules.settings import before_sleep, give_up, log_attempt
from modules.settings import conf
from selenium.webdriver.chrome.webdriver import WebDriver as ChromeDriver
from tenacity import retry, stop_after_attempt, wait_fixed
import logging as log
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.webdriver import WebDriver as ChromeDriver
from tenacity import retry, stop_after_attempt, wait_fixed

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait


@retry(
    stop=stop_after_attempt(conf.retry_attempts),
    wait=wait_fixed(conf.retry_delay),
    reraise=True,
    before=log_attempt,
    before_sleep=before_sleep(f"Failed attempt to initialize browser and navigate to captive URL."),
    retry_error_callback=give_up(f"Unable to initialize browser and navigate to captive URL. Please check your browser and driver paths in the configuration file, as well as your network connection.")
)
def run_login_sequence(driver: ChromeDriver) -> ChromeDriver:
    for index, step in enumerate(conf.login_sequence, start=1):
        action = step.get("action", "")
        selector = step.get("selector", "")
        log.info(f"Executing sequence step {index} out of {len(conf.login_sequence)}: '{action}' on selector '{selector}'")

        # Wait for the document to be ready before interacting with elements
        try:
            WebDriverWait(driver, conf.retry_timeout).until(lambda d: d.execute_script("return document.readyState") == "complete")
        except TimeoutException as e:
            raise RuntimeError(f"Document was not ready within the timeout of {conf.retry_timeout}s for step #{index}") from e

        # Find the element to interact with
        try:
            element = driver.find_element(By.CSS_SELECTOR, selector)
        except Exception as e:
            raise RuntimeError(f"Failed to find element for step #{index} with selector '{selector}'") from e
        
        # Perform the specified action on the element
        try:
            if action == "click":
                element.click()
            elif action == "fill-username":
                element.send_keys(conf.username)
            elif action == "fill-password":
                element.send_keys(conf.password)
        except Exception as e:
            raise RuntimeError(f"Failed to perform action '{action}' on element for step #{index}") from e
        
    # Successfully completed all steps, return the driver
    return driver