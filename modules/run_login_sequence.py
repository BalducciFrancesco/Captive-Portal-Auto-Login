import logging as log
from selenium.webdriver.remote.webdriver import WebDriver
from tenacity import Retrying, stop_after_attempt, wait_fixed

from modules.settings import before_sleep, conf, give_up, log_attempt

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait


def run_login_sequence(driver: WebDriver) -> WebDriver:
    total_steps = len(conf.login_sequence)

    for index, step in enumerate(conf.login_sequence, start=1):
        action = step.get("action", "")
        selector = step.get("selector", "")

        for attempt in Retrying(
            stop=stop_after_attempt(conf.retry_attempts),
            wait=wait_fixed(conf.retry_delay),
            reraise=True,
            before=log_attempt,
            before_sleep=before_sleep(f"Failed attempt for login step #{index} ({action} on '{selector}')"),
            retry_error_callback=give_up(f"Unable to complete login step #{index} ({action} on '{selector}')"),
        ):
            with attempt:
                log.info(f"Executing sequence step {index}/{total_steps}: '{action}' on '{selector}'")
                try:
                    # Wait for the page to load before interacting with elements
                    WebDriverWait(driver, conf.retry_timeout).until(lambda d: d.execute_script("return document.readyState") == "complete")

                    # Find the element and perform the specified action
                    element = driver.find_element(By.CSS_SELECTOR, selector)

                    # Perform the specified action on the element
                    if action == "click":
                        element.click()
                    elif action == "fill-username":
                        element.send_keys(conf.username) # type: ignore
                    elif action == "fill-password":
                        element.send_keys(conf.password)
                except Exception as e:
                    raise RuntimeError(f"Login step #{index} failed ({action} on '{selector}')") from e

    # Successfully completed all steps, return the driver for the next phase
    return driver