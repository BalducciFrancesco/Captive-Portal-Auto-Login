import logging as log
import time
from pathlib import Path

from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.webdriver import WebDriver as ChromeDriver
from selenium import webdriver
from settings import Settings

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
			log.info(f"Attempt {attempt + 1}/{settings.retries} (timeout={settings.get_timeout}s, target={settings.url})")
			driver = ChromeDriver(service=service, options=options)
			driver.set_page_load_timeout(settings.get_timeout)
			driver.get(settings.url)
			return driver
		except (TimeoutException, WebDriverException) as e:
			if attempt < settings.retries - 1:
				log.warning(f"Failed to initialize or navigate with driver. Retrying in {settings.delay}s...")
				time.sleep(settings.delay)
			else:
				log.error(f"Unable to initialize or navigate with webdriver: {e}")

	return None
