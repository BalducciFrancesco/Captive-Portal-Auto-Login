import logging as log
import sys
from pathlib import Path
from browser import get_browser
from portal import login
from settings import Settings
import time

def setup_log():
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
    handler = log.StreamHandler(sys.stdout)
    handler.setFormatter(ColorFormatter("%(levelname)s: %(message)s"))
    log.basicConfig(level=log.INFO, handlers=[handler], force=True)


if __name__ == "__main__":
    setup_log()
    settings = Settings.from_file("config/config.toml")
    success = False

    log.info("Initializing browser...")
    driver = get_browser(settings)
    time.sleep(5)  # debugging

    if driver:
        try:
            log.info(f"Successfully connected through browser at starting page: {driver.current_url}")
            log.info("Initializing login process...")
            success = login(driver, settings)
        finally:
            driver.quit()

    if success:
        log.info("Auto Login successful. Enjoy your internet connection!")
    else:
        log.error("Auto Login failed. I tried my best but I couldn't get you connected. Hopefully there's the sun outside, go out and enjoy it anyway!")