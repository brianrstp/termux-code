"""
Gmail Creator - Configuration
Optimized for Termux (Android) environment.
Uses Playwright + Chromium instead of Chromax.
"""
import os
import json
from pathlib import Path

# ==============================
# PATHS (Termux-compatible)
# ==============================
HOME_DIR = Path.home()
DATA_DIR = HOME_DIR / ".gmail_creator"
ACCOUNTS_FILE = DATA_DIR / "accounts.json"
PROFILES_DIR = DATA_DIR / "profiles"

# Create directories on import
DATA_DIR.mkdir(parents=True, exist_ok=True)
PROFILES_DIR.mkdir(parents=True, exist_ok=True)

# ==============================
# BROWSER SETTINGS (Termux)
# ==============================
# Playwright Chromium paths in Termux
CHROMIUM_EXECUTABLE = None  # Let playwright find it

# Browser launch args for stealth
STEALTH_ARGS = [
    "--disable-blink-features=AutomationControlled",
    "--disable-features=IsolateOrigins,site-per-process",
    "--disable-site-isolation-trials",
    "--no-sandbox",
    "--disable-setuid-sandbox",
    "--disable-dev-shm-usage",
    "--disable-accelerated-2d-canvas",
    "--no-first-run",
    "--no-zygote",
    "--disable-gpu",
    "--disable-web-security",
    "--disable-features=VizDisplayCompositor",
    "--window-size=1366,768",
    "--lang=en-US",
]

# Headless mode (set False if using VNC/X11)
HEADLESS = True

# Viewport size
VIEWPORT = {"width": 1366, "height": 768}

# User agent
USER_AGENT = (
    "Mozilla/5.0 (Linux; Android 13; SM-G991B) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Mobile Safari/537.36"
)

# Mobile user agent (for mobile emulation)
MOBILE_USER_AGENT = (
    "Mozilla/5.0 (Linux; Android 13; SM-G991B) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Mobile Safari/537.36"
)

# ==============================
# SMS VERIFICATION
# ==============================
# Supported providers: "sms_activate", "five_sim", "manual"
SMS_PROVIDER = "manual"

# SMS-Activate API
SMS_ACTIVATE_API_KEY = os.environ.get("SMS_ACTIVATE_API_KEY", "")

# 5sim.net API
FIVE_SIM_API_KEY = os.environ.get("FIVE_SIM_API_KEY", "")

# ==============================
# PROXY SETTINGS
# ==============================
# Format: "protocol://user:pass@host:port" or None
PROXY = os.environ.get("PROXY", None)

# ==============================
# TIMING SETTINGS (Human-like behavior)
# ==============================
TYPING_MIN_DELAY = 50   # ms
TYPING_MAX_DELAY = 150  # ms
TYPING_ERROR_RATE = 0.04  # 4% chance of typo

# Delay between steps (seconds) — longer = less likely to trigger verification
STEP_DELAY_MIN = 2.0
STEP_DELAY_MAX = 5.0

# Page load wait timeout (ms)
PAGE_LOAD_TIMEOUT = 30000

# Max retries for verification
MAX_VERIFICATION_RETRIES = 5

# ==============================
# ACCOUNT FINGERPRINT PROFILES
# ==============================
def get_profile(index: int) -> dict:
    """Generate a fingerprint profile based on index."""
    profiles = [
        {
            "name": "Pixel7",
            "user_agent": "Mozilla/5.0 (Linux; Android 14; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
            "viewport": {"width": 412, "height": 915},
            "locale": "en-US",
            "timezone": "America/New_York",
        },
        {
            "name": "GalaxyS23",
            "user_agent": "Mozilla/5.0 (Linux; Android 13; SM-S911B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
            "viewport": {"width": 360, "height": 780},
            "locale": "en-US",
            "timezone": "America/Chicago",
        },
        {
            "name": "OnePlus11",
            "user_agent": "Mozilla/5.0 (Linux; Android 13; CPH2451) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
            "viewport": {"width": 412, "height": 915},
            "locale": "en-US",
            "timezone": "America/Los_Angeles",
        },
        {
            "name": "Xiaomi13",
            "user_agent": "Mozilla/5.0 (Linux; Android 13; 2211133G) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
            "viewport": {"width": 393, "height": 851},
            "locale": "en-GB",
            "timezone": "Europe/London",
        },
        {
            "name": "Desktop",
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "viewport": {"width": 1920, "height": 1080},
            "locale": "en-US",
            "timezone": "America/New_York",
        },
    ]
    return profiles[index % len(profiles)]


# ==============================
# ACCOUNT STORAGE
# ==============================
def save_account(email: str, password: str, recovery_email: str = "",
                 phone: str = "", profile_name: str = ""):
    """Save created account to local storage."""
    accounts = load_accounts()
    accounts.append({
        "email": email,
        "password": password,
        "recovery_email": recovery_email,
        "phone": phone,
        "profile": profile_name,
        "created_at": __import__("datetime").datetime.now().isoformat(),
    })
    ACCOUNTS_FILE.write_text(json.dumps(accounts, indent=2, ensure_ascii=False))


def load_accounts() -> list:
    """Load all saved accounts."""
    if ACCOUNTS_FILE.exists():
        return json.loads(ACCOUNTS_FILE.read_text())
    return []


def get_account_count() -> int:
    """Get total number of saved accounts."""
    return len(load_accounts())
