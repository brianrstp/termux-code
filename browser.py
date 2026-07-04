"""
Gmail Creator - Browser Module
Selenium-based browser with stealth features for Termux/Android.
"""
import random
import time
import shutil
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from config import (
    HEADLESS, VIEWPORT, USER_AGENT,
    TYPING_MIN_DELAY, TYPING_MAX_DELAY, TYPING_ERROR_RATE,
)


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
        """Launch browser with stealth settings."""
        options = Options()

        # Find chromium binary
        chromium_path = (
            shutil.which("chromium")
            or shutil.which("chromium-browser")
            or "/data/data/com.termux/files/usr/bin/chromium"
        )
        options.binary_location = chromium_path

        if HEADLESS:
            options.add_argument("--headless=new")

        # Stealth args
        for arg in [
            "--no-sandbox",
            "--disable-dev-shm-usage",
            "--disable-blink-features=AutomationControlled",
            "--disable-gpu",
            "--disable-web-security",
            "--disable-extensions",
            "--disable-infobars",
            "--no-first-run",
            "--lang=en-US",
        ]:
            options.add_argument(arg)

        # Viewport & user agent
        vp = self.profile.get("viewport", VIEWPORT)
        options.add_argument(f"--window-size={vp['width']},{vp['height']}")
        ua = self.profile.get("user_agent", USER_AGENT)
        options.add_argument(f"--user-agent={ua}")

        if self.proxy:
            options.add_argument(f"--proxy-server={self.proxy}")

        # Anti-detection
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)

        # Find chromedriver
        chromedriver_path = (
            shutil.which("chromedriver")
            or "/data/data/com.termux/files/usr/bin/chromedriver"
        )
        service = None
        if chromedriver_path and __import__("os").path.exists(chromedriver_path):
            from selenium.webdriver.chrome.service import Service
            service = Service(executable_path=chromedriver_path)
            print(f"🔧 Using chromedriver: {chromedriver_path}")

        # Try launching — fallback to webdriver-manager
        try:
            if service:
                self._driver = webdriver.Chrome(service=service, options=options)
            else:
                self._driver = webdriver.Chrome(options=options)
        except Exception:
            print("⚠️  Chromedriver not found, using webdriver-manager...")
            from webdriver_manager.chrome import ChromeDriverManager
            from selenium.webdriver.chrome.service import Service as ChromeService
            service = ChromeService(ChromeDriverManager().install())
            self._driver = webdriver.Chrome(service=service, options=options)

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
        """Type text with human-like delays and occasional typos."""
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
