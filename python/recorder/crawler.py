import random
import re
import time
import urllib.parse

from selenium.common.exceptions import StaleElementReferenceException, WebDriverException
from selenium.webdriver.common.by import By

# Links that would end the session being crawled (and so break a login script).
_LOGOUT = re.compile(r"log\s*-?\s*out|sign\s*-?\s*out|logoff|sign\s*off|abmelden|déconnexion", re.I)
# Fill values by input type. Values only need to be plausible for a crawl.
_VALUES = {"email": "test@example.com", "password": "admin", "uid": "admin",
           "tel": "5550100", "number": "1", "url": "https://example.com", "search": "test"}
_FILLABLE = {"text", "email", "password", "uid", "search", "tel", "number", "url"}


class AutoCrawler:
    def __init__(self, driver, max_steps=5, max_errors=5):
        self.driver = driver
        self.max_steps = max_steps
        self.max_errors = max_errors
        self.filled_elements = set()
        self.visited = set()

    def crawl(self):
        print(f"Starting autonomous crawl... max steps: {self.max_steps}")
        steps = errors = 0
        while steps < self.max_steps and errors < self.max_errors:
            time.sleep(2)  # let the page and the recorder script settle
            try:
                if self._fill_and_submit() or self._click_link():
                    steps += 1
                    errors = 0
                else:
                    print("No interactable elements found. Stopping crawl.")
                    break
            except StaleElementReferenceException:
                # The page navigated while we looked at it; count it so a page
                # that keeps changing cannot loop forever.
                errors += 1
            except WebDriverException as e:
                if not self._browser_alive():
                    print("Browser closed; stopping crawl.")
                    break
                errors += 1
                print(f"Crawl step failed ({errors}/{self.max_errors}): {str(e).splitlines()[0][:160]}")
            except Exception as e:  # e.g. connection refused once Chrome is gone
                print(f"Crawl stopped: {e!r}")
                break
        print("Autonomous crawl finished.")

    # -- steps ------------------------------------------------------------
    def _fill_and_submit(self) -> bool:
        """Fill one empty visible input, then submit its form if there is a button."""
        for inp in self.driver.find_elements(By.TAG_NAME, "input"):
            if not inp.is_displayed() or not inp.is_enabled():
                continue
            input_type = (inp.get_attribute("type") or "text").lower()
            if input_type not in _FILLABLE:
                continue
            identifier = f"{inp.get_attribute('name') or ''}_{inp.get_attribute('id') or ''}"
            if inp.get_attribute("data-autocrawler-filled") == "true":
                continue
            if identifier != "_" and identifier in self.filled_elements:
                continue
            if str(inp.get_property("value") or "").strip():
                continue  # only fill empty inputs

            inp.clear()
            inp.send_keys(_VALUES.get(input_type, "testuser"))
            # Mark in the DOM so it survives element re-fetches.
            self.driver.execute_script("arguments[0].setAttribute('data-autocrawler-filled', 'true');", inp)
            if identifier != "_":
                self.filled_elements.add(identifier)
            time.sleep(0.5)

            try:
                form = inp.find_element(By.XPATH, "./ancestor::form")
            except WebDriverException:
                form = None
            scope = form or self.driver
            for b in scope.find_elements(By.CSS_SELECTOR, "button, input[type=submit], input[type=image]"):
                if not b.is_displayed() or not b.is_enabled():
                    continue
                b_type = (b.get_attribute("type") or "submit").lower()
                label = " ".join(filter(None, [b.get_attribute("value"), b.get_attribute("name"), b.text]))
                if b_type in ("submit", "image") or re.search(r"login|log in|sign in|submit|go|search", label, re.I):
                    if _LOGOUT.search(label):
                        continue
                    print("Filled input, clicking submit button.")
                    b.click()
                    return True
            # Filled a field but found no button yet: keep going on this page.
            return True
        return False

    def _click_link(self) -> bool:
        current = urllib.parse.urlparse(self.driver.current_url)
        base_current = current.netloc[4:] if current.netloc.startswith("www.") else current.netloc
        candidates = []
        for a in self.driver.find_elements(By.TAG_NAME, "a"):
            if not a.is_displayed():
                continue
            href = a.get_attribute("href") or ""
            parsed = urllib.parse.urlparse(href)
            if parsed.scheme not in ("http", "https"):
                continue  # mailto:, tel:, javascript:, ...
            if _LOGOUT.search(href) or _LOGOUT.search(a.text or ""):
                continue
            base_href = parsed.netloc[4:] if parsed.netloc.startswith("www.") else parsed.netloc
            same_site = (base_href == base_current or base_href.endswith("." + base_current)
                         or base_current.endswith("." + base_href))
            if same_site:
                candidates.append((href.split("#")[0], a))
        if not candidates:
            return False
        # Prefer pages not visited yet.
        fresh = [c for c in candidates if c[0] not in self.visited] or candidates
        href, link = random.choice(fresh)
        self.visited.add(href)
        print(f"Clicking link: {href}")
        try:
            link.click()
        except WebDriverException:
            # Covered by an overlay or similar; click it the way a script would.
            self.driver.execute_script("arguments[0].click();", link)
        return True

    def _browser_alive(self) -> bool:
        try:
            return len(self.driver.window_handles) > 0
        except Exception:
            return False
