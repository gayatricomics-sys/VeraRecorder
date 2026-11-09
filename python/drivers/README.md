# Bundled ChromeDriver

Put `chromedriver.exe` (Windows) or `chromedriver` (macOS/Linux) here.
The backend uses it instead of downloading one, so recording works offline.

**The ChromeDriver major version must match the Chrome installed on the
target machine** (e.g. ChromeDriver 142.x for Chrome 142.x). The
`offline/prepare-offline-kit` script downloads a matching pair from
Chrome for Testing. You can also point to a driver anywhere with the
`VERARECORDER_CHROMEDRIVER` environment variable.
