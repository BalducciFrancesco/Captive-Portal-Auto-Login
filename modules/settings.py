from dataclasses import dataclass
from pathlib import Path
import sys
import tomllib
import logging as log
from tenacity import RetryCallState


# -----
# Configuration setup
# -----

@dataclass(frozen=True)
class Configuration:
    url: str
    headless: bool
    browser_path: str
    driver_path: str
    retry_attempts: int
    retry_delay: int
    retry_timeout: int
    login_sequence: list[dict[str, str]]
    username: str | None
    password: str

    @classmethod
    def from_file(cls, config_file):
        config_path = Path(config_file)

        with open(config_path, "rb") as f:
            cfg = tomllib.load(f)

        # Main sections
        browser_setup = cfg["browser_setup"]
        retry = cfg["retry"]
        login = cfg["login"]

        # Load credentials from separate file
        credentials_path = (config_path.parent / Path(str(login.get("credentials_file", "credentials.txt")).strip())).resolve()
        credentials_lines = [line.strip() for line in credentials_path.read_text(encoding="utf-8").splitlines()]
        if not credentials_lines:
            raise ValueError(f"Password is empty. Please check your credentials file referenced from file {config_file}.")

        if len(credentials_lines) == 1:
            username = None
            password = credentials_lines[0]
        else:
            username = credentials_lines[0]
            password = credentials_lines[1]

        if not password:
            raise ValueError(f"Password is empty. Please check your credentials file referenced from file {config_file}.")

        settings = cls(
            url=str(browser_setup.get("captive_url") or browser_setup.get("fallback_trigger_url")).strip(),
            headless=bool(browser_setup["headless"]),
            browser_path=str(browser_setup["browser_path"]).strip(),
            driver_path=str(browser_setup["driver_path"]).strip(),
            retry_attempts=int(retry["attempts"]),
            retry_delay=int(retry["delay"]),
            retry_timeout=int(retry["timeout"]),
            login_sequence=list(login["sequence"]),
            username=username.strip() if username else None,
            password=password.strip(),
        )

        # Check for empty or missing fields
        empty_fields = []
        for name, value in settings.__dict__.items():
            if value is None:
                empty_fields.append(name)
            elif name != "username" and isinstance(value, str) and not value:
                empty_fields.append(name)
            elif isinstance(value, (list, dict, tuple, set)) and not value:
                empty_fields.append(name)
        if empty_fields:
            raise ValueError(f"Missing/empty fields inside configuration file \"{config_file}\": [{', '.join(empty_fields)}]. Please check out \"config/config_template.toml\" for the correct format.")
        if not settings.username and any(step.get("action") == "fill-username" for step in settings.login_sequence):
            raise ValueError(f"Configuration uses a fill-username step, but the credentials file referenced from file {config_file} does not provide a username.")

        return settings
    
    def __repr__(self):
        str = "Settings: ("
        for key, value in self.__dict__.items():
            if key == "login_sequence":
                str += f"\n\t{key}:"
                for seq in value:
                    str += f"\n\t\t{seq},"
            elif key == "password":
                str += f"\n\t{key}: {'***'},"
            else: 
                str += f"\n\t{key}: {value},"
        str += ")"
        return str

try: # Served globally
    conf = Configuration.from_file("config/config.toml")
except Exception as e:
    log.error(f"Unable to load configuration. Reason: {e}")
    sys.exit(1)

# -----
# Logging setup
# -----

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


# -----
# Retry setup
# -----

def log_attempt(retry_state: RetryCallState):
    log.info(f"Attempt {retry_state.attempt_number} out of {conf.retry_attempts}...")


def before_sleep(message: str):
    def _inner(retry_state: RetryCallState):
        reason = retry_state.outcome.exception() if retry_state.outcome else "unknown"
        log.warning(f"{message}. Reason: {reason}")
        log.info(f"Retrying in {conf.retry_delay}s...")
    return _inner

def give_up(message: str):
    def _inner(retry_state: RetryCallState):
        reason = retry_state.outcome.exception() if retry_state.outcome else "unknown"
        log.error(f"{message}. Reason: {reason}")
        sys.exit(1)
    return _inner