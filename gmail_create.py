"""
Gmail Creator - Main Gmail Creation Logic
Selenium-based, optimized for Termux/Android.
"""
import random
import time
from faker import Faker
from selenium.webdriver.common.by import By

from browser import StealthBrowser
from sms_verify import SmsVerifier
from config import (
    get_profile, save_account,
    STEP_DELAY_MIN, STEP_DELAY_MAX, PAGE_LOAD_TIMEOUT,
    MAX_VERIFICATION_RETRIES,
)

fake = Faker()

SIGNUP_URL = "https://accounts.google.com/signup"
GOOGLE_URLS = [
    "https://www.google.com",
    "https://www.google.com/search?q=weather+today",
    "https://www.youtube.com",
    "https://news.google.com",
    "https://accounts.google.com",
]


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
        """Build trust signals before signup: accept cookies, visit Google properties."""
        driver = self.browser.driver

        # Step 1: Visit Google and accept cookie consent
        print("   🍪 Accepting cookies...")
        try:
            driver.get("https://www.google.com")
            self.browser.random_delay(2, 4)
            self._accept_cookies()
            self.browser.random_delay(1, 2)
        except Exception:
            pass

        # Step 2: Do a Google search (builds trust)
        print("   🔍 Performing search warmup...")
        try:
            driver.get("https://www.google.com/search?q=weather+today")
            self.browser.random_delay(2, 4)
            self._accept_cookies()
            self.browser.scroll_page("down")
            self.browser.random_delay(1, 3)
        except Exception:
            pass

        # Step 3: Visit YouTube (another Google property)
        print("   🎬 YouTube warmup...")
        try:
            driver.get("https://www.youtube.com")
            self.browser.random_delay(2, 4)
            self._accept_cookies()
            self.browser.scroll_page("down")
            self.browser.random_delay(1, 3)
        except Exception:
            pass

        # Step 4: Visit Google News
        print("   📰 News warmup...")
        try:
            driver.get("https://news.google.com")
            self.browser.random_delay(2, 4)
            self._accept_cookies()
            self.browser.random_delay(1, 2)
        except Exception:
            pass

        print("   ✅ Warmup complete")

    def _accept_cookies(self):
        """Click cookie consent buttons on Google pages."""
        from selenium.webdriver.common.by import By
        driver = self.browser.driver
        # Common cookie consent button selectors
        for sel in [
            'button[id*="accept" i]',
            'button[id*="agree" i]',
            'button[id*="consent" i]',
            'button[aria-label*="accept" i]',
            'button[aria-label*="agree" i]',
            'form[action*="consent"] button',
            '#L2AGLb',  # Google's cookie consent ID
            '[data-idom-class] button:first-child',
        ]:
            try:
                btn = driver.find_element(By.CSS_SELECTOR, sel)
                if btn.is_displayed():
                    btn.click()
                    print(f"      🍪 Clicked cookie consent: {sel}")
                    self.browser.random_delay(0.5, 1)
                    return
            except Exception:
                continue
        # Try by text
        for text in ["Accept all", "I agree", "Accept", "Agree", "OK"]:
            try:
                btn = driver.find_element(By.XPATH,
                    f"//button[contains(text(),'{text}')]")
                if btn.is_displayed():
                    btn.click()
                    print(f"      🍪 Clicked cookie consent: {text}")
                    self.browser.random_delay(0.5, 1)
                    return
            except Exception:
                continue

    def _go_to_signup(self):
        self.browser.driver.get(SIGNUP_URL)
        self.browser.random_delay(3, 6)
        self._accept_cookies()  # May show cookie consent on signup page too
        self.browser.random_delay(1, 2)
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

        # ── Gender (Material Design combobox) ──
        # Actual structure found via debug:
        #   <input id="" aria-label="What's your gender?" visible=False> (hidden)
        #   <div id="gender" role="combobox" visible=True> ← THIS is the trigger
        #   <span>Gender</span> ← label
        gender_val = random.choice(["1", "2", "3"])
        gender_labels = {"1": "Female", "2": "Male", "3": "Rather not say"}
        gender_label = gender_labels[gender_val]
        print(f"   ⚧ Selecting gender: {gender_label}")

        gender_triggered = False

        # Strategy 1: #gender div with role=combobox (the VISIBLE trigger)
        for selector in [
            '#gender',
            '[role="combobox"][id*="gender" i]',
            'div[id="gender"]',
            'div[role="combobox"]',
        ]:
            try:
                el = driver.find_element(By.CSS_SELECTOR, selector)
                if el.is_displayed():
                    print(f"   ⚧ Gender trigger: <{el.tag_name}> id={el.get_attribute('id')} "
                          f"role={el.get_attribute('role')} class={el.get_attribute('class')[:40]}")
                    el.click()
                    time.sleep(0.8)
                    gender_triggered = True
                    print(f"   ⚧ Gender dropdown opened via: {selector}")
                    break
            except Exception:
                continue

        if gender_triggered:
            self._select_dropdown_option(gender_label)
        else:
            # Last resort: try typing into the hidden input + arrow keys
            try:
                el = driver.find_element(By.CSS_SELECTOR, '#gender')
                driver.execute_script("arguments[0].click();", el)
                time.sleep(0.8)
                gender_triggered = True
                self._select_dropdown_option(gender_label)
                print("   ⚧ Gender: used JS click fallback")
            except Exception:
                try:
                    el = driver.find_element(By.CSS_SELECTOR,
                        'input[aria-label*="gender" i]')
                    driver.execute_script("arguments[0].removeAttribute('disabled');", el)
                    el.click()
                    time.sleep(0.5)
                    from selenium.webdriver.common.keys import Keys
                    el.send_keys(gender_label)
                    el.send_keys(Keys.ARROW_DOWN)
                    el.send_keys(Keys.ENTER)
                    gender_triggered = True
                    print("   ⚧ Gender: typed + arrow fallback")
                except Exception:
                    print("   ⚠️  Gender selection failed completely")

        self.browser.random_delay(0.5, 1.5)

        # ── Verify page navigated after Next ──
        url_before = self.browser.page_url
        print(f"   📍 URL before Next: {url_before[:80]}...")
        self._click_next()
        time.sleep(3)  # Wait for page navigation

        url_after = self.browser.page_url
        print(f"   📍 URL after Next: {url_after[:80]}...")
        if url_before == url_after:
            print("   ⚠️  Page did NOT navigate! Form may have validation errors.")
            # Check for error messages on the page
            for sel in ['[role="alert"]', '[aria-live="assertive"]',
                       '.error', '[class*="error" i]', '[class*="invalid" i]']:
                try:
                    err = driver.find_element(By.CSS_SELECTOR, sel)
                    if err.is_displayed() and err.text:
                        print(f"   ❌ Validation error: {err.text[:100]}")
                        break
                except Exception:
                    continue
            # Try clicking Next again
            print("   🔄 Retrying Next click...")
            self._click_next()
            time.sleep(3)
            url_retry = self.browser.page_url
            if url_before == url_retry:
                print("   ❌ Still on same page — gender may be required")
                # Try to select gender one more time
                print("   🔄 Attempting gender selection one more time...")
                self._retry_gender_selection(driver, gender_label, gender_val)

    def _retry_gender_selection(self, driver, gender_label: str, gender_val: str):
        """Last resort: brute-force find and click the gender dropdown."""
        from selenium.webdriver.common.by import By
        print("   ══ RETRY GENDER ══")

        # Dump ALL clickable elements to find the gender dropdown
        all_clickable = driver.find_elements(By.XPATH,
            "//*[(self::input or self::div or self::button or self::span or "
            "self::label or self::li or self::ul or self::select) "
            "and @is_displayed() or 1=1]"
        )
        for el in all_clickable:
            try:
                if not el.is_displayed():
                    continue
                tag = el.tag_name
                aria = el.get_attribute("aria-label") or ""
                text = el.text[:40] if el.text else ""
                role = el.get_attribute("role") or ""
                if "gender" in aria.lower() or "gender" in text.lower():
                    print(f"   ⚧ Found: <{tag}> aria={aria} text={text} role={role}")
                    el.click()
                    time.sleep(0.8)
                    # Try to click the option
                    self._select_dropdown_option(gender_label)
                    return
            except Exception:
                continue

        # Try typing into gender input directly
        try:
            el = driver.find_element(By.CSS_SELECTOR,
                'input[aria-label*="gender" i], input[aria-label*="Gender"]')
            el.clear()
            el.send_keys(gender_label)
            print(f"   ⚧ Typed '{gender_label}' into gender input")
            time.sleep(0.5)
            # Press arrow down + enter to select from autocomplete
            from selenium.webdriver.common.keys import Keys
            el.send_keys(Keys.ARROW_DOWN)
            time.sleep(0.3)
            el.send_keys(Keys.ENTER)
            time.sleep(0.3)
        except Exception as e:
            print(f"   ❌ Gender retry failed: {e}")

        print("   ══ END RETRY ══")

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
        from selenium.webdriver.common.by import By
        driver = self.browser.driver

        # Debug: dump current page state before looking for elements
        print("   🔎 Checking current page state...")
        url = self.browser.page_url
        print(f"   📍 URL: {url}")
        body_text = (self.browser.get_page_text() or "")[:500]
        print(f"   📄 Page text preview: {body_text[:200]}")

        # Check if we're on a verification page instead of email step
        if "verify" in url.lower() or "challenge" in url.lower() or "phone" in body_text.lower():
            print("   ⚠️  Phone verification page detected — skipping email step")
            return

        # Try to find email-related elements with multiple strategies
        email_input = None

        # Strategy 1: standard selectors
        for sel in [
            'input[name="Username"]',
            'input[type="email"]',
            '[data-email]',
            'input[aria-label*="username" i]',
            'input[aria-label*="email" i]',
            'input[aria-label*="Gmail" i]',
            'input[placeholder*="username" i]',
            'input[placeholder*="email" i]',
            'input[id*="user" i]',
            'input[id*="email" i]',
        ]:
            try:
                el = driver.find_element(By.CSS_SELECTOR, sel)
                if el.is_displayed():
                    email_input = el
                    print(f"   📧 Email input found via: {sel}")
                    break
            except Exception:
                continue

        # Strategy 2: find by visible text prompts
        if not email_input:
            try:
                # Look for text "Choose your Gmail address" or "Create a Gmail address"
                label = driver.find_element(By.XPATH,
                    "//*[contains(text(),'Gmail address') or "
                    "contains(text(),'username') or "
                    "contains(text(),'email address')]")
                print(f"   📧 Found label: {label.text[:50]}")
            except Exception:
                pass

        # Strategy 3: dump all inputs for debugging
        if not email_input:
            print("   ⚠️  Email input not found — dumping all visible inputs:")
            all_inputs = driver.find_elements(By.TAG_NAME, "input")
            for inp in all_inputs:
                if inp.is_displayed():
                    print(f"      <input type={inp.get_attribute('type')} "
                          f"name={inp.get_attribute('name')} "
                          f"id={inp.get_attribute('id')} "
                          f"aria={inp.get_attribute('aria-label')} "
                          f"placeholder={inp.get_attribute('placeholder')}>")
            # Also dump all buttons and links
            for tag in ["button", "a"]:
                els = driver.find_elements(By.TAG_NAME, tag)
                for el in els:
                    if el.is_displayed() and el.text:
                        print(f"      <{tag}> text={el.text[:50]}")

            raise RuntimeError("❌ Cannot find email/username input on page")

        # ── Try suggestion first (radio buttons or data-email) ──
        try:
            suggestion = driver.find_element(By.CSS_SELECTOR, '[data-email]')
            if suggestion and suggestion.is_displayed():
                self.email = suggestion.get_attribute("data-email")
                self.username = self.email.split("@")[0]
                suggestion.click()
                self.browser.random_delay(0.5, 1.0)
                self._click_next()
                return
        except Exception:
            pass

        # ── Try radio button suggestions (Google sometimes offers suggestions) ──
        try:
            radios = driver.find_elements(By.CSS_SELECTOR, 'input[type="radio"]')
            if radios:
                # Pick first suggestion
                radios[0].click()
                self.browser.random_delay(0.5, 1.0)
                self._click_next()
                return
        except Exception:
            pass

        # ── Custom username ──
        self.username = self._generate_username()
        self.email = f"{self.username}@gmail.com"
        print(f"   📧 Trying username: {self.username}")

        email_input.click()
        time.sleep(random.uniform(0.2, 0.5))
        email_input.clear()
        email_input.send_keys(self.username)
        self.browser.random_delay(0.5, 1.0)
        self._click_next()

        # Check if username is taken
        time.sleep(2)
        error = None
        for sel in ['[aria-live="assertive"]', '[role="alert"]',
                    '.error', '.ErrorMessage', 'div[class*="error" i]']:
            try:
                error = driver.find_element(By.CSS_SELECTOR, sel)
                if error.is_displayed() and error.text:
                    break
                error = None
            except Exception:
                continue

        if error and ("taken" in (error.text or "").lower()
                      or "already" in (error.text or "").lower()
                      or "available" not in (error.text or "").lower()):
            print(f"   ⚠️  Username taken: {error.text[:50]}")
            self.username = f"{self.username}{random.randint(100, 999)}"
            self.email = f"{self.username}@gmail.com"
            print(f"   📧 Retrying with: {self.username}")
            email_input.clear()
            email_input.send_keys(self.username)
            self.browser.random_delay(0.5, 1.0)
            self._click_next()
        elif error:
            print(f"   ℹ️  Info: {error.text[:80]}")

    def _create_password(self):
        self.password = self._generate_password()
        driver = self.browser.driver

        # Debug: dump page state
        print(f"   🔎 Looking for password fields...")
        url = self.browser.page_url
        print(f"   📍 URL: {url}")

        # Find password input with multiple strategies
        pwd = None
        for sel in ['input[name="Passwd"]', 'input[type="password"]',
                    'input[aria-label*="password" i]',
                    'input[aria-label*="Password" i]',
                    'input[placeholder*="password" i]',
                    'input[id*="pass" i]']:
            try:
                el = driver.find_element(By.CSS_SELECTOR, sel)
                if el.is_displayed():
                    pwd = el
                    print(f"   🔐 Password input found via: {sel}")
                    break
            except Exception:
                continue

        if not pwd:
            # Dump all inputs for debugging
            print("   ⚠️  Password input not found — dumping all visible inputs:")
            for inp in driver.find_elements(By.TAG_NAME, "input"):
                if inp.is_displayed():
                    print(f"      <input type={inp.get_attribute('type')} "
                          f"name={inp.get_attribute('name')} "
                          f"aria={inp.get_attribute('aria-label')}>")
            raise RuntimeError("❌ Cannot find password input on page")

        pwd.click()
        time.sleep(random.uniform(0.2, 0.5))
        pwd.send_keys(self.password)
        print(f"   🔐 Password entered")
        self.browser.random_delay(0.3, 0.8)

        # Find confirm password input
        confirm = None
        for sel in ['input[name="PasswdAgain"]', 'input[name="ConfirmPasswd"]',
                    'input[aria-label*="confirm" i]',
                    'input[aria-label*="re-enter" i]',
                    'input[aria-label*="again" i]',
                    'input[type="password"]']:  # second password field
            try:
                el = driver.find_element(By.CSS_SELECTOR, sel)
                if el.is_displayed() and el != pwd:
                    confirm = el
                    print(f"   🔐 Confirm password found via: {sel}")
                    break
            except Exception:
                continue

        if confirm:
            confirm.click()
            time.sleep(random.uniform(0.2, 0.5))
            confirm.send_keys(self.password)

        self.browser.random_delay(0.5, 1.0)
        self._click_next()

    def _handle_verification(self) -> bool:
        """Handle verification page — try to skip phone verification."""
        from selenium.webdriver.common.by import By
        driver = self.browser.driver

        time.sleep(3)
        url = self.browser.page_url
        print(f"   📍 Verification URL: {url[:80]}...")

        # Check if we're actually on a welcome/account page (no verification needed)
        body = self.browser.get_page_text().lower()
        if any(kw in url.lower() for kw in ["myaccount", "mail.google", "welcome"]):
            print("   ✅ No verification needed — already on account page")
            return True
        if any(kw in body for kw in ["welcome", "congratulations", "you're all set"]):
            print("   ✅ No verification needed — welcome page detected")
            return True

        # ── Strategy 1: Try to SKIP verification entirely ──
        print("   🔄 Attempting to skip phone verification...")
        for attempt in range(MAX_VERIFICATION_RETRIES):
            print(f"   📱 Attempt {attempt + 1}/{MAX_VERIFICATION_RETRIES}")

            # Try "Skip" button first
            for skip_text in ["Skip", "Skip this step", "Not now", "Use without",
                              "No thanks", "I'll do this later", "Confirm",
                              "Skip phone number"]:
                try:
                    btn = driver.find_element(By.XPATH,
                        f"//button[contains(text(),'{skip_text}')] | "
                        f"//div[@role='button'][contains(text(),'{skip_text}')] | "
                        f"//span[contains(text(),'{skip_text}')]"
                        f"/ancestor::*[@role='button' or self::button]"
                    )
                    if btn.is_displayed():
                        print(f"   ✅ Found skip option: '{skip_text}'")
                        btn.click()
                        self.browser.random_delay(2, 4)
                        # Check if we moved past verification
                        new_url = self.browser.page_url
                        new_body = self.browser.get_page_text().lower()
                        if any(kw in new_url.lower() for kw in ["myaccount", "welcome", "mail"]):
                            print("   ✅ Verification skipped successfully!")
                            return True
                        if any(kw in new_body for kw in ["welcome", "congratulations"]):
                            print("   ✅ Verification skipped successfully!")
                            return True
                except Exception:
                    continue

            # Try "Try another way" to get alternative options
            for alt_text in ["Try another way", "Other options", "More options"]:
                try:
                    btn = driver.find_element(By.XPATH,
                        f"//button[contains(text(),'{alt_text}')] | "
                        f"//div[@role='button'][contains(text(),'{alt_text}')] | "
                        f"//a[contains(text(),'{alt_text}')]"
                    )
                    if btn.is_displayed():
                        print(f"   🔄 Clicking: '{alt_text}'")
                        btn.click()
                        self.browser.random_delay(2, 3)
                        break
                except Exception:
                    continue

            # After clicking "Try another way", check for skip options
            time.sleep(2)

            # Try "Add recovery email" instead of phone
            for recovery_text in ["Add recovery email", "recovery email"]:
                try:
                    btn = driver.find_element(By.XPATH,
                        f"//*[contains(text(),'{recovery_text}')]"
                        f"/ancestor::*[@role='button' or self::button or self::a]"
                    )
                    if btn.is_displayed():
                        print(f"   📧 Found: '{recovery_text}' — using this instead")
                        btn.click()
                        self.browser.random_delay(1, 2)
                        # Fill recovery email (we can use a fake one)
                        try:
                            rec_input = driver.find_element(By.CSS_SELECTOR,
                                'input[type="email"]')
                            if rec_input.is_displayed():
                                fake_email = f"{self.username}@gmail.com"
                                rec_input.send_keys(fake_email)
                                self.browser.random_delay(0.5, 1)
                                self._click_next()
                                time.sleep(3)
                                return True
                        except Exception:
                            pass
                except Exception:
                    continue

            # Check if we moved to next step anyway
            url = self.browser.page_url
            body = self.browser.get_page_text().lower()
            if any(kw in url.lower() for kw in ["myaccount", "welcome", "mail"]):
                return True
            if any(kw in body for kw in ["welcome", "congratulations"]):
                return True

            print(f"   ⚠️  Attempt {attempt + 1} — no skip option found, retrying...")
            time.sleep(2)

        # ── Strategy 2: If all skip attempts failed, use SMS service ──
        print("   📱 Skip failed — attempting SMS verification...")
        return self._process_verification()

    def _process_verification(self) -> bool:
        """Process phone verification using SMS service."""
        from selenium.webdriver.common.by import By
        driver = self.browser.driver

        try:
            # First try: get SMS number from provider
            sms_data = self.sms_verifier.get_number()
            if not sms_data:
                print("   ❌ No SMS number available")
                return False

            phone = sms_data["number"]
            sms_id = sms_data["id"]
            print(f"   📱 Using phone: {phone}")

            # Find phone input
            phone_input = None
            for sel in ['input[type="tel"]', 'input[name="phoneNumber"]',
                        'input[aria-label*="phone" i]',
                        'input[aria-label*="Phone" i]',
                        'input[placeholder*="phone" i]']:
                try:
                    el = driver.find_element(By.CSS_SELECTOR, sel)
                    if el.is_displayed():
                        phone_input = el
                        print(f"   📱 Phone input found via: {sel}")
                        break
                except Exception:
                    continue

            if not phone_input:
                print("   ❌ Phone input not found")
                return False

            phone_input.click()
            time.sleep(0.5)
            phone_input.send_keys(phone)
            self.browser.random_delay(0.5, 1.0)
            self._click_next()
            time.sleep(3)

            # Wait for SMS code
            try:
                print("   ⏳ Waiting for SMS code...")
                code = self.sms_verifier.get_code(sms_id, timeout=120)
                print(f"   📨 Received code: {code}")

                # Find code input
                code_input = None
                for sel in ['input[type="tel"]', 'input[type="number"]',
                            'input[name="smsUserPin"]',
                            'input[aria-label*="code" i]',
                            'input[aria-label*="Code" i]',
                            'input[placeholder*="code" i]']:
                    try:
                        el = driver.find_element(By.CSS_SELECTOR, sel)
                        if el.is_displayed():
                            code_input = el
                            break
                    except Exception:
                        continue

                if code_input:
                    code_input.click()
                    time.sleep(0.3)
                    code_input.send_keys(code)
                    self.browser.random_delay(0.5, 1.0)
                    self._click_next()
                    time.sleep(3)
                    return True
                else:
                    print("   ❌ Code input not found")

            except TimeoutError:
                print("   ⏰ SMS timeout")
                self.sms_verifier.cancel_number(sms_id)
            except Exception as e:
                print(f"   ❌ SMS error: {e}")
                try:
                    self.sms_verifier.cancel_number(sms_id)
                except Exception:
                    pass

            return False
        except Exception as e:
            print(f"   ⚠️ Verification error: {e}")
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
        driver = self.browser.driver

        # Strategy 0: known Google signup Next button IDs
        for sel in ['#birthdaygenderNext', '#firstNameNext',
                    '[id$="Next"]', '[id*="next" i]']:
            try:
                btn = driver.find_element(By.CSS_SELECTOR, sel)
                if btn.is_displayed():
                    btn.click()
                    print(f"   ▶️ Clicked Next via ID: {sel}")
                    self.browser.random_delay(1, 2)
                    return
            except Exception:
                continue

        # Strategy 1: find button with "Next" or "Continue" text
        for text in ["Next", "Continue"]:
            try:
                btn = driver.find_element(By.XPATH,
                    f"//button[contains(text(),'{text}')] | "
                    f"//div[@role='button'][contains(text(),'{text}')] | "
                    f"//span[contains(text(),'{text}')]//ancestor::*[@role='button' or self::button] | "
                    f"//a[contains(text(),'{text}')] | "
                    f"//input[@type='submit'][contains(@value,'{text}')]"
                )
                if btn.is_displayed():
                    btn.click()
                    print(f"   ▶️ Clicked: {text}")
                    self.browser.random_delay(1, 2)
                    return
            except Exception:
                continue
        # Strategy 2: find by CSS
        for sel in ['button[type="submit"]', 'div[role="button"]', 'button']:
            try:
                btn = driver.find_element(By.CSS_SELECTOR, sel)
                if btn.is_displayed() and btn.text:
                    btn.click()
                    print(f"   ▶️ Clicked button: {btn.text[:30]}")
                    self.browser.random_delay(1, 2)
                    return
            except Exception:
                continue
        # Strategy 3: press Enter as last resort
        print("   ▶️ No button found, pressing Enter")
        driver.find_element(By.TAG_NAME, "body").send_keys("\n")
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
