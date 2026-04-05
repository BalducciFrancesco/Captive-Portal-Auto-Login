import requests
from modules.settings import conf


def check_connection() -> bool:
    try:
        response = requests.get("https://google.com", allow_redirects=False, timeout=conf.retry_timeout)
        if response.status_code == 200:
            return True
    except Exception:
        return False
    return False