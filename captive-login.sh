#!/bin/bash

set -e

# ============================================================================
# ----------------------- CUSTOMIZE THIS SECTION -----------------------------
# ============================================================================

# WiFi & Network
WIFI_SSID="YOUR_WIFI_SSID"                   # Your target WiFi network
HOTSPOT_SSID="Pi-Hotspot"                     # Fallback hotspot name
HOTSPOT_PASSWORD="raspberry"                  # Fallback hotspot password
WLAN_DEVICE="wlan1"                           # WiFi interface name

# Retry & Timing
RETRY_ATTEMPTS=3                              # Attempts before hotspot fallback
RETRY_DELAY=5                                 # Delay between retries (seconds)
LOGIN_TIMEOUT=30                              # Browser action timeout (seconds)
BROWSER_WAIT=2                                # Delay between actions (seconds)

# Browser & Paths
HEADLESS_MODE="true"                          # Set to false to show Firefox
TRIGGER_URL="http://neverssl.com"             # Captive portal trigger URL
SERVICE_NAME="captive-login"                  # systemd service name
VENV_PYTHON_PATH="$HOME/.venv/bin/python3"

# Login sequence - format: [{'action': 'click', 'selector': 'a'}, ... ]
# Supported actions: "click", "fill-username", "fill-password"
LOGIN_SEQUENCE="
[
  {'action': 'click', 'selector': 'a'},
  {'action': 'click', 'selector': '#cp-modal-button-member-simple'},
  {'action': 'fill-username', 'selector': 'input[name=\"UserId\"]'},
  {'action': 'fill-password', 'selector': 'input[name=\"Password\"]'},
  {'action': 'click', 'selector': 'input[type=\"submit\"]'},
  {'action': 'click', 'selector': 'input[type=\"submit\"]'}
]
"

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

USERNAME="${CAPTIVE_LOGIN_USERNAME:-}"
PASSWORD="${CAPTIVE_LOGIN_PASSWORD:-}"

login_sequence_needs_username() {
  grep -q "fill-username" <<< "$LOGIN_SEQUENCE"
}

prompt_credentials() {
  if login_sequence_needs_username && [ -z "${USERNAME:-}" ]; then
    read -r -p "Portal username: " USERNAME
  fi

  if [ -z "${PASSWORD:-}" ]; then
    read -r -s -p "Portal password: " PASSWORD
    echo
  fi
}

save_service_credentials() {
  sudo install -m 600 /dev/null /etc/captive-login.env
  printf 'CAPTIVE_LOGIN_USERNAME=%q\nCAPTIVE_LOGIN_PASSWORD=%q\n' "$USERNAME" "$PASSWORD" | sudo tee /etc/captive-login.env > /dev/null
}

log() {
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

log_error() {
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: $1" >&2
}

log_info() {
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] INFO: $1"
}

# ============================================================================
# PHASE 1: MAC ADDRESS RANDOMIZATION
# ============================================================================

randomize_mac() {
  log "=== PHASE 1: MAC Randomization ==="
  
  log "Generating random MAC address..."
  NEW_MAC=$(printf '%02x:%02x:%02x:%02x:%02x:%02x' $((RANDOM % 256)) $((RANDOM % 256)) $((RANDOM % 256)) $((RANDOM % 256)) $((RANDOM % 256)) $((RANDOM % 256)))
  
  log "Applying MAC address: $NEW_MAC to $WLAN_DEVICE"
  sudo ip link set dev "$WLAN_DEVICE" down || true
  sleep 1
  sudo ip link set dev "$WLAN_DEVICE" address "$NEW_MAC" || true
  sleep 1
  sudo ip link set dev "$WLAN_DEVICE" up || true
  
  log "✓ MAC address updated"
}

# ============================================================================
# PHASE 2: WIFI CONNECTION
# ============================================================================

connect_wifi() {
  log "=== PHASE 2: WiFi Connection ==="

  log "Connecting to WiFi: $WIFI_SSID..."
  
  # Rescan WiFi networks
  sudo nmcli device wifi rescan > /dev/null 2>&1 || true
  sleep 3
  
  # Check if already connected to target SSID
  CURRENT_SSID=$(sudo nmcli -t -f active,ssid dev wifi 2>/dev/null | grep -E "^yes" | awk -F: '{print $2}' | head -1 || echo "")
  
  if [ "$CURRENT_SSID" = "$WIFI_SSID" ]; then
    log "Already connected to $WIFI_SSID"
    return 0
  fi
  
  # Disconnect current connection
  sudo nmcli device disconnect "$WLAN_DEVICE" 2>/dev/null || true
  sleep 2
  
  # Connect to target WiFi
  sudo nmcli device wifi connect "$WIFI_SSID" 2>/dev/null || {
    log_error "Failed to connect to WiFi"
    return 1
  }
  
  # Wait for connection to establish
  for i in {1..15}; do
    if nmcli -t -f active,ssid dev wifi 2>/dev/null | grep -q "^yes:$WIFI_SSID"; then
      log "✓ WiFi connected"
      sleep 2
      return 0
    fi
    sleep 1
  done
  
  log_error "WiFi connection timeout"
  return 1
}

