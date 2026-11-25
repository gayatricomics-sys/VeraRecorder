from recorder.browser.launcher import BrowserLauncher
from recorder.cdp_bridge import CdpRecorderBridge, BINDING_NAME
from recorder.locator.engine import LocatorEngine


class NavigationError(Exception):
    """The start page could not be loaded (the browser is still open)."""


class RecorderEngine:
    def __init__(self, ws_manager):
        self.browser = BrowserLauncher()
        self.locator_engine = LocatorEngine()
        self.ws_manager = ws_manager
        self.driver = None
        self.is_recording = False
        self.bridge = None
        self.start_url = None
        # Set by the API: called with {"command", "target", "value"} for every
        # recorded step. Without it, steps are only delivered via HTTP fallback.
        self.on_event = None

    def start_recording(self, url: str, fallback_url: str = None):
        """Open Chrome on ``url`` and start recording.

        ``fallback_url`` is tried if ``url`` cannot be loaded (used when the
        user typed no scheme: https:// is guessed first, then http://).
        Raises NavigationError if the page cannot be opened; the browser stays
        open and recording, so the user can fix the address there.
        """
        print(f"Starting recording on {url}")
        if self.driver:
            # Don't orphan a previous Chrome session.
            self.stop_recording()
        self.driver = self.browser.launch_chrome()
        self.is_recording = True
        self._setup_recording()
        self._navigate(url, fallback_url)

    def _navigate(self, url, fallback_url=None):
        # The address that really opened (with its scheme), used for exports.
        self.start_url = url
        first_error = self._load(url)
        if first_error is None:
            return
        if fallback_url:
            print(f"{url} failed ({first_error}); trying {fallback_url}")
            if self._load(fallback_url) is None:
                self.start_url = fallback_url
                return
        raise NavigationError(f"Could not open {url}: {first_error}. The browser is open; "
                              "check the address there or in the URL field.")

    def _load(self, url):
        """Navigate; return None on success or a short error message.

        Chrome often shows its own error page ("This site can't be reached")
        without Selenium raising, so the resulting address is checked too."""
        from selenium.common.exceptions import WebDriverException
        try:
            self.driver.get(url)
        except WebDriverException as e:
            text = e.msg or str(e) or repr(e)
            return text.splitlines()[0]
        try:
            # current_url keeps the requested address; the error page is only
            # visible in document.URL.
            if str(self.driver.execute_script("return document.URL")).startswith("chrome-error://"):
                return "the site could not be reached"
        except WebDriverException:
            pass
        return None

    def _setup_recording(self):
        # The page calls window.__vrRecord (== cdp_bridge.BINDING_NAME).
        injection_script = r"""
        (function() {
            if (window.__verarecorder_injected) return;
            window.__verarecorder_injected = true;
            
            function sendEvent(command, target, value) {
                const payload = JSON.stringify({ command, target, value, confidence: 0.95 });
                // Preferred: CDP binding. Travels over the DevTools connection,
                // so the site's Content-Security-Policy cannot block it.
                if (typeof window.__vrRecord === 'function') {
                    window.__vrRecord(payload);
                    return;
                }
                // Fallback (only if the DevTools bridge could not start).
                fetch('http://127.0.0.1:8000/api/record', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    keepalive: true,
                    body: payload
                }).catch(e => console.error("VeraRecorder Sync Error:", e));
            }

            // Escape a value for use inside a double-quoted CSS attribute selector.
            function cssq(v) { return String(v).replace(/\\/g, '\\\\').replace(/"/g, '\\"'); }
            function count(sel) { try { return document.querySelectorAll(sel).length; } catch (_) { return 0; } }

            // Pick a locator that matches exactly ONE element, so replay acts on
            // the same element: name=, then id=, then name+value (radio buttons,
            // several submit buttons sharing a name), then an XPath.
            function locatorFor(el) {
                const tag = el.tagName.toLowerCase();
                const name = el.getAttribute && el.getAttribute('name');
                if (name && count(tag + '[name="' + cssq(name) + '"]') === 1 && document.getElementsByName(name).length === 1)
                    return 'name=' + name;
                // ids containing digits are often generated per page load
                if (el.id && !/\d/.test(el.id) && count('[id="' + cssq(el.id) + '"]') === 1)
                    return 'id=' + el.id;
                if (name && el.value != null && el.value !== '') {
                    const sel = tag + '[name="' + cssq(name) + '"][value="' + cssq(el.value) + '"]';
                    if (count(sel) === 1) return 'css=' + sel;
                }
                return 'xpath=' + getXPath(el);
            }

            const CLICKABLE = 'button, a, input, select, textarea, summary, [role="button"], [role="link"], [role="menuitem"], [role="tab"], [role="checkbox"], [onclick]';
            const NO_TYPE = ['checkbox', 'radio', 'file', 'submit', 'button', 'reset', 'image'];

            document.addEventListener('click', (e) => {
                let el = e.target;
                if (!el || el.nodeType !== 1) return;
                // Clicking a <label> makes the browser also click its control
                // (checkbox/radio/input); record only that click, or replay would
                // toggle it twice.
                const label = el.closest('label');
                if (label && label.control && el !== label.control && !label.control.contains(el)) return;
                // Record the interactive element (the <button>, not a <span> in it).
                el = el.closest(CLICKABLE) || el;
                const tag = el.tagName.toLowerCase();
                // Opening a dropdown is not a step; the 'select' below is.
                if (tag === 'select' || tag === 'option') return;
                sendEvent('click', locatorFor(el), '');
            }, true);

            document.addEventListener('change', (e) => {
                const el = e.target;
                if (!el || el.nodeType !== 1) return;
                const tag = el.tagName.toLowerCase();
                if (tag === 'select') {
                    const opt = el.options[el.selectedIndex];
                    sendEvent('select', locatorFor(el), 'label=' + (opt ? opt.text : ''));
                    return;
                }
                // Checkboxes/radios/buttons are recorded by their click; a 'type'
                // step for them ("on") would fail on replay.
                if (tag === 'input' && NO_TYPE.indexOf((el.type || '').toLowerCase()) !== -1) return;
                if (tag === 'input' || tag === 'textarea' || el.isContentEditable)
                    sendEvent('type', locatorFor(el), el.isContentEditable ? el.innerText : el.value);
            }, true);

            // Absolute XPath (e.g. //*[@id="main"]/div[2]/a[1] or /html/body/div[1]).
            // The old version returned "BODY/DIV[1]", a relative path that
            // matches nothing when evaluated against the document.
            function getXPath(elm) {
                if (!elm || elm.nodeType !== 1) return '';
                if (elm.id && !/["']/.test(elm.id)) return '//*[@id="' + elm.id + '"]';
                if (elm === document.documentElement) return '/html';
                if (elm === document.body) return '/html/body';
                let parent = elm.parentNode;
                if (!parent || parent.nodeType !== 1) return '/' + elm.tagName.toLowerCase();
                let ix = 0;
                let siblings = parent.childNodes;
                for (let i = 0; i < siblings.length; i++) {
                    let sibling = siblings[i];
                    if (sibling === elm) return getXPath(parent) + '/' + elm.tagName.toLowerCase() + '[' + (ix + 1) + ']';
                    if (sibling.nodeType === 1 && sibling.tagName === elm.tagName) ix++;
                }
                return '';
            }
        })();
        """
        assert BINDING_NAME == "__vrRecord"
        # Preferred path: our own DevTools connection installs the script and
        # the binding in every tab and receives each recorded step directly.
        try:
            address = self.driver.capabilities["goog:chromeOptions"]["debuggerAddress"]
            self.bridge = CdpRecorderBridge(address, injection_script, self._emit)
            self.bridge.start()
            print(f"Recording via DevTools connection ({address})")
            return
        except Exception as e:
            print("DevTools recorder unavailable, falling back to HTTP:", e)
            self.bridge = None

        try:
            # Inject into current page
            self.driver.execute_script(injection_script)
            # Inject into all future pages (survives navigation)
            self.driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {'source': injection_script})
        except Exception as e:
            print("Failed to inject script", e)

    def browser_alive(self) -> bool:
        """False if there is no browser or the user closed its window."""
        if not self.driver:
            return False
        try:
            return len(self.driver.window_handles) > 0
        except Exception:
            return False

    def _emit(self, event: dict):
        if self.on_event and event.get("command"):
            self.on_event(event)

    def stop_recording(self):
        print("Stopping recording")
        self.is_recording = False
        if self.bridge:
            self.bridge.stop()
            self.bridge = None
        try:
            self.browser.close()
        except Exception as e:
            # Browser may already have been closed by the user.
            print("Browser already closed:", e)
        finally:
            self.browser.driver = None
            self.driver = None
