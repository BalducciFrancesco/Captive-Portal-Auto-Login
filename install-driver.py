from pathlib import Path
import importlib
import sys
import tomllib
import subprocess


CONFIG_PATH = Path("config/config.toml")
DRIVER_DIR = Path("driver")


def main():
	with CONFIG_PATH.open("rb") as f:
		browser_setup = tomllib.load(f)["browser_setup"]

	DRIVER_DIR.mkdir(parents=True, exist_ok=True)

	if browser_setup.get("chrome_path"):
		subprocess.run([sys.executable, "-m", "pip", "install", "chromedriver-autoinstaller"], check=True)
		importlib.import_module("chromedriver_autoinstaller").install(path=str(DRIVER_DIR))
	elif browser_setup.get("firefox_path"):
		subprocess.run([sys.executable, "-m", "pip", "install", "geckodriver-autoinstaller"], check=True)
		importlib.import_module("geckodriver_autoinstaller").install(path=str(DRIVER_DIR))
	else:
		print("No valid browser path provided in configuration. Please specify either 'chrome_path' or 'firefox_path' in the config.toml file.")
		sys.exit(1)

if __name__ == "__main__":
	main()
