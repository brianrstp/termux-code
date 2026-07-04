"""
Gmail Creator - Main Gmail Creation Logic
Selenium-based, optimized for Termux/Android.
"""
import random
import time
from faker import Faker

from browser import StealthBrowser
from sms_verify import SmsVerifier
from config import (
    get_profile, save_account,
    STEP_DELAY_MIN, STEP_DELAY_MAX, PAGE_LOAD_TIMEOUT,
    MAX_VERIFICATION_RETRIES,
)

fake = Faker()

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

    def create(self) -> dict:
        """Run the full Gmail creation flow."""
        result = {"success": False, "error": None, "email": None}

        try:
            with self.browser:
                driver = self.browser.driver

                # Step 1: Warmup
                print("🔄 Step 1: Browser warmup...")
                self._warmup()

                # Step 2: Navigate to signup
                print("📝 Step 2: Opening signup page...")
                self._go_to_signup()

                # Step 3: Fill name
                print("👤 Step 3: Entering name...")
                self._fill_name()

                # Step 4: Birthday & gender
                print("🎂 Step 4: Birthday & gender...")
                self._fill_birthday_gender()

                # Step 5: Choose email
                print("📧 Step 5: Choosing email...")
                self._choose_email()

                # Step 6: Create password
                print("🔐 Step 6: Creating password...")
                self._create_password()

                # Step 7: Phone verification
                print("📱 Step 7: Phone verification...")
                verified = self._handle_verification()
                if not verified:
                    result["error"] = "Verification failed"
                    return result

                # Step 8: Skip optional steps
                print("⏭️ Step 8: Skipping optional steps...")
                self._skip_optional()

                # Step 9: Accept terms
                print("✅ Step 9: Accepting terms...")
                self._accept_terms()

                # Step 10: Verify success
                print("🎉 Step 10: Verifying...")
                success = self._verify_success()

                if success:
                    result["success"] = True
                    result["email"] = self.email
                    result["password"] = self.password
                    result["name"] = f"{self.first_name} {self.last_name}"
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

    def _warmup(self):
        for url in ["https://www.google.com", "https://about.google"]:
            try:
                self.browser.driver.get(url)
                self.browser.random_delay(2, 5)
                self.browser.scroll_page("down")
                self.browser.random_delay(1, 2)
            except Exception:
                pass

    def _go_to_signup(self):
        self.browser.driver.get(SIGNUP_URL)
        self.browser.random_delay(2, 4)
        self.browser.wait_for('input[name="firstName"]', timeout=15)

    def _fill_name(self):
        first = self.browser.find('input[name="firstName"]')
        first.click()
        time.sleep(random.uniform(0.2, 0.5))
        first.send_keys(self.first_name)
        self.browser.random_delay(0.3, 0.8)

        last = self.browser.find('input[name="lastName"]')
        last.click()
        time.sleep(random.uniform(0.2, 0.5))
        last.send_keys(self.last_name)
        self.browser.random_delay(0.5, 1.0)
        self._click_next()

    def _fill_birthday_gender(self):
        from selenium.webdriver.common.by import By

        driver = self.browser.driver

        # ── Month (Material Design custom dropdown) ──
        month = random.randint(1, 12)
        month_names = [
            "January", "February", "March", "April", "May", "June",
            "July", "August", "September", "October", "November", "December",
        ]
        month_name = month_names[month - 1]
        print(f"   📅 Selecting month: {month_name}")

        # Find month dropdown trigger — look for role="combobox" or
        # div containing "Month" text near the birthday section
        month_triggered = False

        # Strategy 1: aria-label or id containing "month"
        for selector in [
            '[aria-label*="Month" i]',
            '[aria-label*="month" i]',
            '#month',
            '[id*="month" i]',
        ]:
            try:
                el = driver.find_element(By.CSS_SELECTOR, selector)
                if el.is_displayed():
                    el.click()
                    time.sleep(0.5)
                    month_triggered = True
                    print(f"   📅 Month trigger found via: {selector}")
                    break
            except Exception:
                continue

        # Strategy 2: find a clickable div/button with "Month" text
        if not month_triggered:
            try:
                el = driver.find_element(By.XPATH,
                    "//*[contains(@role,'combobox') or contains(@role,'listbox')]"
                    "[.//span[contains(text(),'Month') or contains(text(),'month')]]"
                )
                if el.is_displayed():
                    el.click()
                    time.sleep(0.5)
                    month_triggered = True
                    print("   📅 Month trigger found via role combobox/listbox")
            except Exception:
                pass

        # Strategy 3: find element containing text "Month"
        if not month_triggered:
            try:
                el = driver.find_element(By.XPATH,
                    "//*[contains(text(),'Month') and "
                    "(self::div or self::button or self::span or self::input)]"
                )
                if el.is_displayed():
                    el.click()
                    time.sleep(0.5)
                    month_triggered = True
                    print("   📅 Month trigger found via text 'Month'")
            except Exception:
                pass

        if month_triggered:
            # Now click the month option
            self._select_dropdown_option(month_name)
        else:
            # Fallback: try native select
            try:
                from selenium.webdriver.support.ui import Select
                sel = driver.find_element(By.CSS_SELECTOR,
                    'select[name*="month" i], select[id*="month" i], select')
                Select(sel).select_by_value(str(month).zfill(2))
                print("   📅 Month: used native <select> fallback")
            except Exception:
                print("   ⚠️  Month dropdown not found — trying screenshot debug")
                self._debug_dump()
                raise RuntimeError("❌ Cannot find month dropdown on page")

        time.sleep(random.uniform(0.3, 0.6))

        # ── Day (input[type=tel]) ──
        day_val = str(random.randint(1, 28))
        print(f"   📅 Day: {day_val}")
        day_input = None
        for sel_str in ['input[name="day"]', '#day',
                        'input[aria-label*="Day" i]']:
            try:
                day_input = driver.find_element(By.CSS_SELECTOR, sel_str)
                if day_input.is_displayed():
                    break
                day_input = None
            except Exception:
                continue
        if day_input:
            day_input.click()
            time.sleep(0.1)
            day_input.clear()
            day_input.send_keys(day_val)
        else:
            raise RuntimeError("❌ Cannot find day input")
        time.sleep(random.uniform(0.3, 0.6))

        # ── Year (input[type=tel]) ──
        year_val = str(random.randint(1990, 2006))
        print(f"   📅 Year: {year_val}")
        year_input = None
        for sel_str in ['input[name="year"]', '#year',
                        'input[aria-label*="Year" i]']:
            try:
                year_input = driver.find_element(By.CSS_SELECTOR, sel_str)
                if year_input.is_displayed():
                    break
                year_input = None
            except Exception:
                continue
        if year_input:
            year_input.click()
            time.sleep(0.1)
            year_input.clear()
            year_input.send_keys(year_val)
        else:
            raise RuntimeError("❌ Cannot find year input")
        time.sleep(random.uniform(0.3, 0.6))

        # ── Gender (Material Design custom dropdown) ──
        gender_val = random.choice(["1", "2", "3"])
        gender_labels = {"1": "Female", "2": "Male", "3": "Rather not say"}
        gender_label = gender_labels[gender_val]
        print(f"   ⚧ Selecting gender: {gender_label}")

        gender_triggered = False
        for selector in [
            '[aria-label*="gender" i]',
            '[aria-label*="Gender"]',
        ]:
            try:
                el = driver.find_element(By.CSS_SELECTOR, selector)
                if el.is_displayed():
                    el.click()
                    time.sleep(0.5)
                    gender_triggered = True
                    print(f"   ⚧ Gender trigger found via: {selector}")
                    break
            except Exception:
                continue

        if gender_triggered:
            self._select_dropdown_option(gender_label)
        else:
            # Fallback: native select
            try:
                from selenium.webdriver.support.ui import Select
                sel = driver.find_element(By.CSS_SELECTOR,
                    'select[name*="gender" i], select[id*="gender" i], select')
                Select(sel).select_by_value(gender_val)
                print("   ⚧ Gender: used native <select> fallback")
            except Exception:
                print("   ⚠️  Gender dropdown not found, skipping")

        self.browser.random_delay(0.5, 1.5)
        self._click_next()

    def _select_dropdown_option(self, option_text: str):
        """After clicking a Material Design dropdown, select the option by text."""
        from selenium.webdriver.common.by import By
        driver = self.browser.driver
        time.sleep(0.5)  # Wait for dropdown animation

        # Strategy 1: li with matching text
        try:
            option = driver.find_element(By.XPATH,
                f"//li[.//text()[contains(.,'{option_text}')] or "
                f".//span[contains(text(),'{option_text}')]]"
            )
            option.click()
            print(f"   ✅ Selected: {option_text} (via li)")
            return
        except Exception:
            pass

        # Strategy 2: div with role="option"
        try:
            option = driver.find_element(By.XPATH,
                f"//*[@role='option'][contains(text(),'{option_text}')]"
            )
            option.click()
            print(f"   ✅ Selected: {option_text} (via role=option)")
            return
        except Exception:
            pass

        # Strategy 3: any element with matching text in dropdown overlay
        try:
            option = driver.find_element(By.XPATH,
                f"//*[contains(@class,'option') or contains(@class,'item')]"
                f"[contains(text(),'{option_text}')]"
            )
            option.click()
            print(f"   ✅ Selected: {option_text} (via class)")
            return
        except Exception:
            pass

        # Strategy 4: aria-selected or data-value
        try:
            option = driver.find_element(By.XPATH,
                f"//*[@aria-selected='true' or @data-value='{option_text}']"
            )
            option.click()
            print(f"   ✅ Selected: {option_text} (via aria/data)")
            return
        except Exception:
            pass

        print(f"   ⚠️  Could not select option '{option_text}' from dropdown")

    def _debug_dump(self):
        """Dump page HTML for debugging when elements can't be found."""
        from selenium.webdriver.common.by import By
        driver = self.browser.driver
        print("\n   ══ DEBUG PAGE DUMP ══")
        try:
            # Find all interactive elements
            for tag in ["select", "input", "button", "div[role]", "ul[role]"]:
                try:
                    els = driver.find_elements(By.CSS_SELECTOR, tag)
                    for el in els:
                        if el.is_displayed():
                            name = el.get_attribute("name") or ""
                            aid = el.get_attribute("id") or ""
                            role = el.get_attribute("role") or ""
                            aria = el.get_attribute("aria-label") or ""
                            text = el.text[:50] if el.text else ""
                            print(f"   <{tag}> name={name} id={aid} role={role} "
                                  f"aria={aria} text={text}")
                except Exception:
                    pass
        except Exception as e:
            print(f"   Debug dump failed: {e}")
        print("   ══ END DUMP ══\n")

    def _choose_email(self):
        self.browser.wait_for('[data-email], input[type="email"], input[name="Username"]', timeout=10)

        # Try suggestion
        try:
            suggestion = self.browser.safe_find('[data-email]')
            if suggestion and suggestion.is_displayed():
                self.email = suggestion.get_attribute("data-email")
                self.username = self.email.split("@")[0]
                self.human_click(suggestion)
                self.browser.random_delay(0.5, 1.0)
                self._click_next()
                return
        except Exception:
            pass

        # Custom username
        self.username = self._generate_username()
        self.email = f"{self.username}@gmail.com"

        username_input = self.browser.safe_find('input[name="Username"]') or self.browser.safe_find('input[type="email"]')
        if username_input:
            username_input.click()
            time.sleep(random.uniform(0.2, 0.5))
            username_input.clear()
            username_input.send_keys(self.username)
            self.browser.random_delay(0.5, 1.0)
            self._click_next()

            # Check taken
            time.sleep(2)
            error = self.browser.safe_find('[aria-live="assertive"]')
            if error and ("taken" in (error.text or "").lower() or "already" in (error.text or "").lower()):
                self.username = f"{self.username}{random.randint(100, 999)}"
                self.email = f"{self.username}@gmail.com"
                username_input.clear()
                username_input.send_keys(self.username)
                self.browser.random_delay(0.5, 1.0)
                self._click_next()

    def _create_password(self):
        self.password = self._generate_password()

        self.browser.wait_for('input[name="Passwd"], input[type="password"]', timeout=10)

        pwd = self.browser.find('input[name="Passwd"]')
        pwd.click()
        time.sleep(random.uniform(0.2, 0.5))
        pwd.send_keys(self.password)
        self.browser.random_delay(0.3, 0.8)

        confirm = self.browser.safe_find('input[name="PasswdAgain"]')
        if confirm and confirm.is_displayed():
            confirm.click()
            time.sleep(random.uniform(0.2, 0.5))
            confirm.send_keys(self.password)

        self.browser.random_delay(0.5, 1.0)
        self._click_next()

    def _handle_verification(self) -> bool:
        time.sleep(3)
        for attempt in range(MAX_VERIFICATION_RETRIES):
            url = self.browser.page_url
            if "verify" in url.lower() or "challenge" in url.lower():
                return self._process_verification()
            body = self.browser.get_page_text().lower()
            if "verify" in body or "phone" in body:
                return self._process_verification()
            if "welcome" in body or "congratulations" in body:
                return True
            if "myaccount" in url or "mail" in url:
                return True
            if self._handle_other_pages():
                continue
            time.sleep(2)
        return True

    def _process_verification(self) -> bool:
        try:
            skip = self.browser.safe_find_text("Try another way")
            if skip and skip.is_displayed():
                skip.click()
                time.sleep(2)

            sms_opt = self.browser.safe_find_text("Get a verification code at")
            if sms_opt and sms_opt.is_displayed():
                sms_opt.click()
                time.sleep(1)

            phone_input = self.browser.safe_find('input[type="tel"]')
            if phone_input and phone_input.is_displayed():
                sms_data = self.sms_verifier.get_number()
                phone = sms_data["number"]
                sms_id = sms_data["id"]
                print(f"📱 Using phone: {phone}")

                phone_input.click()
                phone_input.send_keys(phone)
                self.browser.random_delay(0.5, 1.0)
                self._click_next()
                time.sleep(3)

                try:
                    code = self.sms_verifier.get_code(sms_id, timeout=120)
                    print(f"📨 Received code: {code}")
                    code_input = self.browser.safe_find('input[type="tel"]') or self.browser.safe_find('input[type="number"]')
                    if code_input and code_input.is_displayed():
                        code_input.click()
                        code_input.send_keys(code)
                        self.browser.random_delay(0.5, 1.0)
                        self._click_next()
                        time.sleep(3)
                        return True
                except TimeoutError:
                    print("⏰ SMS timeout")
                    self.sms_verifier.cancel_number(sms_id)

            skip_btn = self.browser.safe_find_text("Skip")
            if skip_btn and skip_btn.is_displayed():
                skip_btn.click()
                time.sleep(2)
                return True

            return False
        except Exception as e:
            print(f"⚠️ Verification error: {e}")
            return False

    def _handle_other_pages(self) -> bool:
        body = self.browser.get_page_text().lower()
        if "captcha" in body or "robot" in body:
            print("🤖 CAPTCHA detected, waiting...")
            time.sleep(5)
            return True
        if "too many" in body or "try again" in body:
            print("⏳ Rate limited, waiting 30s...")
            time.sleep(30)
            return True
        return False

    def _skip_optional(self):
        for _ in range(3):
            for text in ["Skip", "Not now", "No thanks"]:
                btn = self.browser.safe_find_text(text)
                if btn and btn.is_displayed():
                    btn.click()
                    self.browser.random_delay(1, 2)
                    break

    def _accept_terms(self):
        try:
            self.browser.scroll_page("down", 1000)
            time.sleep(1)
            for text in ["I agree", "Agree", "Accept"]:
                btn = self.browser.safe_find_text(text)
                if btn and btn.is_displayed():
                    btn.click()
                    self.browser.random_delay(2, 4)
                    return
            self.browser.scroll_page("down", 1000)
            time.sleep(1)
            self._click_next()
        except Exception as e:
            print(f"⚠️ Terms: {e}")

    def _verify_success(self) -> bool:
        time.sleep(5)
        url = self.browser.page_url.lower()
        for indicator in ["myaccount.google.com", "mail.google.com", "accounts.google.com/b"]:
            if indicator in url:
                return True
        body = self.browser.get_page_text().lower()
        return "welcome" in body or "congratulations" in body

    # ========================
    # Helpers
    # ========================

    def _click_next(self):
        for text in ["Next"]:
            btn = self.browser.safe_find_text(text)
            if btn and btn.is_displayed():
                btn.click()
                self.browser.random_delay(1, 2)
                return
        self.browser.driver.find_element(By.TAG_NAME, "body").send_keys("\n")
        self.browser.random_delay(1, 2)

    def _generate_username(self) -> str:
        patterns = [
            f"{self.first_name.lower()}{self.last_name.lower()}{random.randint(10, 99)}",
            f"{self.first_name.lower()}.{self.last_name.lower()}{random.randint(10, 99)}",
            f"{self.first_name[0].lower()}{self.last_name.lower()}{random.randint(100, 999)}",
            f"{self.first_name.lower()}{random.randint(1000, 9999)}",
        ]
        return random.choice(patterns)

    def _generate_password(self) -> str:
        special = "!@#$%^&*"
        return (
            self.first_name.capitalize()
            + random.choice(special)
            + str(random.randint(100, 999))
            + random.choice("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
            + random.choice(special)
        )


def create_one(proxy: str = None, sms_provider: str = None) -> dict:
    """Create a single Gmail account."""
    creator = GmailCreator(proxy=proxy, sms_provider=sms_provider)
    return creator.create()


def create_batch(count: int, proxy: str = None, sms_provider: str = None) -> list:
    """Create multiple Gmail accounts sequentially."""
    results = []
    for i in range(count):
        print(f"\n{'='*50}")
        print(f"📧 Creating account {i+1}/{count}")
        print(f"{'='*50}")
        result = create_one(proxy=proxy, sms_provider=sms_provider)
        results.append(result)
        if i < count - 1:
            delay = random.uniform(5, 15)
            print(f"\n⏳ Waiting {delay:.1f}s before next account...")
            time.sleep(delay)
    return results
