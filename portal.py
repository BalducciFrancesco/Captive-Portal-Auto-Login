import time
import logging as log
from selenium.webdriver.common.by import By
from selenium.common.exceptions import ElementNotInteractableException, NoSuchElementException
from settings import Settings


def login(driver, settings: Settings):
    """
    Performs the login action on the captive portal page.
    """
    try:
        if settings.sequence:
            log.info("Running configured login sequence.")
            run_sequence(driver, settings.sequence, settings)
        else:
            log.info("No login sequence configured, using fallback flow.")
            run_fallback(driver, settings)

        log.info("Sequence executed, waiting 15s to check connection status...")
        time.sleep(15)  
        driver.get("https://captive.apple.com")
        return "captive.apple.com" in driver.current_url and "Success" in driver.page_source
    except NoSuchElementException as e1:
        log.error(f"Could not find the selector element in the previous step: {e1.msg}")
        return False
    except ElementNotInteractableException as e2:
        log.error(f"Could not interact with the selector element in the previous step: {e2.msg}")
        return False


def run_sequence(driver, sequence: list[dict[str, str]], settings: Settings):
    """Runs the configured login sequence on the captive portal page."""
    for index, step in enumerate(sequence, start=1):
        action = step.get("action", "")
        selector = step.get("selector", "")
        log.info(f"Executing sequence step #{index}: '{action}' on selector '{selector}'")

        element = driver.find_element(By.CSS_SELECTOR, selector)
        if action == "click":
            element.click()
        elif action == "fill-username":
            element.send_keys(settings.username)
        elif action == "fill-password":
            element.send_keys(settings.password)
        time.sleep(settings.step_delay)

def run_fallback(driver, settings: Settings):
    """Fallback login flow for simple portals with username/password fields and a submit button."""
    username_field = driver.find_element(By.ID, "username")
    password_field = driver.find_element(By.ID, "password")
    submit_button = driver.find_element(By.TAG_NAME, "button")

    username_field.send_keys(settings.username)
    time.sleep(settings.step_delay)
    password_field.send_keys(settings.password)
    time.sleep(settings.step_delay)
    submit_button.click()
    time.sleep(settings.step_delay)
    log.info("Entered credentials and submitted the form.")
