import logging as log
from pathlib import Path
from browser import get_browser
from portal import login
from settings import Settings
import logging as log
import sys

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
    log.info(f"Startup mode={settings.mode} timeout={settings.get_timeout}s url={settings.target_url}")

    try:
        credentials_path = Path(settings.credentials_file)
        username, password = credentials_path.read_text(encoding="utf-8").strip().splitlines()
    except (KeyError, FileNotFoundError, ValueError) as e:
        log.error(f"Could not read credentials: {e}")
    else:
        driver = get_browser(settings)
        if driver:
            try:
                login(driver, username, password)
                log.info("Successfully logged in.")
            finally:
                driver.quit()
                log.error("Login failed.")