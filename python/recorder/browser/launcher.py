import os
import sys

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options


def _driver_name() -> str:
    return "chromedriver.exe" if sys.platform == "win32" else "chromedriver"


def find_bundled_chromedriver():
    """Locate a ChromeDriver shipped with the app so no download is needed.

    Without this, Selenium Manager downloads ChromeDriver from the internet on
    first launch, which fails on offline machines.

    Search order:
      1. VERARECORDER_CHROMEDRIVER env var (full path to the driver)
      2. next to the packaged backend executable (PyInstaller build)
      3. python/drivers/ when running from source
    """
    override = os.environ.get("VERARECORDER_CHROMEDRIVER")
    if override and os.path.isfile(override):
        return override

    candidates = []
    if getattr(sys, "frozen", False):
        exe_dir = os.path.dirname(sys.executable)
        candidates.append(os.path.join(exe_dir, _driver_name()))
        candidates.append(os.path.join(exe_dir, "drivers", _driver_name()))
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    candidates.append(os.path.join(base_dir, "drivers", _driver_name()))

    for path in candidates:
        if os.path.isfile(path):
            return path
    return None


def find_bundled_chrome():
    """Locate a Chrome for Testing build shipped with the app (optional).

    ChromeDriver only works with the same Chrome major version, and offline
    machines rarely get Chrome updates, so shipping a matched Chrome + driver
    pair is the reliable option. If none is bundled, the installed Chrome is used.
    """
    override = os.environ.get("VERARECORDER_CHROME")
    if override and os.path.isfile(override):
        return override

    if sys.platform == "win32":
        rel = os.path.join("chrome", "chrome.exe")
    elif sys.platform == "darwin":
        rel = os.path.join("chrome", "Google Chrome for Testing.app", "Contents", "MacOS", "Google Chrome for Testing")
    else:
        rel = os.path.join("chrome", "chrome")

    candidates = []
    if getattr(sys, "frozen", False):
        candidates.append(os.path.join(os.path.dirname(sys.executable), rel))
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    candidates.append(os.path.join(base_dir, "drivers", rel))
    for path in candidates:
        if os.path.isfile(path):
            return path
    return None


class BrowserLauncher:
    def __init__(self):
        self.driver = None

    def launch_chrome(self, url: str):
        chrome_options = Options()
        chrome_options.add_argument("--disable-web-security")
        chrome_options.add_argument("--allow-running-insecure-content")
        # Test/staging apps scanned by DAST often use self-signed or expired
        # certificates; without this Chrome stops on a "Privacy error" page and
        # nothing can be recorded. This browser is only used for recording.
        chrome_options.add_argument("--ignore-certificate-errors")
        chrome_options.set_capability("acceptInsecureCerts", True)
        # Enable CDP for listening to DOM events
        chrome_options.set_capability("goog:loggingPrefs", {"performance": "ALL"})

        chrome_path = find_bundled_chrome()
        if chrome_path:
            print(f"Using bundled Chrome: {chrome_path}")
            chrome_options.binary_location = chrome_path

        driver_path = find_bundled_chromedriver()
        if driver_path:
            print(f"Using bundled ChromeDriver: {driver_path}")
            self.driver = webdriver.Chrome(service=Service(executable_path=driver_path), options=chrome_options)
        else:
            # Falls back to Selenium Manager (needs internet the first time).
            print("No bundled ChromeDriver found; falling back to Selenium Manager")
            self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.get(url)
        return self.driver

    def close(self):
        if self.driver:
            try:
                self.driver.quit()
            finally:
                self.driver = None
