from dataclasses import dataclass
from pathlib import Path
import tomllib
import logging as log


@dataclass(frozen=True)
class Settings:
    url: str
    headless: bool
    browser_path: str
    driver_path: str
    retries: int
    delay: int
    get_timeout: int
    step_delay: float
    sequence: list[dict[str, str]]
    username: str
    password: str

    @classmethod
    def from_file(cls, config_file):
        config_path = Path(config_file)

        with open(config_path, "rb") as f:
            cfg = tomllib.load(f)

        # Main sections
        browser = cfg["browser"]
        login = cfg["login"]

        # Load credentials from separate file
        credentials_path = (config_path.parent / Path(str(login.get("credentials_file", "credentials.txt")).strip())).resolve()
        username, password = credentials_path.read_text(encoding="utf-8").strip().splitlines()
        if not username or not password:
            raise ValueError(f"Username or Password is empty. Please check your credentials file referenced from file {config_file}. It has to contain the username in the first line and the password in the second line.")

        settings = cls(
            url=str(browser.get("url") or browser.get("fallback_trigger_url") or "").strip(),
            headless=bool(browser["headless"]),
            browser_path=str(browser["browser_path"]).strip(),
            driver_path=str(browser["driver_path"]).strip(),
            retries=int(browser["retries"]),
            delay=int(browser["delay"]),
            get_timeout=int(browser["get_timeout"]),
            step_delay=float(login["step_delay"]),
            sequence=list(login["captive_sequence"]),
            username=username.strip(),
            password=password.strip(),
        )

        # Check for empty or missing fields
        empty_fields = []
        for name, value in settings.__dict__.items():
            if value is None:
                empty_fields.append(name)
            elif isinstance(value, str) and not value:
                empty_fields.append(name)
            elif isinstance(value, (list, dict, tuple, set)) and not value:
                empty_fields.append(name)

        if empty_fields:
            raise ValueError(f"Missing/empty fields inside configuration file \"{config_file}\": [{', '.join(empty_fields)}]. Please check out \"config/config_template.toml\" for the correct format.")

        return settings
