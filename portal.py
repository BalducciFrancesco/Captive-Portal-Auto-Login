import time
import logging as log
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from settings import Settings

def login(driver, settings: Settings):
    """
    Performs the login action on the captive portal page.
    """
    try:
        username_field = driver.find_element(By.ID, "username")
        password_field = driver.find_element(By.ID, "password")
        submit_button = driver.find_element(By.TAG_NAME, "button")

        username_field.send_keys(settings.username)
        password_field.send_keys(settings.password)
        submit_button.click()
        log.info("Entered credentials and submitted the form.")

        time.sleep(5)  # Wait for login to process

        # Check for success by looking for the username field again
        try:
            driver.find_element(By.ID, "username")
            log.warning("Login failed.")
            return False
        except NoSuchElementException:
            log.info("Login successful.")
            return True
    except NoSuchElementException as e:
        log.error(f"Could not find an element - {e}")
        return False
