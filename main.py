import time
import configparser
from pathlib import Path
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.webdriver import WebDriver as ChromeDriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import WebDriverException, NoSuchElementException

def login_to_captive_portal(config):
    """
    Logs in to a captive portal using settings from the config.
    """
    # Load credentials
    try:
        credentials_path = Path(config["captive_portal"]["credentials_file"])
        username, password = credentials_path.read_text(encoding="utf-8").strip().splitlines()
    except (KeyError, FileNotFoundError, ValueError) as e:
        print(f"Error: Could not read credentials: {e}")
        return False

    # Configure Chrome options
    options = Options()
    if config["captive_portal"].getboolean("headless"):
        options.add_argument("--headless")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
    
    if chrome_path := config["captive_portal"].get("chrome_path"):
        options.binary_location = chrome_path

    # Initialize driver
    try:
        driver = ChromeDriver(options=options)
        driver.set_page_load_timeout(config["captive_portal"].getint("get_timeout", 15))
    except WebDriverException as e:
        print(f"Error: Failed to initialize Chrome driver: {e}")
        return False

    try:
        login_url = config["captive_portal"]["url"] or config["captive_portal"]["fallback_trigger_url"]
        driver.get(login_url)
        print(f"Navigated to: {login_url}")

        # Find and fill login form
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

    except (WebDriverException, NoSuchElementException, KeyError) as e:
        print(f"Error during login process: {e}")
        return False
    finally:
        if 'driver' in locals():
            driver.quit()

def main():
    """
    Main function to run the captive portal login script.
    """
    config = configparser.ConfigParser()
    config.read("config.ini")

    retries = config["captive_portal"].getint("retries", 3)
    delay = config["captive_portal"].getint("delay", 5)

    for attempt in range(retries):
        print(f"Attempt {attempt + 1} to login to captive portal.")
        if login_to_captive_portal(config):
            print("Successfully logged in.")
            return
        print(f"Login failed. Retrying in {delay} seconds...")
        time.sleep(delay)
    
    print("Failed to login after multiple attempts.")

if __name__ == "__main__":
    main()

