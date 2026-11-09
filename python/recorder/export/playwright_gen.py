import re


class PlaywrightGenerator:
    def __init__(self, project_name, base_url=""):
        self.project_name = project_name
        self.base_url = base_url or ""

    def _url(self, target):
        """Resolve a recorded 'open' target (often "/" or a path) against the base URL."""
        from urllib.parse import urljoin
        if self.base_url and not re.match(r"^[a-z][a-z0-9+.-]*:", target or "", re.I):
            return urljoin(self.base_url, target or "/")
        return target or self.base_url

    @staticmethod
    def _q(text):
        """Escape a value for use inside a single-quoted JS string."""
        return str(text if text is not None else "").replace("\\", "\\\\").replace("'", "\\'").replace("\n", "\\n")

    def _format_target(self, target):
        return self._q(self._raw_target(target))

    def _raw_target(self, target):
        target = target or ""
        if target.startswith('id='):
            return f"#{target[3:]}"
        elif target.startswith('name='):
            return f"[name=\"{target[5:]}\"]"
        elif target.startswith('css='):
            return target[4:]
        elif target.startswith('xpath='):
            # Keep the explicit engine prefix: Playwright only auto-detects
            # XPath for selectors starting with "//", not "/html/...".
            return target
        elif target.startswith('linkText='):
            return f"text={target[9:]}"
        return target

    def generate(self, commands):
        script = [
            "import { test, expect } from '@playwright/test';",
            "",
            f"test('{self._q(self.project_name)} Recorded Session', async ({{ page }}) => {{"
        ]
        
        # Recordings start on the target page without an explicit 'open' step;
        
        # without this the script would start on a blank page.
        
        first = next((c.get('command') for c in commands if c.get('command')), None)
        
        if self.base_url and first != 'open':
        
            script.append(f"  await page.goto('{self._q(self.base_url)}');")

        
        for cmd in commands:
            c = cmd.get('command')
            t = cmd.get('target') or ''
            v = cmd.get('value') or ''
            
            if not c:
                continue
                
            # Filter out veracode specific wait commands if they aren't natively supported, 
            # though standard commands are what we expect.
            if c == 'open':
                script.append(f"  await page.goto('{self._q(self._url(t))}');")
            elif c == 'click':
                script.append(f"  await page.locator('{self._format_target(t)}').click();")
            elif c == 'type':
                # Playwright uses fill for typing into inputs
                script.append(f"  await page.locator('{self._format_target(t)}').fill('{self._q(v)}');")
            elif c == 'select':
                # format is usually label=Value
                val = v.replace('label=', '')
                script.append(f"  await page.locator('{self._format_target(t)}').selectOption({{ label: '{self._q(val)}' }});")
            elif c == 'assertElementPresent' or c == 'waitForElementPresent':
                script.append(f"  await expect(page.locator('{self._format_target(t)}')).toBeVisible();")
            elif c == 'pause':
                script.append(f"  await page.waitForTimeout({int(v) if str(v).isdigit() else 0});")

        script.append("});")
        return "\n".join(script)
