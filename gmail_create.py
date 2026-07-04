"""
Gmail Creator - Main Gmail Creation Logic
Optimized for Termux/Android with Playwright + stealth.
"""
import asyncio
import random
import re
from faker import Faker

from browser import StealthBrowser
from sms_verify import SmsVerifier
from config import (
    get_profile, save_account,
    STEP_DELAY_MIN, STEP_DELAY_MAX, PAGE_LOAD_TIMEOUT,
    MAX_VERIFICATION_RETRIES,
)

fake = Faker()

# Gmail signup URL
SIGNUP_URL = "https://accounts.google.com/signup"


class GmailCreator:
    """Creates Gmail accounts with anti-detection measures."""

    def __init__(self, proxy: str = None, sms_provider: str = None):
        self.proxy = proxy
        self.sms_verifier = SmsVerifier(sms_provider)
        self.profile = get_profile(random.randint(0, 100))
        self.browser = StealthBrowser(profile=self.profile, proxy=proxy)
        self.first_name = fake.first_name()
        self.last_name = fake.last_name()
        self.username = None
        self.password = None
        self.email = None

    async def create(self) -> dict:
        """
        Run the full Gmail creation flow.
        Returns dict with account info or error.
        """
        result = {"success": False, "error": None, "email": None}

        try:
            async with self.browser as browser:
                page = self.browser.page

                # Step 1: Warmup
                print("🔄 Step 1: Browser warmup...")
                await self._warmup(page)

                # Step 2: Navigate to signup
                print("📝 Step 2: Opening signup page...")
                await self._go_to_signup(page)

                # Step 3: Fill name
                print("👤 Step 3: Entering name...")
                await self._fill_name(page)

                # Step 4: Birthday & gender
                print("🎂 Step 4: Birthday & gender...")
                await self._fill_birthday_gender(page)

                # Step 5: Choose email
                print("📧 Step 5: Choosing email...")
                await self._choose_email(page)

                # Step 6: Create password
                print("🔐 Step 6: Creating password...")
                await self._create_password(page)

                # Step 7: Phone verification (if required)
                print("📱 Step 7: Phone verification...")
                verified = await self._handle_verification(page)
                if not verified:
                    result["error"] = "Verification failed"
                    return result

                # Step 8: Skip optional steps
                print("⏭️ Step 8: Skipping optional steps...")
                await self._skip_optional(page)

                # Step 9: Accept terms
                print("✅ Step 9: Accepting terms...")
                await self._accept_terms(page)

                # Step 10: Verify success
                print("🎉 Step 10: Verifying account creation...")
                success = await self._verify_success(page)

                if success:
                    result["success"] = True
                    result["email"] = self.email
                    result["password"] = self.password
                    result["name"] = f"{self.first_name} {self.last_name}"

                    # Save to storage
                    save_account(
                        email=self.email,
                        password=self.password,
                        profile_name=self.profile["name"],
                    )
                    print(f"\n✅ Account created: {self.email}")
                else:
                    result["error"] = "Account creation could not be verified"

        except Exception as e:
            result["error"] = str(e)
            print(f"\n❌ Error: {e}")

        return result

    # ========================
    # Flow Steps
    # ========================

    async def _warmup(self, page):
        """Visit sites to warm up browser fingerprint."""
        pages_to_visit = [
            "https://www.google.com",
            "https://about.google",
        ]
        for url in pages_to_visit:
            try:
                await page.goto(url, timeout=PAGE_LOAD_TIMEOUT)
                await self.browser.random_delay(2, 5)
                # Simulate scrolling
                await self.browser.scroll_page(page, "down")
                await self.browser.random_delay(1, 2)
            except Exception:
                pass

    async def _go_to_signup(self, page):
        """Navigate to Gmail signup page."""
        await page.goto(SIGNUP_URL, timeout=PAGE_LOAD_TIMEOUT, wait_until="networkidle")
        await self.browser.random_delay(1, 3)

        # Check if we're on the right page
        await page.wait_for_selector('input[name="firstName"]', timeout=15000)

    async def _fill_name(self, page):
        """Enter first and last name."""
        first_name_input = page.locator('input[name="firstName"]')
        await first_name_input.click()
        await asyncio.sleep(random.uniform(0.2, 0.5))
        await first_name_input.type(self.first_name, delay=random.uniform(40, 110))

        await self.browser.random_delay(0.3, 0.8)

        last_name_input = page.locator('input[name="lastName"]')
        await last_name_input.click()
        await asyncio.sleep(random.uniform(0.2, 0.5))
        await last_name_input.type(self.last_name, delay=random.uniform(40, 110))

        await self.browser.random_delay(0.5, 1.0)

        # Click Next
        await self._click_next(page)

    async def _fill_birthday_gender(self, page):
        """Enter birthday and gender."""
        await page.wait_for_selector('select[name="month"]', timeout=10000)

        # Month
        month = random.randint(1, 12)
        await page.select_option('select[name="month"]', str(month).zfill(2))
        await asyncio.sleep(random.uniform(0.3, 0.6))

        # Day
        day = random.randint(1, 28)
        await page.fill('input[name="day"]', str(day))
        await asyncio.sleep(random.uniform(0.3, 0.6))

        # Year (18-35 years old)
        year = random.randint(1990, 2006)
        await page.fill('input[name="year"]', str(year))
        await asyncio.sleep(random.uniform(0.3, 0.6))

        # Gender
        gender = random.choice(["1", "2", "3"])  # 1=Male, 2=Female, 3=Rather not say
        await page.select_option('select[name="gender"]', gender)

        await self.browser.random_delay(0.5, 1.5)
        await self._click_next(page)

    async def _choose_email(self, page):
        """Choose or create email address."""
        await page.wait_for_selector('[data-email], input[type="email"], [aria-label*="Username"]',
                                      timeout=10000)

        # Try to find "Create your own" option
        try:
            create_own = page.locator('text=Create your own Gmail address')
            if await create_own.is_visible(timeout=3000):
                await create_own.click()
                await asyncio.sleep(1)
        except Exception:
            pass

        # Check if there's a suggested email we can use
        try:
            suggestion = page.locator('[data-email]').first
            if await suggestion.is_visible(timeout=2000):
                suggested_email = await suggestion.get_attribute("data-email")
                if suggested_email:
                    self.username = suggested_email.split("@")[0]
                    self.email = suggested_email
                    await suggestion.click()
                    await self.browser.random_delay(0.5, 1.0)
                    await self._click_next(page)
                    return
        except Exception:
            pass

        # Generate and type custom username
        self.username = self._generate_username()
        self.email = f"{self.username}@gmail.com"

        username_input = page.locator('input[name="Username"], input[type="email"]')
        await username_input.click()
        await asyncio.sleep(random.uniform(0.2, 0.5))
        await username_input.fill("")  # Clear first
        await username_input.type(self.username, delay=random.uniform(40, 110))

        await self.browser.random_delay(0.5, 1.0)
        await self._click_next(page)

        # Check if username is taken
        await asyncio.sleep(2)
        error = await page.query_selector('[aria-live="assertive"]')
        if error:
            error_text = await error.text_content()
            if error_text and ("taken" in error_text.lower() or "already" in error_text.lower()):
                # Try with numbers
                self.username = f"{self.username}{random.randint(100, 999)}"
                self.email = f"{self.username}@gmail.com"
                await username_input.fill("")
                await username_input.type(self.username, delay=random.uniform(40, 110))
                await self.browser.random_delay(0.5, 1.0)
                await self._click_next(page)

    async def _create_password(self, page):
        """Create and confirm password."""
        self.password = self._generate_password()

        await page.wait_for_selector('input[name="Passwd"], input[type="password"]', timeout=10000)

        # Enter password
        pwd_input = page.locator('input[name="Passwd"]')
        await pwd_input.click()
        await asyncio.sleep(random.uniform(0.2, 0.5))
        await pwd_input.type(self.password, delay=random.uniform(40, 110))

        await self.browser.random_delay(0.3, 0.8)

        # Confirm password
        confirm_input = page.locator('input[name="PasswdAgain"]')
        if await confirm_input.is_visible(timeout=3000):
            await confirm_input.click()
            await asyncio.sleep(random.uniform(0.2, 0.5))
            await confirm_input.type(self.password, delay=random.uniform(40, 110))

        await self.browser.random_delay(0.5, 1.0)
        await self._click_next(page)

    async def _handle_verification(self, page) -> bool:
        """Handle phone verification if required."""
        await asyncio.sleep(3)

        for attempt in range(MAX_VERIFICATION_RETRIES):
            current_url = page.url

            # Check if we're on verification page
            if "verify" in current_url.lower() or "challenge" in current_url.lower():
                return await self._process_verification(page)

            # Check page content
            try:
                page_text = await page.text_content("body")
                if page_text:
                    page_text_lower = page_text.lower()
                    if "verify" in page_text_lower or "phone" in page_text_lower:
                        return await self._process_verification(page)
                    if "congratulations" in page_text_lower or "welcome" in page_text_lower:
                        return True  # No verification needed
            except Exception:
                pass

            # Check if we've moved past verification
            if "myaccount" in current_url or "mail" in current_url:
                return True

            # Might be a different page type
            if await self._handle_other_pages(page):
                continue

            await asyncio.sleep(2)

        # If no verification page appeared, might be fine
        return True

    async def _process_verification(self, page) -> bool:
        """Process the actual verification step."""
        try:
            # Try "Try another way" first
            try:
                another_way = page.locator('text=Try another way')
                if await another_way.is_visible(timeout=3000):
                    await another_way.click()
                    await asyncio.sleep(2)
            except Exception:
                pass

            # Look for SMS option
            try:
                sms_option = page.locator('text=Get a verification code at')
                if await sms_option.is_visible(timeout=3000):
                    await sms_option.click()
                    await asyncio.sleep(1)
            except Exception:
                pass

            # Get phone number input
            phone_input = page.locator('input[type="tel"]')
            if await phone_input.is_visible(timeout=5000):
                # Get number from SMS provider
                sms_data = await self.sms_verifier.get_number()
                phone_number = sms_data["number"]
                sms_id = sms_data["id"]

                print(f"📱 Using phone: {phone_number}")

                # Enter phone number
                await phone_input.click()
                await phone_input.type(phone_number, delay=random.uniform(50, 100))
                await self.browser.random_delay(0.5, 1.0)

                # Click send/next
                await self._click_next(page)
                await asyncio.sleep(3)

                # Wait for and enter code
                try:
                    code = await self.sms_verifier.get_code(sms_id, timeout=120)
                    print(f"📨 Received code: {code}")

                    code_input = page.locator('input[type="tel"], input[type="number"]')
                    if await code_input.is_visible(timeout=10000):
                        await code_input.click()
                        await code_input.type(code, delay=random.uniform(50, 100))
                        await self.browser.random_delay(0.5, 1.0)
                        await self._click_next(page)
                        await asyncio.sleep(3)
                        return True
                except TimeoutError:
                    print("⏰ SMS timeout, retrying...")
                    await self.sms_verifier.cancel_number(sms_id)

            # Try skip/no verification
            try:
                skip_btn = page.locator('button:has-text("Skip"), a:has-text("Skip")')
                if await skip_btn.is_visible(timeout=3000):
                    await skip_btn.click()
                    await asyncio.sleep(2)
                    return True
            except Exception:
                pass

            return False

        except Exception as e:
            print(f"⚠️ Verification error: {e}")
            return False

    async def _handle_other_pages(self, page) -> bool:
        """Handle unexpected page types during signup."""
        try:
            body_text = await page.text_content("body") or ""
            body_lower = body_text.lower()

            # CAPTCHA page
            if "captcha" in body_lower or "robot" in body_lower:
                print("🤖 CAPTCHA detected! Waiting 5 seconds...")
                await asyncio.sleep(5)
                return True

            # Rate limited
            if "too many" in body_lower or "try again" in body_lower:
                print("⏳ Rate limited. Waiting 30 seconds...")
                await asyncio.sleep(30)
                return True

            # Blocked
            if "couldn't create" in body_lower or "not available" in body_lower:
                print("🚫 Account creation blocked")
                return False

        except Exception:
            pass
        return False

    async def _skip_optional(self, page):
        """Skip optional setup steps."""
        skip_selectors = [
            'button:has-text("Skip")',
            'button:has-text("Not now")',
            'button:has-text("No thanks")',
            'a:has-text("Skip")',
            'a:has-text("Not now")',
        ]

        for _ in range(3):  # Skip up to 3 optional pages
            for sel in skip_selectors:
                try:
                    btn = page.locator(sel).first
                    if await btn.is_visible(timeout=2000):
                        await btn.click()
                        await self.browser.random_delay(1, 2)
                        break
                except Exception:
                    continue

    async def _accept_terms(self, page):
        """Accept Google Terms of Service."""
        try:
            # Scroll to bottom of terms
            await self.browser.scroll_page(page, "down", 1000)
            await asyncio.sleep(1)

            # Click agree/accept
            agree_selectors = [
                'button:has-text("I agree")',
                'button:has-text("Agree")',
                'button:has-text("Accept")',
                'button:has-text("I agree to the")',
            ]

            for sel in agree_selectors:
                try:
                    btn = page.locator(sel).first
                    if await btn.is_visible(timeout=3000):
                        await btn.click()
                        await self.browser.random_delay(2, 4)
                        return
                except Exception:
                    continue

            # Sometimes need to scroll more and click
            await self.browser.scroll_page(page, "down", 1000)
            await asyncio.sleep(1)
            await self._click_next(page)

        except Exception as e:
            print(f"⚠️ Terms acceptance: {e}")

    async def _verify_success(self, page) -> bool:
        """Verify that account was successfully created."""
        await asyncio.sleep(5)
        current_url = page.url

        success_indicators = [
            "myaccount.google.com",
            "mail.google.com",
            "accounts.google.com/b",
            "welcome",
        ]

        for indicator in success_indicators:
            if indicator in current_url.lower():
                return True

        try:
            body = await page.text_content("body") or ""
            body_lower = body.lower()
            if "welcome" in body_lower or "congratulations" in body_lower:
                return True
        except Exception:
            pass

        return False

    # ========================
    # Helpers
    # ========================

    async def _click_next(self, page):
        """Click the Next button."""
        next_selectors = [
            'button:has-text("Next")',
            '#next button',
            'div[role="button"]:has-text("Next")',
            'button[jsname="LgbsSe"]',
        ]

        for sel in next_selectors:
            try:
                btn = page.locator(sel).first
                if await btn.is_visible(timeout=3000):
                    await btn.click()
                    await self.browser.random_delay(1, 2)
                    return
            except Exception:
                continue

        # Fallback: press Enter
        await page.keyboard.press("Enter")
        await self.browser.random_delay(1, 2)

    def _generate_username(self) -> str:
        """Generate a realistic-looking username."""
        patterns = [
            lambda: f"{self.first_name.lower()}{self.last_name.lower()}{random.randint(10, 99)}",
            lambda: f"{self.first_name.lower()}.{self.last_name.lower()}{random.randint(10, 99)}",
            lambda: f"{self.first_name[0].lower()}{self.last_name.lower()}{random.randint(100, 999)}",
            lambda: f"{self.first_name.lower()}{random.randint(1000, 9999)}",
            lambda: f"{self.first_name.lower()}{self.last_name.lower()}{random.choice(['dev', 'me', 'official', 'x', 'info'])}",
        ]
        return random.choice(patterns)()

    def _generate_password(self) -> str:
        """Generate a strong password."""
        special = "!@#$%^&*"
        pwd = (
            self.first_name.capitalize()
            + random.choice(special)
            + str(random.randint(100, 999))
            + random.choice("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
            + random.choice(special)
        )
        return pwd


async def create_one(proxy: str = None, sms_provider: str = None) -> dict:
    """Create a single Gmail account."""
    creator = GmailCreator(proxy=proxy, sms_provider=sms_provider)
    return await creator.create()


async def create_batch(count: int, proxy: str = None, sms_provider: str = None) -> list:
    """Create multiple Gmail accounts sequentially."""
    results = []
    for i in range(count):
        print(f"\n{'='*50}")
        print(f"📧 Creating account {i+1}/{count}")
        print(f"{'='*50}")

        result = await create_one(proxy=proxy, sms_provider=sms_provider)
        results.append(result)

        # Delay between accounts
        if i < count - 1:
            delay = random.uniform(5, 15)
            print(f"\n⏳ Waiting {delay:.1f}s before next account...")
            await asyncio.sleep(delay)

    return results
