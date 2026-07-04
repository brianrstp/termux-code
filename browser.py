"""
Gmail Creator - Browser Module
Selenium-based browser with stealth features for Termux/Android.
Includes pre-launch diagnostics to catch chromium issues early.
"""
import os
import random
import subprocess
import time
import shutil
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from config import (
    HEADLESS, VIEWPORT, USER_AGENT,
    TYPING_MIN_DELAY, TYPING_MAX_DELAY, TYPING_ERROR_RATE,
)

TERMUX_BIN = "/data/data/com.termux/files/usr/bin"


def _find_binary(names: list, extra_paths: list = None) -> str:
    """Find first existing + executable binary from candidates."""
    candidates = []
    for name in names:
        which = shutil.which(name)
        if which:
            candidates.append(which)
    for p in (extra_paths or []):
        candidates.append(p)
    for p in candidates:
        if os.path.isfile(p) and os.access(p, os.X_OK):
            return p
    return ""


def _find_chromium() -> str:
    """Find chromium binary."""
    return _find_binary(
        ["chromium", "chromium-browser"],
        [f"{TERMUX_BIN}/chromium", "/usr/bin/chromium"],
    )


def _find_chromedriver() -> str:
    """Find chromedriver binary."""
    return _find_binary(
        ["chromedriver"],
        [f"{TERMUX_BIN}/chromedriver", "/usr/bin/chromedriver"],
    )


def _diagnose_chromium(chromium_path: str):
    """Run pre-launch checks to verify chromium works on this system."""
    print(f"🔍 Diagnosing chromium: {chromium_path}")

    # 1. Version check
    try:
        result = subprocess.run(
            [chromium_path, "--version"],
            capture_output=True, text=True, timeout=10,
        )
        version = result.stdout.strip() or result.stderr.strip()
        if result.returncode == 0 and version:
            print(f"   ✅ Version: {version}")
        else:
            print(f"   ⚠️  --version returned code {result.returncode}")
            print(f"   stdout: {result.stdout.strip()[:200]}")
            print(f"   stderr: {result.stderr.strip()[:200]}")
    except subprocess.TimeoutExpired:
        print("   ⚠️  --version timed out (10s) — binary may be broken")
    except FileNotFoundError:
        print("   ❌ Binary not found or not executable")
    except Exception as e:
        print(f"   ❌ Error: {e}")

    # 2. Shared library check (ldd)
    try:
        result = subprocess.run(
            ["ldd", chromium_path],
            capture_output=True, text=True, timeout=10,
        )
        missing = []
        for line in result.stdout.splitlines():
            if "not found" in line:
                missing.append(line.strip())
        if missing:
            print(f"   ❌ Missing {len(missing)} shared libraries:")
            for lib in missing[:10]:
                print(f"      {lib}")
        else:
            print("   ✅ All shared libraries found")
    except FileNotFoundError:
        print("   ⚠️  ldd not available — cannot check libraries")
    except Exception as e:
        print(f"   ⚠️  ldd failed: {e}")

    # 3. Headless test
    print("   Testing headless mode (5s timeout)...")
    try:
        result = subprocess.run(
            [chromium_path, "--headless", "--no-sandbox",
             "--disable-gpu", "--dump-dom", "about:blank"],
            capture_output=True, text=True, timeout=5,
        )
        if result.returncode == 0:
            print("   ✅ Headless mode works!")
        else:
            print(f"   ⚠️  Headless returned code {result.returncode}")
            stderr = result.stderr.strip()[:300]
            if stderr:
                print(f"   stderr: {stderr}")
    except subprocess.TimeoutExpired:
        print("   ⚠️  Headless test timed out — mode may not work")
        print("   Will try fallback options at launch")
    except Exception as e:
        print(f"   ❌ Headless test error: {e}")

    print("   ── Diagnosis complete ──")


