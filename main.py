import logging as log
import sys
from settings import Settings
import requests
import time
import logging as log
import time
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.webdriver import WebDriver as ChromeDriver
from settings import Settings
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
import requests

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

log.info(f"----\nStep (1/4): Initializing loading of configuration file...")

try:
    settings = Settings.from_file("config/config.toml")
except Exception as e:
    log.error(f"Unable to load configuration. Reason: {e}")
    sys.exit(1)

log.info(f"Successfully loaded configuration file. {settings}")

# -----
# Identify captive portal URL
# -----

log.info(f"\n----\nStep (2/4): Identifying captive portal URL ...")

captive_url = None
for attempt in range(settings.retries):
    log.info(f"Attempt {attempt + 1} out of {settings.retries}...")
    try:
        response = requests.get(settings.url, allow_redirects=False, timeout=settings.get_timeout)
        if 'Location' in response.headers:
            captive_url = response.headers['Location']
            break
    except Exception as e:
        log.warning(f"Failed attempt to get captive URL from trigger URL {settings.url}. Retrying in {settings.delay}s... Reason: {e}")
        time.sleep(settings.delay)
        continue

if(attempt == settings.retries - 1 and not captive_url):
    log.error(f"Unable to obtain captive URL after {settings.retries} attempts. Please check your network connection and the trigger URL in your configuration file.")
    sys.exit(1)

log.info(f"Successfully obtained captive URL.")
log.info(f"Captive URL: {captive_url}")

# -----
# Initialize browser and attach to portal URL
# -----

log.info(f"\n----\nStep (3/4): Initializing browser and attaching to captive portal URL...")

driver = None
for attempt in range(settings.retries):
    log.info(f"Attempt {attempt + 1} out of {settings.retries}...")

    options = Options()
    options.binary_location = settings.browser_path
    options.add_argument("--disable-chrome-captive-portal-detector")
    options.add_argument("--ignore-certificate-errors")
    options.add_argument("--ignore-ssl-errors=yes")
    options.add_argument("--allow-running-insecure-content")
    options.set_capability("acceptInsecureCerts", True)
    service = Service(executable_path=settings.driver_path)

    if settings.headless:
        options.add_argument("--headless")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")

    try:
        driver = ChromeDriver(service=service, options=options)
        driver.set_page_load_timeout(settings.get_timeout)
        driver.get(captive_url) # type: ignore
        break
    except Exception as e:
        log.warning(f"Failed attempt to initialize browser and navigate to captive URL {captive_url}. Retrying in {settings.delay}s... Reason: {e}")
        time.sleep(settings.delay)
        continue

if(attempt == settings.retries - 1 and not driver):
    log.error(f"Unable to initialize browser and navigate to captive URL after {settings.retries} attempts. Please check your browser and driver paths in the configuration file, as well as your network connection.")
    sys.exit(1)

log.info(f"Successfully initialized browser at captive portal URL.")
log.info(f"Current URL in browser: {driver.current_url}") # type: ignore

# -----
# Interactively navigate the captive portal and perform login
# -----

log.info(f"\n----\nStep (4/4): Performing login sequence on captive portal...")

for attempt in range(settings.retries):
    log.info(f"Attempt {attempt + 1} out of {settings.retries}...")

    for index, step in enumerate(settings.sequence, start=1):
        action = step.get("action", "")
        selector = step.get("selector", "")
        log.info(f"Executing sequence step #{index} out of {len(settings.sequence)}: '{action}' on selector '{selector}'")

        try: # Wait for DOM ready state
            WebDriverWait(driver, settings.get_timeout).until(lambda d: d.execute_script("return document.readyState") == "complete")   # type: ignore
        except TimeoutException:
            log.warning(f"Document was not ready within the timeout of {settings.get_timeout}s for step #{index}. Retrying the whole sequence from the start in {settings.delay}s...")
            time.sleep(settings.delay)
            continue

        try: # Attempt locating the element
            element = driver.find_element(By.CSS_SELECTOR, selector) # type: ignore
        except Exception as e:
            log.warning(f"Failed to find element for step #{index} with selector '{selector}'. Retrying the whole sequence from the start in {settings.delay}s... Reason: {e}")
            time.sleep(settings.delay)
            continue
        
        try: # Perform the specified action on the element
            if action == "click":
                element.click()
            elif action == "fill-username":
                element.send_keys(settings.username)
            elif action == "fill-password":
                element.send_keys(settings.password)
        except Exception as e:
            log.warning(f"Failed to perform action '{action}' on element for step #{index}. Retrying the whole sequence from the start in {settings.delay}s... Reason: {e}")
            time.sleep(settings.delay)
            continue

    # All actions executed
    break
    
log.info(f"Successfully executed the login sequence on the captive portal. Waiting 15s to check connection status...")
time.sleep(15)

# -----
# Check final connection 
# -----

try:
    response = requests.get("https://google.com", allow_redirects=False, timeout=settings.get_timeout)
    if response.status_code == 200:
        log.info(f"Successfully logged in and bypassed the captive portal! Connection is now open. Have fun bro!")
        sys.exit(0)
except Exception as e:
    pass

log.error(f"Unable to reach the internet after executing the login sequence. The captive portal is still blocking the connection. \
            I'm sorry but I tried my best. Hopefully there's still the sun and some fresh air outside. \
            Please check your configuration retry later, or at least that's what we say in these cases")
sys.exit(1)

# -----

if __name__ == "__main__":
    pass