import configparser
import time
from pathlib import Path
from browser import get_browser
from portal import login

def attempt_login(config):
    """
    Attempts to log in to the captive portal.
    """
    portal_config = config["captive_portal"]
    
    # Load credentials
    try:
        credentials_path = Path(portal_config["credentials_file"])
        username, password = credentials_path.read_text(encoding="utf-8").strip().splitlines()
    except (KeyError, FileNotFoundError, ValueError) as e:
        print(f"Error: Could not read credentials: {e}")
        return False

    driver = get_browser(portal_config)
    if not driver:
        return False

    try:
        return login(driver, username, password)
    finally:
        driver.quit()

if __name__ == "__main__":
    config = configparser.ConfigParser()
    config.read("config.ini")

    retries = config["captive_portal"].getint("retries", 3)
    delay = config["captive_portal"].getint("delay", 5)

    for attempt in range(retries):
        print(f"Attempt {attempt + 1} to login to captive portal.")
        if attempt_login(config):
            print("Successfully logged in.")
            break
        print(f"Login failed. Retrying in {delay} seconds...")
        time.sleep(delay)
    
    print("Failed to login after multiple attempts.")