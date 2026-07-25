from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import time

class BrowserLauncher:
    def __init__(self):
        self.driver = None

    def launch_chrome(self, url: str):
        chrome_options = Options()
        chrome_options.add_argument("--disable-web-security")
        chrome_options.add_argument("--allow-running-insecure-content")
        # Enable CDP for listening to DOM events
        chrome_options.set_capability("goog:loggingPrefs", {"performance": "ALL"})
        
        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.get(url)
        return self.driver

    def close(self):
        if self.driver:
            self.driver.quit()
            self.driver = None
