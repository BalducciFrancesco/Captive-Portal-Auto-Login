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
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.common.exceptions import WebDriverException, NoSuchElementException

# Configuration
CREDENTIALS_FILE = "credentials.txt"  # line 1: username, line 2: password
URL = ""  # Replace with the captive portal URL if known, otherwise, the script will try to detect it.
HEADLESS = True  # Set to True to run Chrome in headless mode (recommended for servers)
CHROME_PATH = "/usr/bin/google-chrome"  # Path to Chrome executable (usually auto-detected)
CHROMEDRIVER_PATH = "/usr/bin/chromedriver"  # Path to the chromedriver

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

def login_to_captive_portal(url, username, password, headless=True):
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
    driver = webdriver.Chrome(options=options)

    try:
        driver.get(url)
        colored_print(f"Navigated to: {url}", Colors.OKBLUE)  # Improved CLI output
    except WebDriverException as e:
        colored_print(f"Error: Failed to navigate to URL: {url} - {e}", Colors.FAIL)
        driver.quit()
        return False

    # Locate the username and password input fields and the submit button
    try:
        username_field = driver.find_element(By.ID, "username")
        password_field = driver.find_element(By.ID, "password")
        submit_button = driver.find_element(By.TAG_NAME, "button")  # or By.CSS_SELECTOR, etc.
    except NoSuchElementException:
        colored_print("Error: Could not find login form elements. Check the HTML of the captive portal page.", Colors.FAIL)
        driver.quit()
        return False

    # Enter the credentials and submit the form
    username_field.send_keys(username)
    password_field.send_keys(password)
    submit_button.click()
    colored_print("Entered credentials and submitted the form.", Colors.OKBLUE)  # Improved CLI output

    # Wait for a brief period to allow the login process to complete.  Adjust as necessary.
    time.sleep(5)

    # Check for a successful login.  This is highly dependent on the specific captive portal.
    # Look for an element that indicates successful login (e.g., a welcome message,
    # a different page title, or the absence of the login form).
    try:
        # Example 1: Check for a specific element on the page after login.
        # success_element = driver.find_element(By.ID, "success-message")
        # if success_element:
        #    colored_print("Login successful (found success element).", Colors.OKGREEN)
        #    driver.quit()
        #    return True

        # Example 2: Check if the page title has changed.
        if "Success" in driver.title:
            colored_print("Login successful (title changed).", Colors.OKGREEN)
            driver.quit()
            return True

        # Example 3: Check if the login form is no longer present.
        try:
            driver.find_element(By.ID, "username")  # Try to find the username field.
            colored_print("Login failed (login form still present).", Colors.FAIL)
            driver.quit()
            return False  # If it's found, login probably failed.
        except NoSuchElementException:
            colored_print("Login successful (login form not found).", Colors.OKGREEN)
            driver.quit()
            return True  # If it's not found, login might be successful

        # If none of the above work, you'll need to inspect the captive portal's HTML
        # and come up with a reliable way to determine if login was successful.
        colored_print("Warning: Could not reliably determine login status.  Please check the script.", Colors.WARNING)
        driver.quit()
        return False  # Return false, and log/check.

    except Exception as e:
        colored_print(f"Error checking login status: {e}", Colors.FAIL)
        driver.quit()
        return False

def main():
    """
    Main function to run the captive portal login script.
    """
    retries = 3
    delay = 5  # seconds

    if not URL:
        colored_print("Error: URL is not configured.  Please set the URL variable in the script.", Colors.FAIL)
        return

    username, password = load_credentials(CREDENTIALS_FILE)
    if not username or not password:
        return

    for attempt in range(retries):
        colored_print(f"Attempt {attempt + 1} to login to captive portal at {URL}", Colors.OKBLUE)
        success = login_to_captive_portal(URL, username, password, HEADLESS)
        if success:
            colored_print("Successfully logged in to the captive portal.", Colors.OKGREEN)
            return
        else:
            colored_print(f"Login failed.  Retrying in {delay} seconds...", Colors.WARNING)
            time.sleep(delay)
    colored_print("Failed to login to the captive portal after multiple attempts.", Colors.FAIL)

if __name__ == "__main__":
    main()
