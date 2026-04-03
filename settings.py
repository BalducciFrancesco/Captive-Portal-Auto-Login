from dataclasses import dataclass
from pathlib import Path
import tomllib
import logging as log


@dataclass(frozen=True)
class Settings:
    url: str
    headless: bool
    chrome_path: str
    chromedriver_path: str
    retries: int
    delay: int
    get_timeout: int
    sequence: list[dict[str, str]]
    username: str
    password: str

    @classmethod
    def from_file(cls, config_file="config/config.toml"):
        config_path = Path(config_file)
        with open(config_path, "rb") as f:
            cfg = tomllib.load(f)

        browser = cfg["browser"]
        login = cfg["login"]

        try:
            credentials_path = (config_path.parent / Path(str(login.get("credentials_file", "credentials.txt")).strip())).resolve()
            username, password = credentials_path.read_text(encoding="utf-8").strip().splitlines()
        except (FileNotFoundError, ValueError) as e:
            log.error(f"Could not read credentials: {e}")
            username, password = "", ""

        return cls(
            url=str(browser.get("url", "")).strip() or str(browser.get("fallback_trigger_url", "")).strip(),
            headless=bool(browser.get("headless", False)),
            chrome_path=str(browser.get("chrome_path", "")).strip(),
            chromedriver_path=str(browser.get("chromedriver_path", "")).strip(),
            retries=int(browser.get("retries", 3)),
            delay=int(browser.get("delay", 5)),
            get_timeout=int(browser.get("get_timeout", 15)),
            sequence=list(login.get("captive_sequence", login.get("sequence", []))),
            username=username,
            password=password,
        )
