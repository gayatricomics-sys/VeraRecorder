"""Deliver recorded browser events over Chrome DevTools Protocol (CDP).

The recording script inside the page used to send each step with
fetch('http://127.0.0.1:8000/api/record'). Websites can block that:

  * a Content-Security-Policy such as ``connect-src 'self'`` (very common on
    production/enterprise apps) silently drops every request,
  * Chrome's private/local-network-access rules can block a public site from
    calling localhost.

When that happens nothing is recorded, so the Cypress/Playwright/.side exports
come out empty. CDP ``Runtime.addBinding`` instead gives the page a function
(``window.__vrRecord``) whose calls travel over the DevTools connection, which
the page's security policy cannot block.

This module opens its own DevTools connection to the Chrome that Selenium
started (chromedriver reports its ``debuggerAddress``), attaches to every tab
(including ones opened later, e.g. target=_blank links), installs the binding
plus the recording script, and calls ``on_event(dict)`` for every recorded step.
"""
import json
import threading
import urllib.request

from websockets.sync.client import connect

BINDING_NAME = "__vrRecord"


class CdpRecorderBridge:
    def __init__(self, debugger_address: str, page_script: str, on_event):
        host, _, port = debugger_address.rpartition(":")
        # "localhost" can resolve to IPv6 first on Windows; Chrome listens on IPv4.
        host = "127.0.0.1" if host in ("localhost", "") else host
        self._http = f"http://{host}:{port}"
        self._script = page_script
        self._on_event = on_event
        self._ws = None
        self._thread = None
        self._next_id = 0
        self._attached = set()
        self._stopped = threading.Event()

    # -- public -----------------------------------------------------------
    def start(self):
        with urllib.request.urlopen(self._http + "/json/version", timeout=5) as r:
            browser_ws = json.load(r)["webSocketDebuggerUrl"]
        # No Origin header is sent, so Chrome's --remote-allow-origins check passes.
        self._ws = connect(browser_ws, max_size=None, open_timeout=10)
        # Discover existing and future tabs; attach to each page as it appears.
        self._send("Target.setDiscoverTargets", {"discover": True})
        self._thread = threading.Thread(target=self._run, name="cdp-recorder", daemon=True)
        self._thread.start()

    def stop(self):
        self._stopped.set()
        if self._ws is not None:
            try:
                self._ws.close()
            except Exception:
                pass
            self._ws = None

    # -- internals --------------------------------------------------------
    def _send(self, method, params=None, session_id=None):
        self._next_id += 1
        msg = {"id": self._next_id, "method": method, "params": params or {}}
        if session_id:
            msg["sessionId"] = session_id
        self._ws.send(json.dumps(msg))

    def _setup_session(self, session_id):
        self._send("Runtime.enable", {}, session_id)
        self._send("Runtime.addBinding", {"name": BINDING_NAME}, session_id)
        self._send("Page.enable", {}, session_id)
        # Future documents in this tab...
        self._send("Page.addScriptToEvaluateOnNewDocument", {"source": self._script}, session_id)
        # ...and the document that is already loaded.
        self._send("Runtime.evaluate", {"expression": self._script}, session_id)
        self._send("Runtime.runIfWaitingForDebugger", {}, session_id)

    def _run(self):
        try:
            while not self._stopped.is_set():
                ws = self._ws
                if ws is None:
                    break
                msg = json.loads(ws.recv())
                method = msg.get("method")
                params = msg.get("params", {})
                if method in ("Target.targetCreated", "Target.targetInfoChanged"):
                    info = params.get("targetInfo", {})
                    tid = info.get("targetId")
                    if info.get("type") == "page" and tid not in self._attached:
                        self._attached.add(tid)
                        self._send("Target.attachToTarget", {"targetId": tid, "flatten": True})
                elif method == "Target.attachedToTarget":
                    self._setup_session(params["sessionId"])
                elif method == "Target.targetDestroyed":
                    self._attached.discard(params.get("targetId"))
                elif method == "Runtime.bindingCalled" and params.get("name") == BINDING_NAME:
                    try:
                        event = json.loads(params.get("payload") or "{}")
                    except ValueError:
                        continue
                    try:
                        self._on_event(event)
                    except Exception as e:  # never let a handler kill the bridge
                        print("Recorder event handler error:", e)
        except Exception as e:
            if not self._stopped.is_set():
                print("CDP recorder connection closed:", e)
