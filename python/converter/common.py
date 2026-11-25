"""Shared pieces for converting Playwright / Cypress scripts to .side commands."""
import re

from recorder.side.generator import SideGenerator

# A JS string literal in ', " or ` quotes (simple backslash escapes allowed).
Q = r"""(?:'(?:[^'\\]|\\.)*'|"(?:[^"\\]|\\.)*"|`(?:[^`\\]|\\.)*`)"""


def unquote(lit: str) -> str:
    body = lit[1:-1]
    return re.sub(r"\\(.)", r"\1", body)


def xq(text: str) -> str:
    """Quote a string for XPath 1.0 (which has no escapes)."""
    if '"' not in text:
        return f'"{text}"'
    if "'" not in text:
        return f"'{text}'"
    parts = text.split('"')
    return "concat(" + ", '\"', ".join(f'"{p}"' for p in parts) + ")"


def css_attr(v: str) -> str:
    return v.replace("\\", "\\\\").replace('"', '\\"')


_PREFIXES = ("id=", "name=", "css=", "xpath=", "link=", "linkText=")


def locator_from_selector(sel: str) -> str:
    """Turn a CSS/XPath selector string from a script into a Selenium IDE locator."""
    sel = sel.strip()
    if sel.startswith(("xpath=", "css=")):
        return sel
    if sel.startswith(("//", "(//", "/html")):
        return "xpath=" + sel
    if sel.startswith("text="):
        return "xpath=//*[normalize-space(text())=" + xq(sel[5:].strip("'\"")) + "]"
    if re.fullmatch(r"#[A-Za-z][\w-]*", sel):
        return "id=" + sel[1:]
    if sel.startswith(_PREFIXES):
        return sel
    return "css=" + sel


class BaseConverter:
    """Line-based converter: subclasses implement convert_line()."""

    def __init__(self, script_content, project_name, url=""):
        self.script_content = script_content or ""
        self.project_name = project_name
        self.url = url or "https://example.com"
        self.generator = SideGenerator(self.project_name, self.url)
        self.generator.current_test["commands"] = []
        # (line number, text) of script steps that could not be converted.
        self.skipped = []

    # Lines that are structure, not steps.
    _NOISE = re.compile(r"^\s*(import |const |let |var |await expect|expect\(|test\(|it\(|describe\(|beforeEach|afterEach|\}|\)|//|#|/\*|\*)")

    def convert(self) -> str:
        for no, raw in enumerate(self.script_content.splitlines(), 1):
            line = raw.strip().rstrip(";").strip()
            if not line or self._NOISE.match(line) and not self.is_step(line):
                continue
            if not self.convert_line(line) and self.is_step(line):
                self.skipped.append((no, raw.strip()))
        return self.generator.generate()

    def is_step(self, line: str) -> bool:
        raise NotImplementedError

    def convert_line(self, line: str) -> bool:
        raise NotImplementedError

    def open(self, url_val: str):
        if not self.url or self.url == "https://example.com":
            self.url = url_val
            self.generator.url = url_val
        target = url_val
        if target.startswith(self.url):
            target = target[len(self.url):] or "/"
            if not target.startswith("/"):
                target = "/" + target
        self.generator.add_command("open", target)

    def add(self, command, locator, value=""):
        self.generator.add_command(command, locator, value)
