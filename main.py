#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script Name: captive_portal_login.py
Description: This script uses Selenium to automate login to a captive portal on a Linux server.
             It is designed to be used with a cron job for maintaining a stable network connection.
Author: AI Assistant
Date: 2024-02-08
Version: 1.1 (Enhanced CLI Output)
Dependencies:
    - Python 3
    - Selenium (pip install selenium)
    - ChromeDriver (install via apt: `sudo apt install chromium-driver`)
    - crontab (for scheduling)
    - (Optional) Xvfb (for running Chrome in headless mode on a server: `sudo apt install xvfb`)

Configuration:
    1.  Install the dependencies listed above.
    2.  Configure the script variables below (USERNAME, PASSWORD, URL, etc.).
    3.  (Optional) If running on a server without a display, uncomment and configure the Xvfb section.
    4.  Schedule the script to run periodically using cron (see crontab instructions below).

Usage:
    1.  Save the script to a file (e.g., captive_portal_login.py).
    2.  Make the script executable: `chmod +x captive_portal_login.py`
    3.  Configure the script variables:
        -   USERNAME: The username for the captive portal.
        -   PASSWORD: The password for the captive portal.
        -   URL: The URL of the captive portal login page.  If you don't know the URL,
                 the script can try to find it, but it's more reliable if you provide it.
        -   HEADLESS:  Set to True to run Chrome in headless mode (recommended for servers).
        -   CHROME_PATH: (Optional) If Chrome is not in the default location, provide the full path
                         to the Chrome executable.
        -   CHROMEDRIVER_PATH: (Optional) If chromedriver is not in the system PATH, provide the full path.
    4.  (Optional) If running headless, ensure Xvfb is set up correctly.
    5.  Test the script manually: `./captive_portal_login.py`
    6.  Schedule the script with cron (see below).

Crontab Instructions:
    1.  Open the crontab editor: `crontab -e`
    2.  Add a line to schedule the script (e.g., to run every 30 minutes):
        `*/30 * * * * /usr/bin/python3 /path/to/captive_portal_login.py > /var/log/captive_portal_login.log 2>&1`
        -   Replace `/usr/bin/python3` with the actual path to your Python 3 executable.
        -   Replace `/path/to/captive_portal_login.py` with the actual path to your script.
        -   `> /var/log/captive_portal_login.log 2>&1` redirects output and errors to a log file.  This is highly recommended.
    3.  Save and exit the crontab editor.

Notes:
    -   This script requires network connectivity to function.
    -   The script assumes the captive portal login form has input fields with IDs
        "username" and "password", and a submit button.  You may need to modify
        the element selectors (find_element calls) if the actual form is different.
    -   Error handling is included, but captive portals can be unpredictable.  Monitor
        the log file (`/var/log/captive_portal_login.log` if you used the crontab example)
        for any errors.
    -   Running Chrome in headless mode (HEADLESS = True) is recommended for servers
        as it doesn't require a graphical display.  If you encounter issues with headless
        mode, you may need to adjust your Xvfb configuration or try running with a
        visible display (HEADLESS = False).
    -   The script includes a retry mechanism with a 5-second delay and a maximum of 3 attempts.
    -   The script now uses Chrome instead of Firefox, and installs the driver via apt.
