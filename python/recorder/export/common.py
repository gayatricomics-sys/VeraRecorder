"""Shared helpers for turning recorded Selenium-IDE style steps
(command / target / value) into Playwright and Cypress code."""
import re
from urllib.parse import urljoin


def js_str(text) -> str:
    """Escape a value for a single-quoted JavaScript string literal."""
    s = "" if text is None else str(text)
    return (s.replace("\\", "\\\\").replace("'", "\\'")
             .replace("\r", "\\r").replace("\n", "\\n").replace("\u2028", "\\u2028").replace("\u2029", "\\u2029"))


def _attr(v: str) -> str:
    """Escape a value for a double-quoted CSS attribute selector."""
    return v.replace("\\", "\\\\").replace('"', '\\"')


def parse_target(target: str):
    """Return (kind, selector) with kind in {"css", "xpath", "text"}.

    id=foo     -> css  [id="foo"]   (not "#foo": ids like "user.name" or ":r1:" are invalid as #id)
    name=foo   -> css  [name="foo"]
    css=...    -> css  ...
    xpath=...  -> xpath ...
    link=/linkText=... -> text ...
    anything else is treated as XPath if it starts with "/" or "(", otherwise CSS.
    """
    t = target or ""
    if t.startswith("id="):
        return "css", f'[id="{_attr(t[3:])}"]'
    if t.startswith("name="):
        return "css", f'[name="{_attr(t[5:])}"]'
    if t.startswith("css="):
        return "css", t[4:]
    if t.startswith("xpath="):
        return "xpath", t[6:]
    if t.startswith("linkText="):
        return "text", t[9:]
    if t.startswith("link="):
        return "text", t[5:]
    if t.startswith(("/", "(")):
        return "xpath", t
    return "css", t


def parse_select_value(value: str):
    """Selenium select values: label=X, value=X, index=N, or a bare label."""
    v = value or ""
    for kind in ("label", "value", "index"):
        if v.startswith(kind + "="):
            return kind, v[len(kind) + 1:]
    return "label", v


def resolve_url(base_url: str, target: str) -> str:
    """Resolve a recorded 'open' target (often "/" or a path) against the base URL."""
    if base_url and not re.match(r"^[a-z][a-z0-9+.-]*:", target or "", re.I):
        return urljoin(base_url, target or "/")
    return target or base_url


def wait_ms(value) -> int:
    v = str(value or "").strip()
    return int(v) if v.isdigit() else 0


def starts_with_open(commands) -> bool:
    first = next((c.get("command") for c in commands if c.get("command")), None)
    return first == "open"
