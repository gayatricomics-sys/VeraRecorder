from recorder.browser.launcher import BrowserLauncher
from recorder.cdp_bridge import CdpRecorderBridge, BINDING_NAME
from recorder.locator.engine import LocatorEngine


class RecorderEngine:
    def __init__(self, ws_manager):
        self.browser = BrowserLauncher()
        self.locator_engine = LocatorEngine()
        self.ws_manager = ws_manager
        self.driver = None
        self.is_recording = False
        self.bridge = None
        # Set by the API: called with {"command", "target", "value"} for every
        # recorded step. Without it, steps are only delivered via HTTP fallback.
        self.on_event = None

    def start_recording(self, url: str):
        print(f"Starting recording on {url}")
        if self.driver:
            # Don't orphan a previous Chrome session.
            self.stop_recording()
        self.driver = self.browser.launch_chrome(url)
        self.is_recording = True

        # The page calls window.__vrRecord (== cdp_bridge.BINDING_NAME).
        injection_script = """
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

            document.addEventListener('click', (e) => {
                let target = e.target;
                let locator = '';
                if (target.name) locator = 'name=' + target.name;
                else if (target.id && !/\\d/.test(target.id)) locator = 'id=' + target.id;
                else locator = 'xpath=' + getXPath(target);
                
                sendEvent('click', locator, '');
            }, true);

            document.addEventListener('change', (e) => {
                let target = e.target;
                let locator = '';
                if (target.name) locator = 'name=' + target.name;
                else if (target.id && !/\\d/.test(target.id)) locator = 'id=' + target.id;
                else locator = 'xpath=' + getXPath(target);
                
                if (target.tagName.toLowerCase() === 'select') {
                    let selectedOption = target.options[target.selectedIndex];
                    let optionText = selectedOption ? selectedOption.text : '';
                    sendEvent('select', locator, 'label=' + optionText);
                } else {
                    sendEvent('type', locator, target.value);
                }
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
