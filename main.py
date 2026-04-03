import configparser
import time
import logging as log
import sys
from pathlib import Path
from browser import get_browser
from portal import login

class ColorFormatter(log.Formatter):
    COLORS = {
        log.DEBUG: "\033[36m",
        log.INFO: "\033[94m",
        log.WARNING: "\033[93m",
        log.ERROR: "\033[91m",
        log.CRITICAL: "\033[95m",
    }
    RESET = "\033[0m"

    def format(self, record):
        color = self.COLORS.get(record.levelno, self.RESET)
        base = super().format(record)
        return f"{color}{base}{self.RESET}"

def setup_log():
    handler = log.StreamHandler(sys.stdout)
    handler.setFormatter(ColorFormatter("%(levelname)s: %(message)s"))
    log.basicConfig(level=log.INFO, handlers=[handler], force=True)

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
        log.error(f"Could not read credentials: {e}")
        return False

    driver = get_browser(portal_config)
    if not driver:
        return False

    try:
        return login(driver, username, password)
    finally:
        if driver:
            driver.quit()

if __name__ == "__main__":
    setup_log()
    config = configparser.ConfigParser()
    config.read("config.ini")

    retries = config["captive_portal"].getint("retries", 3)
    delay = config["captive_portal"].getint("delay", 5)

    for attempt in range(retries):
        log.info(f"Attempt {attempt + 1} to login to captive portal.")
        if attempt_login(config):
            log.info("Successfully logged in.")
            break
        log.warning(f"Login failed. Retrying in {delay} seconds...")
        time.sleep(delay)
    else:
        log.error("Failed to login after multiple attempts.")