class StealthBrowser:
    """Manages a stealth Chromium browser instance via Selenium."""

    def __init__(self, profile: dict = None, proxy: str = None):
        self.profile = profile or {}
        self.proxy = proxy
        self._driver = None

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, *args):
        self.close()

    def start(self):
        """Launch browser with stealth settings and diagnostics."""
        options = Options()

        # ── Find chromium ──
        chromium_path = _find_chromium()
        if not chromium_path:
            raise RuntimeError(
                "❌ Chromium not found!\n"
                "Install with:\n"
                "  pkg install x11-repo\n"
                "  pkg install chromium\n\n"
                "If chromium is in a different location, "
                "set it in config.py or add to PATH."
            )
        print(f"🌐 Chromium: {chromium_path}")
        options.binary_location = chromium_path

        # ── Run diagnostics ──
        _diagnose_chromium(chromium_path)

        # ── Headless mode ──
        options.add_argument("--headless")

        # ── Stability flags ──
        flags = [
            "--no-sandbox",
            "--disable-dev-shm-usage",
            "--disable-gpu",
            "--disable-software-rasterizer",
            "--disable-extensions",
            "--disable-infobars",
            "--no-first-run",
            "--disable-background-networking",
            "--disable-default-apps",
            "--disable-sync",
            "--disable-translate",
            "--metrics-recording-only",
            "--mute-audio",
            "--lang=en-US",
            "--single-process",
            "--disable-setuid-sandbox",
            "--no-zygote",
        ]
        for arg in flags:
            options.add_argument(arg)

        # ── Viewport & user agent ──
        vp = self.profile.get("viewport", VIEWPORT)
        options.add_argument(f"--window-size={vp['width']},{vp['height']}")
        ua = self.profile.get("user_agent", USER_AGENT)
        options.add_argument(f"--user-agent={ua}")

        if self.proxy:
            options.add_argument(f"--proxy-server={self.proxy}")

        # ── Anti-detection ──
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)

        # ── Find chromedriver ──
        chromedriver_path = _find_chromedriver()
        if not chromedriver_path:
            raise RuntimeError(
                "❌ Chromedriver not found!\n"
                "Install with:\n"
                "  pkg install chromium-driver"
            )
        print(f"🔧 Chromedriver: {chromedriver_path}")
        service = Service(executable_path=chromedriver_path)

        # ── Launch ──
        print("🚀 Launching browser...")
        try:
            self._driver = webdriver.Chrome(service=service, options=options)
        except Exception as e:
            err = str(e)
            if "timed out" in err.lower() or "timeout" in err.lower():
                raise RuntimeError(
                    "❌ Browser launch timed out!\n\n"
                    "This means chromedriver started but Chromium browser "
                    "could not connect back.\n\n"
                    "Common causes on Termux:\n"
                    "1. Chromium crashes on launch (missing libraries)\n"
                    "   → Run: ldd $(which chromium) | grep 'not found'\n"
                    "   → Install missing packages\n"
                    "2. Shared memory issue\n"
                    "   → Already using --disable-dev-shm-usage\n"
                    "3. Too many chromium processes running\n"
                    "   → Run: killall chromium\n\n"
                    f"Original error: {err[:300]}"
                )
            raise

        # Anti-detection JS
        self._driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": """
                Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
                window.chrome = { runtime: {}, loadTimes: function(){}, csi: function(){}, app: {} };
                Object.defineProperty(navigator, 'plugins', { get: () => [1,2,3,4,5] });
                Object.defineProperty(navigator, 'languages', { get: () => ['en-US','en'] });
            """
        })

        self._driver.set_page_load_timeout(30)
        self._driver.implicitly_wait(10)
        print("✅ Browser ready!")
        return self._driver

    @property
    def driver(self):
        return self._driver

    def close(self):
        try:
            if self._driver:
                self._driver.quit()
        except Exception:
            pass

    # ========================
    # Human-like interactions
    # ========================
    def human_type(self, element, text: str):
        element.click()
        time.sleep(random.uniform(0.1, 0.3))
        for char in text:
            if random.random() < TYPING_ERROR_RATE:
                wrong = chr(ord(char) + random.randint(-2, 2))
                element.send_keys(wrong)
                time.sleep(random.uniform(0.05, 0.15))
                element.send_keys("\b")
                time.sleep(random.uniform(0.05, 0.1))
            element.send_keys(char)
            time.sleep(random.uniform(TYPING_MIN_DELAY / 1000, TYPING_MAX_DELAY / 1000))
            if random.random() < 0.05:
                time.sleep(random.uniform(0.3, 0.8))

    def human_click(self, element):
        time.sleep(random.uniform(0.05, 0.2))
        element.click()

    def random_delay(self, min_sec: float = 1.0, max_sec: float = 3.0):
        time.sleep(random.uniform(min_sec, max_sec))

    def scroll_page(self, direction: str = "down", amount: int = None):
        if amount is None:
            amount = random.randint(200, 500)
        if direction == "up":
            amount = -amount
        self._driver.execute_script(f"window.scrollBy(0, {amount})")
        time.sleep(random.uniform(0.3, 0.8))

    def wait_for(self, selector: str, timeout: int = 10):
        return WebDriverWait(self._driver, timeout).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, selector))
        )

    def wait_for_clickable(self, selector: str, timeout: int = 10):
        return WebDriverWait(self._driver, timeout).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
        )

    def find(self, selector: str):
        return self._driver.find_element(By.CSS_SELECTOR, selector)

    def find_text(self, text: str):
        return self._driver.find_element(By.XPATH, f"//*[contains(text(), '{text}')]")

    def safe_find(self, selector: str):
        try:
            return self._driver.find_element(By.CSS_SELECTOR, selector)
        except Exception:
            return None

    def safe_find_text(self, text: str):
        try:
            return self._driver.find_element(By.XPATH, f"//*[contains(text(), '{text}')]")
        except Exception:
            return None

    @property
    def page_url(self) -> str:
        return self._driver.current_url

    def get_page_text(self) -> str:
        return self._driver.page_source or ""
