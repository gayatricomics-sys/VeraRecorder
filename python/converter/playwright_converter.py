import re

from converter.common import Q, BaseConverter, css_attr, locator_from_selector, unquote, xq

# getByRole name -> XPath for elements that have that role implicitly.
_ROLE_XPATH = {
    "button": '//button[normalize-space()={n}] | //input[(@type="submit" or @type="button" or @type="reset") and @value={n}] | //*[@role="button" and normalize-space()={n}]',
    "link": '//a[normalize-space()={n}] | //*[@role="link" and normalize-space()={n}]',
    "textbox": '//input[@aria-label={n} or @placeholder={n} or @id=//label[normalize-space()={n}]/@for] | //textarea[@aria-label={n} or @placeholder={n}]',
    "checkbox": '//input[@type="checkbox" and (@aria-label={n} or @id=//label[normalize-space()={n}]/@for)] | //label[normalize-space()={n}]//input[@type="checkbox"]',
    "combobox": '//select[@aria-label={n} or @id=//label[normalize-space()={n}]/@for]',
    "heading": '//*[self::h1 or self::h2 or self::h3 or self::h4 or self::h5 or self::h6][normalize-space()={n}]',
}

_LOC = re.compile(
    r"^(?:await\s+)?page\.(?:"
    rf"locator\((?P<loc>{Q})\)"
    rf"|getByRole\((?P<role>{Q})(?:\s*,\s*\{{[^}}]*?name:\s*(?P<rname>{Q})[^}}]*\}})?\s*\)"
    rf"|getByLabel\((?P<label>{Q})[^)]*\)"
    rf"|getByPlaceholder\((?P<ph>{Q})[^)]*\)"
    rf"|getByText\((?P<text>{Q})[^)]*\)"
    rf"|getByTestId\((?P<tid>{Q})\)"
    r")(?:\.(?:first|last)\(\)|\.nth\(\d+\))*"
    rf"\.(?P<act>click|dblclick|fill|type|pressSequentially|selectOption|check|uncheck)\((?P<args>.*)\)$"
)
_DIRECT = re.compile(
    rf"^(?:await\s+)?page\.(?P<act>click|dblclick|fill|type|selectOption|check|uncheck)\((?P<sel>{Q})(?:\s*,\s*(?P<args>.*))?\)$"
)
_GOTO = re.compile(rf"^(?:await\s+)?page\.goto\((?P<url>{Q})")


class PlaywrightConverter(BaseConverter):
    def __init__(self, script_content, project_name="Playwright_Converted", url=""):
        super().__init__(script_content, project_name, url)

    def is_step(self, line):
        return "page." in line and not line.startswith(("await expect", "expect("))

    def convert_line(self, line):
        m = _GOTO.match(line)
        if m:
            self.open(unquote(m.group("url")))
            return True
        m = _LOC.match(line)
        if m:
            return self._act(self._locator(m), m.group("act"), m.group("args"))
        m = _DIRECT.match(line)
        if m:
            return self._act(locator_from_selector(unquote(m.group("sel"))), m.group("act"), m.group("args") or "")
        return False

    @staticmethod
    def _locator(m):
        if m.group("loc"):
            return locator_from_selector(unquote(m.group("loc")))
        if m.group("role"):
            role = unquote(m.group("role"))
            if m.group("rname"):
                n = xq(unquote(m.group("rname")))
                tmpl = _ROLE_XPATH.get(role, '//*[@role="' + role + '" and normalize-space()={n}]')
                return "xpath=" + tmpl.format(n=n)
            return f'xpath=//*[@role="{role}"]'
        if m.group("label"):
            n = xq(unquote(m.group("label")))
            return (f"xpath=//*[@id=//label[normalize-space()={n}]/@for] | //label[normalize-space()={n}]//*[self::input or self::select or self::textarea]"
                    f" | //*[@aria-label={n}]")
        if m.group("ph"):
            return f'css=[placeholder="{css_attr(unquote(m.group("ph")))}"]'
        if m.group("text"):
            return f"xpath=//*[normalize-space(text())={xq(unquote(m.group('text')))}]"
        return f'css=[data-testid="{css_attr(unquote(m.group("tid")))}"]'

    def _act(self, locator, act, args):
        args = (args or "").strip()
        if act in ("click", "dblclick", "check", "uncheck"):
            self.add("click", locator)
            return True
        if act in ("fill", "type", "pressSequentially"):
            m = re.match(Q, args)
            if not m:
                return False
            self.add("type", locator, unquote(m.group(0)))
            return True
        if act == "selectOption":
            m = re.match(rf"^\{{\s*(label|value|index)\s*:\s*({Q}|\d+)", args)
            if m:
                val = m.group(2)
                if val[0] in "'\"`":
                    val = unquote(val)
                self.add("select", locator, f"{m.group(1)}={val}")
                return True
            m = re.match(Q, args)
            if m:
                self.add("select", locator, f"label={unquote(m.group(0))}")
                return True
        return False
