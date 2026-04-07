# Captive Portal Auto-Login

A Python tool that automatically detects and logs into captive portals (e.g. hotel Wi-Fi, airport Wi-Fi, university networks) using a configurable browser automation sequence powered by [Selenium](https://www.selenium.dev/).

> A more stable and shell-friendly alternative has been developed in the branch [shell-version](https://github.com/BalducciFrancesco/Captive-Portal-Auto-Login/tree/shell-version). Make sure to check it out!

## Features

- Supports **Chrome/Chromium** and **Firefox**
- Runs the browser in **headless mode** by default (no GUI required)
- **Configurable login sequence**: click buttons, fill username/password fields — all driven by CSS selectors
- **Automatic retries** with configurable attempts, delay, and timeout
- Optional **auto-install** of the matching WebDriver binary

## Requirements

- Python 3.11+
- Chrome/Chromium or Firefox installed on the system
- Matching WebDriver (chromedriver / geckodriver) — see [Setup](#setup)

Install Python dependencies:

```bash
pip install -r requirements.txt
```

## Setup

### 1. Create the configuration file

Copy the template and edit it:

```bash
cp config/config_template.toml config/config.toml
```

Edit `config/config.toml` (see [Configuration reference](#configuration-reference) below).

### 2. Create the credentials file

Create a plain-text file with your credentials (path is set in `config.toml`, default `./credentials.txt`):

- **Username + password** (two lines):
  ```
  your_username
  your_password
  ```
- **Password only** (one line, for portals that only ask for a password):
  ```
  your_password
  ```

> The credentials file is excluded from version control via `.gitignore`.

### 3. Install the WebDriver (optional)

If you don't already have a matching WebDriver on your system, run the autoinstaller:

```bash
pip install chromedriver-autoinstaller && python -c "import chromedriver_autoinstaller; print(chromedriver_autoinstaller.install())" 
```

or

```bash
pip install geckodriver-autoinstaller && python -c "import geckodriver_autoinstaller; print(geckodriver_autoinstaller.install())"
```

This will download the correct WebDriver binary for your installed browser version and print the path to it. You can then set `driver_path` in your `config.toml` to that path.

Alternatively, you can set `driver_path` to an existing binary in your config, or omit it entirely to let Selenium resolve/download it at runtime.

## Usage

```bash
python main.py
```

The script will:
1. Load `config/config.toml`
2. Detect the captive portal URL (via HTTP redirect from a trigger URL)
3. Open the browser and navigate to the captive portal
4. Execute the configured login sequence (clicks, form fills)
5. Wait 15 seconds and verify internet connectivity

Exit code `0` means success; exit code `1` means the login sequence failed or connectivity could not be confirmed.

## Configuration reference

`config/config.toml` (based on `config/config_template.toml`):

```toml
[browser_setup]
captive_url = ""                              # (Optional) Direct URL of the captive portal login page
fallback_trigger_url = "http://neverssl.com"  # URL used to trigger captive portal redirection when captive_url is not set
headless = true                               # Run browser without a GUI
chrome_path = "/usr/bin/chrome"               # Path to Chrome/Chromium binary (use this OR firefox_path)
# firefox_path = "/Applications/Firefox.app/Contents/MacOS/firefox"  # Path to Firefox binary
driver_path = "/usr/bin/chromedriver"         # (Optional) Path to the WebDriver binary

[retry]
attempts = 3      # Number of retry attempts for each step
delay = 5         # Seconds to wait between retries
timeout = 15      # Seconds before a request or page-load times out

[login]
credentials_file = "./credentials.txt"        # Path to the credentials file (relative to config.toml)
sequence = [                                  # Ordered list of browser actions to perform
  { action = "click",         selector = "a" },
  { action = "click",         selector = "#cp-modal-button-member-simple" },
  { action = "fill-username", selector = "input:nth-of-type(1)" },
  { action = "fill-password", selector = "input:nth-of-type(2)" },
  { action = "click",         selector = "button[type=\"submit\"]" },
]
```

### Login sequence actions

| Action          | Description                                      |
|-----------------|--------------------------------------------------|
| `click`         | Click the element matching `selector`            |
| `fill-username` | Type the username into the element               |
| `fill-password` | Type the password into the element               |

All selectors use standard [CSS selector](https://developer.mozilla.org/en-US/docs/Web/CSS/CSS_selectors) syntax.

## Project structure

```
.
├── config/
│   └── config_template.toml   # Configuration template
├── driver/                    # WebDriver binaries (git-ignored, populated by install-driver.py)
├── modules/
│   ├── check_connection.py    # Verifies internet access after login
│   ├── find_captive_url.py    # Resolves the captive portal URL via HTTP redirect
│   ├── init_browser.py        # Initialises the Selenium WebDriver
│   ├── run_login_sequence.py  # Executes the configured login sequence
│   └── settings.py            # Loads and validates config; logging and retry helpers
├── install-driver.py          # Helper script to download the matching WebDriver
├── main.py                    # Entry point
└── requirements.txt
```

## License

This project is open source. See the repository for license details.
