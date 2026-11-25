from recorder.export.common import (js_str, parse_select_value, parse_target, resolve_url,
                                    starts_with_open, wait_ms)

# Typed text is literal: without this Cypress treats "{" in values as key
# commands ({enter}, {selectall}...), which breaks passwords containing braces.
TYPE_OPTS = "{ parseSpecialCharSequences: false }"


class CypressGenerator:
    def __init__(self, project_name, base_url=""):
        self.project_name = project_name
        self.base_url = base_url or ""
        self.uses_xpath = False

    def _get(self, target):
        kind, sel = parse_target(target)
        if kind == "xpath":
            self.uses_xpath = True
            return f"cy.xpath('{js_str(sel)}')"
        if kind == "text":
            return f"cy.contains('{js_str(sel)}')"
        return f"cy.get('{js_str(sel)}')"

    def generate(self, commands):
        self.uses_xpath = False
        body = []
        if self.base_url and not starts_with_open(commands):
            body.append(f"    cy.visit('{js_str(self.base_url)}');")

        for cmd in commands:
            c = cmd.get("command")
            t = cmd.get("target") or ""
            v = cmd.get("value") or ""
            if not c:
                continue
            if c == "open":
                body.append(f"    cy.visit('{js_str(resolve_url(self.base_url, t))}');")
            elif c == "click":
                body.append(f"    {self._get(t)}.click();")
            elif c == "type":
                # Selenium "type" replaces the content; Cypress .type('') is an error.
                if v == "":
                    body.append(f"    {self._get(t)}.clear();")
                else:
                    body.append(f"    {self._get(t)}.clear().type('{js_str(v)}', {TYPE_OPTS});")
            elif c == "select":
                kind, val = parse_select_value(v)
                arg = str(wait_ms(val)) if kind == "index" else f"'{js_str(val)}'"
                body.append(f"    {self._get(t)}.select({arg});")
            elif c in ("assertElementPresent", "waitForElementPresent", "waitForElementVisible"):
                body.append(f"    {self._get(t)}.should('be.visible');")
            elif c == "pause":
                body.append(f"    cy.wait({wait_ms(v)});")

        header = []
        if self.uses_xpath:
            header = ["// Uses cy.xpath(): install the @cypress/xpath plugin and add",
                      "// require('@cypress/xpath') to cypress/support/e2e.js.", ""]
        return "\n".join(header + [
            f"describe('{js_str(self.project_name)} Recorded Session', () => {{",
            "  it('plays back successfully', () => {",
            *body,
            "  });",
            "});",
        ]) + "\n"
