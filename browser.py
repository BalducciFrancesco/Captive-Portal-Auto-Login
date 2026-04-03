import logging as log
import time
from pathlib import Path

from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.webdriver import WebDriver as ChromeDriver
from settings import Settings

def get_browser(settings: Settings):
	"""Initialize driver and open the configured starting URL with retries."""
	options = Options()
	if settings.headless:
		options.add_argument("--headless")
		options.add_argument("--disable-gpu")
		options.add_argument("--no-sandbox")
		options.add_argument("--disable-dev-shm-usage")

	if chrome_path := settings.chrome_path:
		options.binary_location = chrome_path

	service = None
	if chromedriver_path := settings.chromedriver_path:
		if Path(chromedriver_path).is_file():
			service = Service(executable_path=chromedriver_path)
		else:
			log.warning(f"chromedriver_path not found, using Selenium default resolution: {chromedriver_path}")

	timeout = settings.get_timeout
	target_url = settings.target_url

	if not target_url:
		log.error("No URL configured. Set url or fallback_trigger_url in config.toml")
		return None

	log.info(f"Mode={settings.mode} timeout={timeout}s target={target_url} retries={settings.retries}")

	for attempt in range(settings.retries):
		log.info(f"Browser attempt {attempt + 1}/{settings.retries}")
		driver = None
		try:
			driver = ChromeDriver(service=service, options=options) if service else ChromeDriver(options=options)
			driver.set_page_load_timeout(timeout)

			try:
				driver.get(target_url)
			except TimeoutException:
				log.error(f"Navigation timeout after {timeout}s while opening: {target_url}")
				driver.quit()
				driver = None

			if driver:
				log.info(f"Starting page opened: {driver.current_url}")
				return driver
		except WebDriverException as e:
			log.error(f"Failed to initialize or navigate with Chrome driver: {e}")
			if driver:
				driver.quit()

		if attempt < settings.retries - 1:
			log.warning(f"Retrying browser setup in {settings.delay}s...")
			time.sleep(settings.delay)

	return None
