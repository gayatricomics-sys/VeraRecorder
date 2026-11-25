import re

from converter.common import Q, BaseConverter, locator_from_selector, unquote, xq

_CHAIN = r"(?:\.(?:first|last|clear|focus|scrollIntoView|should|eq|wait)\([^()]*\))*"
_VISIT = re.compile(rf"^cy\.visit\((?P<url>{Q})")
# cy.get(sel)[.find(sel)][chain].action(args)
_GET = re.compile(
    rf"^cy\.get\((?P<sel>{Q})[^)]*\)(?:\.find\((?P<find>{Q})\))?{_CHAIN}"
    rf"(?:\.contains\((?P<ctext>{Q})\))?{_CHAIN}"
    rf"\.(?P<act>click|dblclick|type|select|check|uncheck|clear)\((?P<args>.*)\)$"
)
# cy.contains(text) / cy.contains(selector, text)
_CONTAINS = re.compile(
    rf"^cy\.contains\((?P<a>{Q})(?:\s*,\s*(?P<b>{Q}))?[^)]*\){_CHAIN}\.(?P<act>click|dblclick|check)\(\s*\)$"
)


class CypressConverter(BaseConverter):
    def __init__(self, script_content, project_name="Cypress_Converted", url=""):
        super().__init__(script_content, project_name, url)

    def is_step(self, line):
        return line.startswith("cy.") and not re.match(r"^cy\.(wait|log|intercept|viewport|fixture|request|task|on)\b", line)

    def convert_line(self, line):
        m = _VISIT.match(line)
        if m:
            self.open(unquote(m.group("url")))
            return True
        m = _GET.match(line)
        if m:
            sel = unquote(m.group("sel"))
            if m.group("find"):
                sel = sel + " " + unquote(m.group("find"))
            locator = locator_from_selector(sel)
            if m.group("ctext"):
                css = locator[4:] if locator.startswith("css=") else None
                text = xq(unquote(m.group("ctext")))
                if css is None or "[" in css or ">" in css or " " in css:
                    locator = f"xpath=//*[normalize-space()={text}]"
                else:  # simple tag/class selector: keep it in the XPath
                    tag = re.match(r"^[a-zA-Z][\w-]*", css)
                    locator = f"xpath=//{tag.group(0) if tag else '*'}[normalize-space()={text}]"
            return self._act(locator, m.group("act"), m.group("args"))
        m = _CONTAINS.match(line)
        if m:
            if m.group("b"):
                tag = re.match(r"^[a-zA-Z][\w-]*$", unquote(m.group("a")))
                locator = f"xpath=//{tag.group(0) if tag else '*'}[contains(normalize-space(), {xq(unquote(m.group('b')))})]"
            else:
                locator = f"xpath=//*[contains(normalize-space(text()), {xq(unquote(m.group('a')))})]"
            return self._act(locator, m.group("act"), "")
        return False

    def _act(self, locator, act, args):
        args = (args or "").strip()
        if act in ("click", "dblclick", "check", "uncheck"):
            self.add("click", locator)
            return True
        if act == "clear":
            self.add("type", locator, "")
            return True
        m = re.match(Q, args)
        if not m:
            return False
        val = unquote(m.group(0))
        if act == "type":
            # Cypress key sequences such as {enter} are not plain text.
            special = re.findall(r"\{[a-zA-Z]+\}", val)
            if special and "parseSpecialCharSequences: false" not in args:
                val = re.sub(r"\{[a-zA-Z]+\}", "", val)
                if not val:
                    return False
            self.add("type", locator, val)
            return True
        if act == "select":
            self.add("select", locator, f"label={val}")
            return True
        return False
