class PlaywrightGenerator:
    def __init__(self, project_name):
        self.project_name = project_name

    def _format_target(self, target):
        if target.startswith('id='):
            return f"#{target[3:]}"
        elif target.startswith('name='):
            return f"[name=\"{target[5:]}\"]"
        elif target.startswith('css='):
            return target[4:]
        elif target.startswith('xpath='):
            return target[6:]
        elif target.startswith('linkText='):
            return f"text={target[9:]}"
        return target

    def generate(self, commands):
        script = [
            "import { test, expect } from '@playwright/test';",
            "",
            f"test('{self.project_name} Recorded Session', async ({{ page }}) => {{"
        ]
        
        for cmd in commands:
            c = cmd.get('command')
            t = cmd.get('target', '')
            v = cmd.get('value', '')
            
            if not c:
                continue
                
            # Filter out veracode specific wait commands if they aren't natively supported, 
            # though standard commands are what we expect.
            if c == 'open':
                script.append(f"  await page.goto('{t}');")
            elif c == 'click':
                script.append(f"  await page.locator('{self._format_target(t)}').click();")
            elif c == 'type':
                # Playwright uses fill for typing into inputs
                script.append(f"  await page.locator('{self._format_target(t)}').fill('{v}');")
            elif c == 'select':
                # format is usually label=Value
                val = v.replace('label=', '')
                script.append(f"  await page.locator('{self._format_target(t)}').selectOption({{ label: '{val}' }});")
            elif c == 'assertElementPresent' or c == 'waitForElementPresent':
                script.append(f"  await expect(page.locator('{self._format_target(t)}')).toBeVisible();")
            elif c == 'pause':
                script.append(f"  await page.waitForTimeout({v});")

        script.append("});")
        return "\n".join(script)
