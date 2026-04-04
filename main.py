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

setup_log()

# -----
# Load configuration
# -----

try:
    settings = Settings.from_file("config/config.toml")
except Exception as e:
    log.error(f"Unable to load configuration. Reason: {e}")
    sys.exit(1)

if __name__ == "__main__":
    pass