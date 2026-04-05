import requests
from tenacity import retry, stop_after_attempt, wait_fixed
from modules.settings import before_sleep, give_up, log_attempt
from modules.settings import conf

@retry(
    stop=stop_after_attempt(conf.retries),
    wait=wait_fixed(conf.delay),
    reraise=True,
    before=log_attempt,
    before_sleep=before_sleep(f"Failed attempt to get captive URL from trigger URL {conf.url}"),
    retry_error_callback=give_up(f"Unable to obtain captive URL. Please check your network connection and the trigger URL in your configuration file.")
)
def get_captive_url() -> str:
    response = requests.get(conf.url, allow_redirects=False, timeout=conf.get_timeout)
    if "Location" not in response.headers:
        raise RuntimeError("Missing 'Location' header in response")
    return response.headers["Location"]