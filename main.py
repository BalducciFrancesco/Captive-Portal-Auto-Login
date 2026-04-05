import logging as log
import sys
import time
from modules.check_connection import check_connection
from modules.find_captive_url import get_captive_url
from modules.init_browser import init_browser
from modules.run_login_sequence import run_login_sequence
from modules.settings import setup_log

def main():
    # %%
    setup_log()

    # %%
    log.info(f"----\nStep (1/4): Initializing loading of configuration file...")
    
    from modules.settings import conf
    
    log.info(f"Successfully loaded configuration file. {conf}")

    # %%
    log.info(f"\n----\nStep (2/4): Identifying captive portal URL ...")

    captive_url = get_captive_url()

    log.info(f"Successfully obtained captive URL.")
    log.info(f"Captive URL: {captive_url}")

    # %%
    log.info(f"\n----\nStep (3/4): Initializing browser and attaching to captive portal URL...")

    driver = init_browser(captive_url)

    log.info(f"Successfully initialized browser at captive portal URL.")
    log.info(f"Current URL in browser: {driver.current_url}")

    # %%
    log.info(f"\n----\nStep (4/4): Performing login sequence on captive portal...")

    driver = run_login_sequence(driver)
        
    log.info(f"Successfully executed the login sequence on the captive portal. Waiting 15s to check connection status...")
    time.sleep(15)

    # %%
    log.info(f"\n----\nStep (5/5): Checking connection...")

    if check_connection():
        log.info(f"Successfully logged in and bypassed the captive portal! Connection is now open. Have fun bro!")
        sys.exit(0)
    else:
        log.error(f"Unable to reach the internet after executing the login sequence. The captive portal is still blocking the connection.")
        log.error(f"I'm sorry but I tried my best. Hopefully there's still the sun and some fresh air outside.")
        log.error(f"Please check your configuration and retry later, or at least that's what we say in these cases")
        sys.exit(1)

# %%
if __name__ == "__main__":
    main()