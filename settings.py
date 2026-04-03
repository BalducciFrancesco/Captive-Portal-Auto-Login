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
    username: str
    password: str

    @classmethod
    def from_file(cls, config_file="config/config.toml"):
        config_path = Path(config_file)
        with open(config_path, "rb") as f:
            cfg = tomllib.load(f)["captive_portal"]

        credentials_file = str(cfg.get("credentials_file", "credentials.txt")).strip()
        credentials_path = Path(credentials_file)
        if not credentials_path.is_absolute():
            credentials_file = str((config_path.parent / credentials_path).resolve())

        username, password = "", ""
        try:
            credentials_path = Path(credentials_file)
            username, password = credentials_path.read_text(encoding="utf-8").strip().splitlines()
        except (KeyError, FileNotFoundError, ValueError) as e:
            log.error(f"Could not read credentials: {e}")

        return cls(
            url=str(cfg.get("url", "")).strip() or str(cfg.get("fallback_trigger_url", "")).strip(),
            headless=bool(cfg.get("headless", False)),
            chrome_path=str(cfg.get("chrome_path", "")).strip(),
            chromedriver_path=str(cfg.get("chromedriver_path", "")).strip(),
            retries=int(cfg.get("retries", 3)),
            delay=int(cfg.get("delay", 5)),
            get_timeout=int(cfg.get("get_timeout", 15)),
            username=username,
            password=password,
        )
