from dataclasses import dataclass
from pathlib import Path
import tomllib


@dataclass(frozen=True)
class Settings:
    credentials_file: str
    url: str
    fallback_trigger_url: str
    headless: bool
    chrome_path: str
    chromedriver_path: str
    retries: int
    delay: int
    get_timeout: int

    @property
    def mode(self):
        return "direct-url" if self.url else "fallback-trigger"

    @property
    def target_url(self):
        return self.url or self.fallback_trigger_url

    @classmethod
    def from_file(cls, config_file="config/config.toml"):
        config_path = Path(config_file)
        with open(config_path, "rb") as f:
            cfg = tomllib.load(f)["captive_portal"]

        credentials_file = str(cfg.get("credentials_file", "credentials.txt")).strip()
        credentials_path = Path(credentials_file)
        if not credentials_path.is_absolute():
            credentials_file = str((config_path.parent / credentials_path).resolve())

        return cls(
            credentials_file=credentials_file,
            url=str(cfg.get("url", "")).strip(),
            fallback_trigger_url=str(cfg.get("fallback_trigger_url", "")).strip(),
            headless=bool(cfg.get("headless", False)),
            chrome_path=str(cfg.get("chrome_path", "")).strip(),
            chromedriver_path=str(cfg.get("chromedriver_path", "")).strip(),
            retries=int(cfg.get("retries", 3)),
            delay=int(cfg.get("delay", 5)),
            get_timeout=int(cfg.get("get_timeout", 15)),
        )