# ============================================================================
# PHASE 3: CAPTIVE PORTAL DETECTION
# ============================================================================

detect_captive_portal() {
  log "=== PHASE 3: Detecting Captive Portal ==="
  
  log "Querying $TRIGGER_URL for captive portal redirect..."
  
  # Query the trigger URL without following redirects
  RESPONSE=$(curl -s -i -L "$TRIGGER_URL" 2>/dev/null | head -20)
  
  # Check if there's a redirect (Location header indicates captive portal)
  REDIRECT_URL=$(echo "$RESPONSE" | grep -i "^Location:" | head -1 | cut -d' ' -f2 | tr -d '\r')
  
  if [ -z "$REDIRECT_URL" ]; then
    log "No redirect detected - no captive portal present"
    return 1
  fi
  
  # Clean up redirect URL
  REDIRECT_URL=$(echo "$REDIRECT_URL" | xargs)
  
  if [[ ! "$REDIRECT_URL" =~ ^https?:// ]]; then
    REDIRECT_URL="http://$REDIRECT_URL"
  fi
  
  log "✓ Captive portal detected"
  log "Portal URL: $REDIRECT_URL"
  
  echo "$REDIRECT_URL"
  return 0
}

# ============================================================================
# PHASE 4: CAPTIVE PORTAL INTERACTION
# ============================================================================

run_browser_login() {
  log "=== PHASE 4: Captive Portal Interaction ==="

  local portal_url="$1"
  log "Navigating to: $portal_url"
  
  # Escape credentials for Python
  local escaped_username=$(echo "$USERNAME" | sed "s/'/'\\\''/g")
  local escaped_password=$(echo "$PASSWORD" | sed "s/'/'\\\''/g")
  
  # Inline Python script for browser automation
  "$VENV_PYTHON_PATH" << PYTHON_EOF
    import sys
    import time
    import ast
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.firefox.options import Options as FirefoxOptions

    # Configuration
    portal_url = "$portal_url"
    username = "$escaped_username"
    password = "$escaped_password"
    timeout = $LOGIN_TIMEOUT
    browser_wait = $BROWSER_WAIT
    login_sequence = ast.literal_eval("""$LOGIN_SEQUENCE""")

    try:
        # Initialize Firefox in headless mode
        options = FirefoxOptions()
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--ignore-certificate-errors")
        options.set_capability("acceptInsecureCerts", True)
        
        if "$HEADLESS_MODE" == "true":
          options.add_argument("--headless")
        
        driver = webdriver.Firefox(options=options)
        driver.set_page_load_timeout(timeout)
        
        # Navigate to portal
        driver.get(portal_url)
        time.sleep(browser_wait)
        
        # Execute login sequence
        for idx, step in enumerate(login_sequence, 1):
            action = step.get("action", "")
            selector = step.get("selector", "")
            
            print(f"[Step {idx}/{len(login_sequence)}] {action} on '{selector}'")
            
            # Wait for element to be present and clickable
            try:
                element = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                )
                
                # Perform action
                if action == "click":
                    element.click()
                elif action == "fill-username":
                    element.send_keys(username)
                elif action == "fill-password":
                    element.send_keys(password)
                
                time.sleep(browser_wait)
            
            except Exception as e:
                print(f"Error on step {idx}: {e}", file=sys.stderr)
                driver.quit()
                sys.exit(1)
        
        print("✓ Login sequence completed")
        driver.quit()
        sys.exit(0)

    except Exception as e:
        print(f"Browser error: {e}", file=sys.stderr)
        sys.exit(1)
PYTHON_EOF
  
  return $?
}

# ============================================================================
# PHASE 5: CONNECTIVITY VERIFICATION
# ============================================================================

check_connectivity() {
  log "=== PHASE 5: Checking Internet Connectivity ==="
  
  log "Waiting 15s for connection to establish..."
  sleep 15
  
  if curl -s -I https://www.google.com -m 5 > /dev/null 2>&1; then
    log "✓ Internet connected!"
    return 0
  else
    log_error "Internet not reachable"
    return 1
  fi
}

# ============================================================================
# PHASE 5-bis: HOTSPOT FALLBACK
# ============================================================================

activate_hotspot() {
  log "=== PHASE 5-bis: Activating Hotspot Fallback ==="
  
  log_error "Login failed after $RETRY_ATTEMPTS attempts."
  log "Activating hotspot: $HOTSPOT_SSID"
  
  sudo nmcli device disconnect "$WLAN_DEVICE" 2>/dev/null || true
  sleep 2
  
  sudo nmcli device wifi hotspot ifname "$WLAN_DEVICE" ssid "$HOTSPOT_SSID" password "$HOTSPOT_PASSWORD" 2>/dev/null || {
    log_error "Failed to activate hotspot"
    return 1
  }
  
  log "✓ Hotspot activated: $HOTSPOT_SSID"
  log "Hotspot password: $HOTSPOT_PASSWORD"
  
  return 0
}

# ============================================================================
# MAIN FLOW WITH RETRY LOGIC
# ============================================================================

main() {
  prompt_credentials

  if login_sequence_needs_username && [ -z "${USERNAME:-}" ]; then
    log_error "Missing username"
    exit 1
  fi

  if [ -z "${PASSWORD:-}" ]; then
    log_error "Missing credentials"
    exit 1
  fi

  log "╔════════════════════════════════════════════════════════════╗"
  log "║  CAPTIVE PORTAL AUTO-LOGIN SCRIPT                          ║"
  log "║  $(date '+%Y-%m-%d %H:%M:%S')                          ║"
  log "╚════════════════════════════════════════════════════════════╝"
  
  # MAC randomization and WiFi connection
  randomize_mac
  connect_wifi || {
    log_error "WiFi connection failed"
    exit 1
  }
  
  # Detect captive portal
  PORTAL_URL=$(detect_captive_portal)
  if [ -z "$PORTAL_URL" ]; then
    log "No captive portal detected - internet is free!"
    exit 0
  fi
  
  # Login attempt with retry loop
  attempt=1
  while [ $attempt -le $RETRY_ATTEMPTS ]; do
    log "Login attempt $attempt/$RETRY_ATTEMPTS"
    
    if run_browser_login "$PORTAL_URL"; then
      log "Login sequence succeeded"
      
      if check_connectivity; then
        log "╔════════════════════════════════════════════════════════════╗"
        log "║  ✓ SUCCESS! Logged in and internet is connected.           ║"
        log "╚════════════════════════════════════════════════════════════╝"
        exit 0
      fi
    fi
    
    if [ $attempt -lt $RETRY_ATTEMPTS ]; then
      log "Retrying in ${RETRY_DELAY}s..."
      sleep "$RETRY_DELAY"
    fi
    
    ((attempt++))
  done
  
  # All retries failed - activate hotspot fallback
  activate_hotspot
  
  log "╔════════════════════════════════════════════════════════════╗"
  log "║  ✗ FAILED - Hotspot activated as fallback                  ║"
  log "║  Manual intervention may be required.                      ║"
  log "╚════════════════════════════════════════════════════════════╝"
  
  exit 1
}

# ============================================================================
# SYSTEMD SERVICE INSTALLATION (optional)
# ============================================================================

install_systemd_service() {
  log "Installing systemd service..."

  prompt_credentials

  if login_sequence_needs_username && [ -z "${USERNAME:-}" ]; then
    log_error "Missing username"
    exit 1
  fi

  if [ -z "${PASSWORD:-}" ]; then
    log_error "Missing credentials"
    exit 1
  fi

  save_service_credentials
  
  SCRIPT_PATH="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/$(basename "${BASH_SOURCE[0]}")"
  
  # Create systemd service file
sudo tee "/etc/systemd/system/${SERVICE_NAME}.service" > /dev/null << SYSTEMD
[Unit]
Description=Captive Portal Auto-Login
After=network-online.target
Wants=network-online.target

[Service]
Type=oneshot
WorkingDirectory=/tmp
EnvironmentFile=/etc/captive-login.env
ExecStart=/bin/bash $SCRIPT_PATH
RemainAfterExit=yes
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
SYSTEMD

  sudo systemctl daemon-reload
  sudo systemctl enable "${SERVICE_NAME}.service"
  
  log "✓ Service installed and enabled"
  log "To check status: sudo systemctl status ${SERVICE_NAME}.service"
  log "To view logs: sudo journalctl -u ${SERVICE_NAME}.service -f"
  log "Rebooting in 10 seconds..."
  
  sleep 10
  sudo reboot
}

# ============================================================================
# SCRIPT ENTRY POINT
# ============================================================================

# Trap errors and provide diagnostics
trap 'log_error "Script interrupted"; exit 130' INT TERM

# Run main flow
if [ "${BASH_SOURCE[0]}" = "${0}" ]; then
  if [ "$1" = "--install-service" ]; then
    INSTALL_SERVICE="true"
  elif [ -n "${1:-}" ]; then
    log_error "Unknown option: $1"
    exit 1
  fi

  if [ "${INSTALL_SERVICE:-}" = "true" ]; then
    install_systemd_service
  else
    main
  fi
fi
