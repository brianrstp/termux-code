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
        # Google's gender field is <input type=text aria-label="What's your gender?">
        # It's a custom dropdown — clicking opens a list of options
        gender_val = random.choice(["1", "2", "3"])
        gender_labels = {"1": "Female", "2": "Male", "3": "Rather not say"}
        gender_label = gender_labels[gender_val]
        print(f"   ⚧ Selecting gender: {gender_label}")

        # Debug: dump ALL elements with "gender" in any attribute
        print("   🔎 Scanning for gender elements...")
        for tag in ["input", "div", "button", "span", "select", "li", "ul"]:
            try:
                els = driver.find_elements(By.TAG_NAME, tag)
                for el in els:
                    name = el.get_attribute("name") or ""
                    aid = el.get_attribute("id") or ""
                    aria = el.get_attribute("aria-label") or ""
                    role = el.get_attribute("role") or ""
                    cls = el.get_attribute("class") or ""
                    txt = el.text[:30] if el.text else ""
                    if ("gender" in name.lower() or "gender" in aid.lower()
                            or "gender" in aria.lower() or "gender" in role.lower()
                            or "gender" in cls.lower() or "gender" in txt.lower()):
                        print(f"      <{tag}> name={name} id={aid} aria={aria} "
                              f"role={role} class={cls[:40]} text={txt} "
                              f"visible={el.is_displayed()}")
            except Exception:
                continue

        gender_triggered = False

        # Strategy 1: aria-label containing "gender"
        for selector in [
            '[aria-label*="gender" i]',
            '[aria-label*="Gender"]',
            '#gender',
            '[name*="gender" i]',
            '[id*="gender" i]',
        ]:
            try:
                el = driver.find_element(By.CSS_SELECTOR, selector)
                displayed = el.is_displayed()
                tag_name = el.tag_name
                print(f"   ⚧ Found via {selector}: <{tag_name}> displayed={displayed}")
                # Click even if not fully displayed — Material Design may still respond
                el.click()
                time.sleep(0.8)
                gender_triggered = True
                print(f"   ⚧ Gender trigger clicked via: {selector}")
                break
            except Exception as e:
                continue

        # Strategy 2: find div/button/label with "gender" text
        if not gender_triggered:
            try:
                el = driver.find_element(By.XPATH,
                    "//*[contains(text(),'gender') or contains(text(),'Gender') or "
                    "contains(@aria-label,'gender') or contains(@aria-label,'Gender')]"
                )
                print(f"   ⚧ Found gender element via text: <{el.tag_name}> text={el.text[:30]}")
                el.click()
                time.sleep(0.8)
                gender_triggered = True
            except Exception:
                pass

        if gender_triggered:
            self._select_dropdown_option(gender_label)

            # Verify gender was selected by checking if dropdown closed
            time.sleep(0.5)
            # Try to find the selected value in the input
            try:
                for sel in ['[aria-label*="gender" i]', '[name*="gender" i]',
                           '#gender', '[id*="gender" i]']:
                    el = driver.find_element(By.CSS_SELECTOR, sel)
                    val = el.get_attribute("value") or ""
                    if val:
                        print(f"   ⚧ Gender field value: {val}")
                        break
            except Exception:
                pass
        else:
            # Last resort: try native select
            try:
                from selenium.webdriver.support.ui import Select
                sel = driver.find_element(By.CSS_SELECTOR,
                    'select[name*="gender" i], select[id*="gender" i], select')
                Select(sel).select_by_value(gender_val)
                print("   ⚧ Gender: used native <select> fallback")
            except Exception:
                print("   ⚠️  Gender element not found — form may reject submission")
                print("   ⚠️  Trying to continue anyway...")

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
        driver = self.browser.driver
        # Strategy 1: find button/link with "Next" text
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