"""

import time
import configparser
import re
from pathlib import Path
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.webdriver import WebDriver as ChromeDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import WebDriverException, NoSuchElementException, TimeoutException

# Configuration
CONFIG_FILE = "config.ini"  # should be a copy of template.ini with your settings

# ANSI color codes for CLI output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def colored_print(text, color=Colors.ENDC):
    """
    Prints text to the console with the specified color.

    Args:
        text (str): The text to print.
        color (str, optional): The color code to use. Defaults to Colors.ENDC (no color).
    """
    print(f"{color}{text}{Colors.ENDC}")

def load_config(config_file):
    config_path = Path(config_file)
    if not config_path.is_absolute():
        config_path = Path(__file__).resolve().parent / config_path

    parser = configparser.ConfigParser(interpolation=None)
    parser.read(config_path, encoding="utf-8")

    return parser["captive_portal"]

def parse_sequence(sequence_text):
    steps = []
    for raw_line in sequence_text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith(("#", ";")):
            continue

        match = re.match(r"^\[(?P<action>[a-z-]+)\]\s*(?P<selector>.+)$", line)
        if not match:
            raise ValueError(f"Invalid step: {line}")

        action = match.group("action")
        selector = match.group("selector").strip()
        if not selector:
            raise ValueError(f"Missing selector for step: {line}")

        steps.append({"action": action, "selector": selector})

    return steps

def execute_sequence(driver, sequence_text, username, password):
    for step in parse_sequence(sequence_text):
        if step["action"] == "fill-username":
            value = username
        elif step["action"] == "fill-password":
            value = password
        else:
            value = None

        element = driver.find_element(By.CSS_SELECTOR, step["selector"])

        if step["action"] == "click":
            element.click()
            continue

        if step["action"] in ("fill-username", "fill-password"):
            element.clear()
            element.send_keys(value)
            continue

        raise ValueError(f"Unsupported action: {step['action']}")

def wait_for_login_page(driver, sequence_text, get_timeout):
    if not sequence_text.strip():
        return

    steps = parse_sequence(sequence_text)
    first_selector = steps[0]["selector"]

    def ready(d):
        current = (d.current_url or "").strip().lower()
        if current.startswith("data:") or current.startswith("chrome-error://"):
            return False
        return len(d.find_elements(By.CSS_SELECTOR, first_selector)) > 0

    WebDriverWait(driver, get_timeout).until(ready)

def login_succeeded(driver):
    if "Success" in driver.title:
        return True

    try:
        driver.find_element(By.ID, "username")
        return False
    except NoSuchElementException:
        return True

def load_credentials(credentials_file):
    credentials_path = Path(credentials_file)
    if not credentials_path.is_absolute():
        credentials_path = Path(__file__).resolve().parent / credentials_path

    try:
        lines = credentials_path.read_text(encoding="utf-8").splitlines()
    except Exception as e:
        colored_print(f"Error: Could not read credentials file {credentials_path}: {e}", Colors.FAIL)
        return None, None

    if len(lines) < 2:
        colored_print(
            f"Error: Credentials file {credentials_path} must have username on line 1 and password on line 2.",
            Colors.FAIL,
        )
        return None, None

    username = lines[0].strip()
    password = lines[1].strip()
    if not username or not password:
        colored_print(
            f"Error: Credentials file {credentials_path} must have non-empty username/password.",
            Colors.FAIL,
        )
        return None, None

    return username, password

def login_to_captive_portal(
    url,
    username,
    password,
    headless=True,
    sequence_text="",
    get_timeout=15,
    wait_for_redirect=False,
):
    """
    Logs in to a captive portal.

    Args:
        url (str): The URL of the captive portal login page.
        username (str): The username for the captive portal.
        password (str): The password for the captive portal.
        headless (bool, optional): Whether to run the browser in headless mode. Defaults to True.

    Returns:
        bool: True if login was successful, False otherwise.
    """
    options = Options()
    if headless:
        options.add_argument("--headless")
        options.add_argument("--disable-gpu")  # Recommended for headless mode
        options.add_argument("--no-sandbox")  # For running as root in Docker/CI
        options.add_argument("--disable-dev-shm-usage")  # Overcome limited resource issues
    # Set Chrome binary path if necessary
    if CHROME_PATH:
        options.binary_location = CHROME_PATH

    # Initialize the Chrome driver
    driver = ChromeDriver(options=options)
    driver.set_page_load_timeout(get_timeout)

    try:
        driver.get(url)
        colored_print(f"Navigated to: {url}", Colors.OKBLUE)  # Improved CLI output
    except TimeoutException:
        colored_print(f"Error: Timed out after {get_timeout}s while loading URL: {url}", Colors.FAIL)
        driver.quit()
        return False
    except WebDriverException as e:
        colored_print(f"Error: Failed to navigate to URL: {url} - {e}", Colors.FAIL)
        driver.quit()
        return False

    if wait_for_redirect:
        try:
            wait_for_login_page(driver, sequence_text, get_timeout)
        except TimeoutException:
            colored_print(
                f"Error: Redirect/login page not ready after {get_timeout}s. Current URL: {driver.current_url}",
                Colors.FAIL,
            )
            driver.quit()
            return False
        except ValueError as e:
            colored_print(f"Error: Invalid sequence config: {e}", Colors.FAIL)
            driver.quit()
            return False

    try:
        if sequence_text.strip():
            execute_sequence(driver, sequence_text, username, password)
            colored_print("Executed configured captive portal steps.", Colors.OKBLUE)
        else:
            username_field = driver.find_element(By.ID, "username")
            password_field = driver.find_element(By.ID, "password")
            submit_button = driver.find_element(By.TAG_NAME, "button")
            username_field.send_keys(username)
            password_field.send_keys(password)
            submit_button.click()
            colored_print("Entered credentials and submitted the form.", Colors.OKBLUE)
    except (NoSuchElementException, ValueError) as e:
        colored_print(f"Error: Could not complete login steps: {e}", Colors.FAIL)
        driver.quit()
        return False

    # Wait for a brief period to allow the login process to complete.  Adjust as necessary.
    time.sleep(5)

    try:
        success = login_succeeded(driver)
        colored_print("Login successful." if success else "Login failed.", Colors.OKGREEN if success else Colors.FAIL)
        driver.quit()
        return success

    except Exception as e:
        colored_print(f"Error checking login status: {e}", Colors.FAIL)
        driver.quit()
        return False

def main():
    """
    Main function to run the captive portal login script.
    """
    config = load_config(CONFIG_FILE)
    if not config:
        colored_print(f"Error: Failed to load configuration from {CONFIG_FILE}.", Colors.FAIL)
        return

    credentials_file = config["credentials_file"]
    login_url = config["url"].strip()
    fallback_trigger_url = config["fallback_trigger_url"].strip()
    headless = config["headless"].lower() in ("1", "true", "yes", "on")
    retries = int(config["retries"])
    delay = int(config["delay"])
    get_timeout = int(config.get("get_timeout", "15"))
    sequence_text = config.get("sequence", "").strip()

    global CHROME_PATH, CHROMEDRIVER_PATH
    CHROME_PATH = config["chrome_path"].strip()
    CHROMEDRIVER_PATH = config["chromedriver_path"].strip()

    using_fallback_url = False
    if not login_url:
        login_url = fallback_trigger_url
        using_fallback_url = True
        colored_print(f"URL not configured. Using fallback trigger URL: {login_url}", Colors.WARNING)

    username, password = load_credentials(credentials_file)
    if not username or not password:
        return

    for attempt in range(retries):
        colored_print(f"Attempt {attempt + 1} to login to captive portal at {login_url}", Colors.OKBLUE)
        success = login_to_captive_portal(
            login_url,
            username,
            password,
            headless,
            sequence_text,
            get_timeout,
            using_fallback_url,
        )
        if success:
            colored_print("Successfully logged in to the captive portal.", Colors.OKGREEN)
            return
        else:
            colored_print(f"Login failed.  Retrying in {delay} seconds...", Colors.WARNING)
            time.sleep(delay)
    colored_print("Failed to login to the captive portal after multiple attempts.", Colors.FAIL)

if __name__ == "__main__":
    main()
