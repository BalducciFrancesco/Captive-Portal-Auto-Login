# Captive Portal Auto-Login

Simple, fast bash script that automatically logs into captive portals (airport WiFi, hotel WiFi, university networks) on Raspberry Pi or any Linux system.

## Features

- [x] Single bash script
- [x] Auto-installs dependencies (python3, firefox, selenium)
- [x] Randomizes MAC address before WiFi connection
- [x] Automatically detects captive portal via `neverssl.com` redirect
- [x] Automatically uses Firefox through Selenium (click, fill forms, submit)
- [x] Retry logic (3 attempts, 5s delay between retries)
- [x] Falls back to hotspot creation if login fails
- [x] Auto-runs at startup (if systemd service installed)

## How to find portal login selectors

You need to customize the `LOGIN_SEQUENCE` property with the correct CSS selectors sequence for your specific captive portal. In order to find them, you want to inspect the portal manually:
1. Connect to WiFi without the script
2. Open a browser and access the portal login page
3. Right-click → Inspect Element
4. Take note of the [CSS selectors](https://developer.mozilla.org/en-US/docs/Web/CSS/CSS_Selectors) for the exact step you would perform manually:
    - Button IDs/classes for clicks: `button#login`, `a.accept-tos`, etc.
    - Input field names for credentials: `input[name="UserId"]`, `input#password`, etc.
5. Update `LOGIN_SEQUENCE` with the correct selectors

## Usage

### Step 1: Install dependencies

```bash
sudo apt-get update
sudo apt-get install -y python3 python3-pip python3-venv firefox-esr network-manager
python3 -m venv .venv
source .venv/bin/activate
pip install selenium
```

### Step 2: Download the script

```bash
mkdir -p ~/bin
wget -O ~/bin/captive-login.sh https://raw.githubusercontent.com/BalducciFrancesco/Captive-Portal-Auto-Login/shell-version/captive-login.sh
```

### Step 3: Configure the script

```bash
nano ~/bin/captive-login.sh
```
Here you want to edit the configuration section at the top of the script. Set your WiFi SSID and update the `LOGIN_SEQUENCE` with the correct CSS selectors for your captive portal.

#### Required configuration options
```bash
WIFI_SSID="YOUR_WIFI_SSID"              # Your target WiFi network

LOGIN_SEQUENCE=(...)                    # Your specific steps for the captive portal login (see below)
```

#### Optional configuration options
```bash
HOTSPOT_SSID="Pi-Hotspot"               # Fallback hotspot name
HOTSPOT_PASSWORD="raspberry"            # Fallback hotspot password
WLAN_DEVICE="wlan1"                     # WiFi interface name

RETRY_ATTEMPTS=3                         # Attempts before hotspot fallback
RETRY_DELAY=5                            # Delay between retries (seconds)
LOGIN_TIMEOUT=30                         # Browser action timeout (seconds)
BROWSER_WAIT=2                           # Delay between actions (seconds)

HEADLESS_MODE="true"                     # Set to false to show Firefox
TRIGGER_URL="http://neverssl.com"        # Captive portal trigger URL
SERVICE_NAME="captive-login"             # systemd service name
```



### Step 4: Run the script
```bash
chmod +x ~/bin/captive-login.sh
~/bin/captive-login.sh
```

The script will prompt for the username and password for the captive portal at runtime. It will then attempt to connect to the specified WiFi network, detect the captive portal, and execute the login sequence using Firefox and Selenium. If `HEADLESS_MODE` is set to `false`, Firefox opens visibly. If it fails after the specified number of attempts, it will create a fallback hotspot.


## (Optional) Installation as service (autorun)

Instead of running the script manually, you can set it up to run automatically at startup using a systemd service. This is especially useful for Raspberry Pi devices that need to connect to captive portals without user intervention and without a monitor/keyboard attached.

Just replace [step 4](#step-4-run-the-script) with the following command:
```bash
./captive-login.sh --install-service
```

This will:
1. Create a service `/etc/systemd/system/captive-login.service`
2. Save the portal username and password in `/etc/captive-login.env` with root-only permissions
3. Enable automatic run of the script at boot
4. Reboot the system


## Troubleshooting

Due to the nature of captive portals and the wide variety of implementations, you will ~~probably~~ encounter issues during setup or execution. Here are some common issues and how to diagnose/resolve them:

| Issue | Diagnosis | Solution |
|-------|-----------|----------|
| "No captive portal detected" | WiFi may already be open or no internet | Run `curl -i http://neverssl.com` to verify; check WiFi connection with `nmcli device wifi list` |
| "Login sequence failed" | CSS selectors don't match your portal's HTML | Revisit the portal's HTML inspector and update `LOGIN_SEQUENCE` with correct selectors |
| "Internet not reachable after login" | Login executed but portal didn't authenticate | Verify credentials are correct; portal may require additional steps (e.g., accept ToS) |
| "WiFi connection failed" | SSID name may be wrong or network out of range | Check SSID spelling in config; ensure WiFi is in range; verify with `nmcli device wifi list` |
| "Firefox not found" | Browser not installed | Run: `sudo apt-get install firefox-esr` |
| "Selenium import error" | Python module not available | Run in a venv: `python3 -m venv .venv && source .venv/bin/activate && pip install selenium` |

Here are some specific commands to help you debug:

### View service status quickly
```bash
sudo systemctl status captive-login.service
```
It should return `active (running)`. If it shows `failed` or `inactive`, check the logs for errors.

### View service logs in real-time
```bash
sudo journalctl -u captive-login.service -f
```
It should return the live output of the script, including any errors or debug messages. Look for lines indicating:
- WiFi connection attempts
- Captive portal detection results
- Login sequence execution
- Hotspot fallback activation

### Manual checks
```bash
# Restart service
sudo systemctl restart captive-login.service

# Disable auto-run
sudo systemctl disable captive-login.service

# Test captive portal detection
curl -i http://neverssl.com

# Check available WiFi networks
nmcli device wifi list

# Verify internet connectivity
curl -I https://www.google.com

# Remove everything
sudo systemctl disable captive-login.service
sudo rm /etc/systemd/system/captive-login.service
sudo systemctl daemon-reload
rm ~/bin/captive-login.sh
```

## Security Notes

Credentials are not stored in the script. Manual runs prompt for them at runtime, and service installs save them once in `/etc/captive-login.env` with root-only permissions so systemd can load them at boot.