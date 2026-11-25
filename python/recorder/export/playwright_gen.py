from recorder.export.common import (js_str, parse_select_value, parse_target, resolve_url,
                                    starts_with_open, wait_ms)


class PlaywrightGenerator:
    def __init__(self, project_name, base_url=""):
        self.project_name = project_name
        self.base_url = base_url or ""

    @staticmethod
    def _locator(target):
        kind, sel = parse_target(target)
        if kind == "xpath":
            # Keep the engine prefix: Playwright only auto-detects XPath for "//...".
            return f"page.locator('xpath={js_str(sel)}')"
        if kind == "text":
            return f"page.getByText('{js_str(sel)}', {{ exact: true }})"
        return f"page.locator('{js_str(sel)}')"

    def generate(self, commands):
        script = [
            "import { test, expect } from '@playwright/test';",
            "",
            f"test('{js_str(self.project_name)} Recorded Session', async ({{ page }}) => {{",
        ]
        # Recordings start on the target page without an explicit 'open' step;
        # without this the script would start on a blank page.
        if self.base_url and not starts_with_open(commands):
            script.append(f"  await page.goto('{js_str(self.base_url)}');")

        for cmd in commands:
            c = cmd.get("command")
            t = cmd.get("target") or ""
            v = cmd.get("value") or ""
            if not c:
                continue
            if c == "open":
                script.append(f"  await page.goto('{js_str(resolve_url(self.base_url, t))}');")
            elif c == "click":
                script.append(f"  await {self._locator(t)}.click();")
            elif c == "type":
                # fill() replaces the field's content, like Selenium's "type".
                script.append(f"  await {self._locator(t)}.fill('{js_str(v)}');")
            elif c == "select":
                kind, val = parse_select_value(v)
                arg = f"{{ index: {wait_ms(val)} }}" if kind == "index" else f"{{ {kind}: '{js_str(val)}' }}"
                script.append(f"  await {self._locator(t)}.selectOption({arg});")
            elif c in ("assertElementPresent", "waitForElementPresent", "waitForElementVisible"):
                script.append(f"  await expect({self._locator(t)}).toBeVisible();")
            elif c == "pause":
                script.append(f"  await page.waitForTimeout({wait_ms(v)});")
        script.append("});")
        return "\n".join(script) + "\n"
