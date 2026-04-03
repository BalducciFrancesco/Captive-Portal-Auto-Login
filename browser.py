import logging as log
import time
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.webdriver import WebDriver as ChromeDriver
from settings import Settings
import requests

def find_captive_url(settings: Settings) -> str:
	response = requests.get(settings.url, allow_redirects=False, timeout=settings.get_timeout)
	if 'Location' in response.headers:
		return response.headers['Location']
	else:
		raise Exception("No redirection detected from trigger URL, cannot determine captive portal URL.")

def get_browser(settings: Settings):
	"""Initialize driver and open the configured starting URL with retries."""
	service = Service(executable_path=settings.driver_path)
	options = Options()
	options.binary_location = settings.browser_path
	options.add_argument("--disable-chrome-captive-portal-detector")
	options.add_argument("--ignore-certificate-errors")
	options.add_argument("--ignore-ssl-errors=yes")
	options.add_argument("--allow-running-insecure-content")
	options.set_capability("acceptInsecureCerts", True)
	if settings.headless:
		options.add_argument("--headless")
		options.add_argument("--disable-gpu")
		options.add_argument("--no-sandbox")
		options.add_argument("--disable-dev-shm-usage")

	for attempt in range(settings.retries):
		try:
			log.info("Attempting to obtain captive URL...")
			captive_url = find_captive_url(settings)
			log.info(f"Found captive URL: {captive_url}")
			log.info(f"Attempt {attempt + 1}/{settings.retries} (timeout={settings.get_timeout}s, target={captive_url})")
			driver = ChromeDriver(service=service, options=options)
			driver.set_page_load_timeout(settings.get_timeout)
			driver.get(captive_url)
			return driver
		except Exception as e:
			if attempt < settings.retries - 1:
				log.warning(f"Failed to initialize or navigate with driver. Retrying in {settings.delay}s...")
				time.sleep(settings.delay)
			else:
				log.error(f"Unable to initialize or navigate with webdriver: {e}")

	return None
