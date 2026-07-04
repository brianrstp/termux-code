"""
Gmail Creator - Browser Module
Playwright-based browser with stealth features for Termux/Android.
Replaces Chromax browser from Windows version.
"""
import asyncio
import random
import os

try:
    from playwright.async_api import async_playwright, Browser, BrowserContext, Page
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    print("⚠️  Playwright not installed. Install with:")
    print("    pip install --no-binary :all: playwright")
    print("    (or run setup_termux.sh)")

from config import (
    STEALTH_ARGS, HEADLESS, VIEWPORT, USER_AGENT,
    PROXY, TYPING_MIN_DELAY, TYPING_MAX_DELAY, TYPING_ERROR_RATE,
)


class StealthBrowser:
    """Manages a stealth Chromium browser instance via Playwright."""

    def __init__(self, profile: dict = None, proxy: str = None):
        self.profile = profile or {}
        self.proxy = proxy or PROXY
        self._playwright = None
        self._browser: Browser = None
        self._context: BrowserContext = None
        self._page: Page = None

    async def __aenter__(self):
        await self.start()
        return self

    async def __aexit__(self, *args):
        await self.close()

    async def start(self):
        """Launch browser with stealth settings."""
        if not PLAYWRIGHT_AVAILABLE:
            raise RuntimeError(
                "Playwright is not installed!\n"
                "Install it with:\n"
                "  pip install --no-binary :all: playwright\n"
                "  python -m playwright install chromium\n"
                "Or run: ./setup_termux.sh"
            )
        self._playwright = await async_playwright().start()

        launch_args = {
            "headless": HEADLESS,
            "args": STEALTH_ARGS,
        }

        # Proxy support
        if self.proxy:
            launch_args["proxy"] = {"server": self.proxy}

        # Try launching - fallback to system chromium on ARM/Termux
        try:
            self._browser = await self._playwright.chromium.launch(**launch_args)
        except Exception as e:
            print(f"⚠️  Chromium launch failed: {e}")
            print("🔄 Trying system chromium...")
            import shutil
            system_chromium = (
                shutil.which("chromium-browser")
                or shutil.which("chromium")
                or os.environ.get("PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH")
            )
            if system_chromium:
                launch_args["executable_path"] = system_chromium
                self._browser = await self._playwright.chromium.launch(**launch_args)
            else:
                raise RuntimeError(
                    "No chromium found! Install with:\n"
                    "  pkg install chromium\n"
                    "or run: python -m playwright install chromium"
                )

        # Determine viewport & user agent from profile
        vp = self.profile.get("viewport", VIEWPORT)
        ua = self.profile.get("user_agent", USER_AGENT)
        locale = self.profile.get("locale", "en-US")
        tz = self.profile.get("timezone", "America/New_York")

        context_args = {
            "viewport": vp,
            "user_agent": ua,
            "locale": locale,
            "timezone_id": tz,
            "permissions": ["geolocation"],
            "geolocation": {"latitude": 40.7128, "longitude": -74.0060},
            "java_script_enabled": True,
            "bypass_csp": True,
            "ignore_https_errors": True,
        }

        self._context = await self._browser.new_context(**context_args)

        # Apply stealth scripts to every new page
        await self._apply_stealth_scripts()

        self._page = await self._context.new_page()

        # Block detection-heavy resources
        await self._setup_request_interception()

        return self._page

    async def _apply_stealth_scripts(self):
        """Inject JavaScript to hide automation indicators."""
        stealth_js = """
        // Overwrite navigator.webdriver
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined,
        });

        // Overwrite chrome detection
        window.chrome = {
            runtime: {},
            loadTimes: function() {},
            csi: function() {},
            app: {},
        };

        // Overwrite permissions
        const originalQuery = window.navigator.permissions.query;
        window.navigator.permissions.query = (parameters) =>
            parameters.name === 'notifications'
                ? Promise.resolve({ state: Notification.permission })
                : originalQuery(parameters);

        // Overwrite plugins
        Object.defineProperty(navigator, 'plugins', {
            get: () => [1, 2, 3, 4, 5],
        });

        // Overwrite languages
        Object.defineProperty(navigator, 'languages', {
            get: () => ['en-US', 'en'],
        });

        // Prevent WebGL fingerprint detection
        const getParameter = WebGLRenderingContext.prototype.getParameter;
        WebGLRenderingContext.prototype.getParameter = function(parameter) {
            if (parameter === 37445) return 'Intel Inc.';
            if (parameter === 37446) return 'Intel Iris OpenGL Engine';
            return getParameter.call(this, parameter);
        };

        // Override toString to prevent function detection
        const origToString = Function.prototype.toString;
        Function.prototype.toString = function() {
            if (this === navigator.permissions.query) {
                return 'function query() { [native code] }';
            }
            return origToString.call(this);
        };
        """
        await self._context.add_init_script(stealth_js)

    async def _setup_request_interception(self):
        """Block requests that could be used for bot detection."""
        async def route_handler(route):
            request = route.request
            resource_type = request.resource_type

            # Block tracking/analytics that detect automation
            block_patterns = [
                "google-analytics.com",
                "googletagmanager.com",
                "doubleclick.net",
                "googlesyndication.com",
            ]
            url = request.url

            if any(p in url for p in block_patterns):
                await route.abort()
            elif resource_type in ("image", "media", "font") and "google" not in url:
                # Allow Google resources but block others to speed up
                await route.continue_()
            else:
                await route.continue_()

        await self._context.route("**/*", route_handler)

    @property
    def page(self) -> Page:
        return self._page

    @property
    def context(self) -> BrowserContext:
        return self._context

    async def close(self):
        """Clean up all browser resources."""
        try:
            if self._page and not self._page.is_closed():
                await self._page.close()
        except Exception:
            pass
        try:
            if self._context:
                await self._context.close()
        except Exception:
            pass
        try:
            if self._browser:
                await self._browser.close()
        except Exception:
            pass
        try:
            if self._playwright:
                await self._playwright.stop()
        except Exception:
            pass

    # ========================
    # Human-like interactions
    # ========================
    async def human_type(self, page: Page, selector: str, text: str):
        """Type text with human-like delays and occasional typos."""
        await page.click(selector)
        await asyncio.sleep(random.uniform(0.1, 0.3))

        for i, char in enumerate(text):
            # Occasional typo
            if random.random() < TYPING_ERROR_RATE:
                wrong_char = chr(ord(char) + random.randint(-2, 2))
                await page.keyboard.type(wrong_char, delay=random.uniform(10, 30))
                await asyncio.sleep(random.uniform(0.05, 0.15))
                await page.keyboard.press("Backspace")
                await asyncio.sleep(random.uniform(0.05, 0.1))

            await page.keyboard.type(char, delay=random.uniform(TYPING_MIN_DELAY, TYPING_MAX_DELAY))

            # Occasional pause (thinking)
            if random.random() < 0.05:
                await asyncio.sleep(random.uniform(0.3, 0.8))

    async def human_click(self, page: Page, selector: str):
        """Click an element with human-like mouse movement."""
        element = await page.wait_for_selector(selector, timeout=10000)
        if element:
            box = await element.bounding_box()
            if box:
                # Random offset within element
                x = box["x"] + random.uniform(box["width"] * 0.2, box["width"] * 0.8)
                y = box["y"] + random.uniform(box["height"] * 0.2, box["height"] * 0.8)

                # Move mouse gradually
                await page.mouse.move(x, y, steps=random.randint(5, 15))
                await asyncio.sleep(random.uniform(0.05, 0.2))
                await page.mouse.click(x, y)
            else:
                await element.click()
        else:
            await page.click(selector)

    async def random_delay(self, min_sec: float = 1.0, max_sec: float = 3.0):
        """Wait a random amount of time."""
        delay = random.uniform(min_sec, max_sec)
        await asyncio.sleep(delay)

    async def scroll_page(self, page: Page, direction: str = "down", amount: int = None):
        """Scroll page naturally."""
        if amount is None:
            amount = random.randint(200, 500)
        if direction == "up":
            amount = -amount
        await page.mouse.wheel(0, amount)
        await asyncio.sleep(random.uniform(0.3, 0.8))
