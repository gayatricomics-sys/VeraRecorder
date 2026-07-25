import time
import random
import urllib.parse
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import WebDriverException, StaleElementReferenceException

class AutoCrawler:
    def __init__(self, driver, max_steps=5):
        self.driver = driver
        self.max_steps = max_steps
        self.filled_elements = set()

    def crawl(self):
        print(f"Starting autonomous crawl... max steps: {self.max_steps}")
        steps = 0
        
        while steps < self.max_steps:
            time.sleep(2) # Wait for page and JS injections to settle
            try:
                # 1. Find text/password/email inputs and fill them (one at a time)
                inputs = self.driver.find_elements(By.TAG_NAME, "input")
                filled_any = False
                filled_form = None
                for inp in inputs:
                    if not inp.is_displayed():
                        continue
                    
                    input_name = inp.get_attribute("name") or ""
                    input_id = inp.get_attribute("id") or ""
                    identifier = f"{input_name}_{input_id}"
                    
                    # Prevent duplicate fills by checking if we already marked this element
                    if inp.get_attribute("data-autocrawler-filled") == "true":
                        continue
                    if identifier != "_" and identifier in self.filled_elements:
                        continue
                    
                    # Only fill empty inputs so we don't repeatedly fill the same one
                    # Use get_property to read the current DOM state instead of HTML attribute
                    current_val = inp.get_property("value")
                    if current_val and str(current_val).strip() != "":
                        continue
                        
                    input_type = inp.get_attribute("type")
                    if input_type in ["text", "email", "password", "uid"]:
                        value = "admin" if input_type == "uid" else "testuser"
                        if input_type == "email":
                            value = "test@example.com"
                        elif input_type == "password":
                            value = "admin"
                            
                        # Clear and send keys
                        try:
                            inp.clear()
                            inp.send_keys(value)
                            # Mark in the actual DOM so it survives element re-fetches
                            self.driver.execute_script("arguments[0].setAttribute('data-autocrawler-filled', 'true');", inp)
                            if identifier != "_":
                                self.filled_elements.add(identifier)
                                
                            # Keep track of the form this input belongs to
                            try:
                                filled_form = inp.find_element(By.XPATH, "./ancestor::form")
                            except Exception:
                                filled_form = None
                                
                            filled_any = True
                            time.sleep(0.5) # Slight pause to simulate typing cadence
                            break # Once one input is filled, go to the next things on the page
                        except Exception as e:
                            print(f"Crawler error filling input: {e}")

                # 2. If we filled forms, look for a submit button
                if filled_any:
                    print("Filled forms, looking for submit button...")
                    
                    if filled_form:
                        buttons = filled_form.find_elements(By.TAG_NAME, "input") + filled_form.find_elements(By.TAG_NAME, "button")
                    else:
                        buttons = self.driver.find_elements(By.TAG_NAME, "input") + self.driver.find_elements(By.TAG_NAME, "button")
                        
                    submit_btn = None
                    for b in buttons:
                        b_type = b.get_attribute("type")
                        b_value = b.get_attribute("value") or ""
                        b_name = b.get_attribute("name") or ""
                        if not b.is_displayed():
                            continue
                            
                        if b_type == "submit" or "login" in b_value.lower() or "submit" in b_name.lower():
                            submit_btn = b
                            break
                            
                    if submit_btn:
                        print("Clicking submit button.")
                        submit_btn.click()
                        steps += 1
                        continue # Start next loop since page likely navigated
                    else:
                        print("Filled input but no submit button found yet. Continuing to next input...")
                        continue # Start next loop to fill other inputs
                
                # 3. If no forms filled, let's look for navigation links
                print("Looking for links to navigate...")
                
                # Get current origin to restrict crawling
                current_url = self.driver.current_url
                current_domain = urllib.parse.urlparse(current_url).netloc
                
                links = self.driver.find_elements(By.TAG_NAME, "a")
                valid_links = []
                for l in links:
                    if l.is_displayed():
                        href = l.get_attribute("href")
                        if href:
                            href_domain = urllib.parse.urlparse(href).netloc
                            
                            # Determine base domains by stripping www.
                            base_current = current_domain[4:] if current_domain.startswith("www.") else current_domain
                            base_href = href_domain[4:] if href_domain.startswith("www.") else href_domain
                            
                            # Allow if same domain, parent domain, or subdomain
                            is_allowed = (
                                not href_domain or 
                                base_href == base_current or 
                                base_href.endswith("." + base_current) or 
                                base_current.endswith("." + base_href)
                            )
                            
                            if is_allowed:
                                valid_links.append(l)
                
                
                if valid_links:
                    link_to_click = random.choice(valid_links)
                    print(f"Clicking link: {link_to_click.get_attribute('href')}")
                    link_to_click.click()
                    steps += 1
                else:
                    print("No interactable elements found. Stopping crawl.")
                    break
                    
            except StaleElementReferenceException:
                print("Page navigating... continuing crawl loop.")
            except WebDriverException as e:
                print(f"WebDriver exception during crawl: {e}")
                break
                
        print("Autonomous crawl finished.")
