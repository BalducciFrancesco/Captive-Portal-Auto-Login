import time
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException

def login(driver, username, password):
    """
    Performs the login action on the captive portal page.
    """
    try:
        username_field = driver.find_element(By.ID, "username")
        password_field = driver.find_element(By.ID, "password")
        submit_button = driver.find_element(By.TAG_NAME, "button")

        username_field.send_keys(username)
        password_field.send_keys(password)
        submit_button.click()
        print("Entered credentials and submitted the form.")

        time.sleep(5)  # Wait for login to process

        # Check for success by looking for the username field again
        try:
            driver.find_element(By.ID, "username")
            print("Login failed.")
            return False
        except NoSuchElementException:
            print("Login successful.")
            return True
    except NoSuchElementException as e:
        print(f"Error during login process: Could not find an element - {e}")
        return False
