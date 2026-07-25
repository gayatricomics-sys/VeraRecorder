import re
from recorder.side.generator import SideGenerator

class PlaywrightConverter:
    def __init__(self, script_content, project_name="Playwright_Converted", url=""):
        self.script_content = script_content
        self.project_name = project_name
        self.url = url or "https://example.com"
        self.generator = SideGenerator(self.project_name, self.url)
        # Clear default Prep commands to only reflect the script
        self.generator.current_test["commands"] = []

    def convert(self):
        lines = self.script_content.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line or line.startswith('//') or line.startswith('#'):
                continue
                
            # Parse .goto('url')
            goto_match = re.search(r'\.goto\([\'"]([^\'"]+)[\'"]\)', line)
            if goto_match:
                url_val = goto_match.group(1)
                if not self.url or self.url == "https://example.com":
                    self.url = url_val
                    self.generator.url = url_val
                
                # if URL matches base, use /
                target = url_val
                if target.startswith(self.url):
                    target = target.replace(self.url, "")
                    if not target.startswith("/"):
                        target = "/" + target
                
                self.generator.add_command("open", target)
                continue
                
            # Parse .click('selector')
            click_match_1 = re.search(r'\.click\([\'"]([^\'"]+)[\'"]\)', line)
            if click_match_1:
                self._add_action("click", click_match_1.group(1))
                continue
                
            # Parse .locator('selector').click()
            click_match_2 = re.search(r'\.locator\([\'"]([^\'"]+)[\'"]\)\.click\(\)', line)
            if click_match_2:
                self._add_action("click", click_match_2.group(1))
                continue
                
            # Parse .getByRole('type', { name: 'value' }).click()
            role_match = re.search(r'\.getByRole\([\'"]([^\'"]+)[\'"],\s*\{\s*name:\s*[\'"]([^\'"]+)[\'"]\s*\}\)\.click\(\)', line)
            if role_match:
                role = role_match.group(1)
                name = role_match.group(2)
                xpath = f'xpath=//*[@role="{role}" and text()="{name}"]'
                self._add_action("click", xpath)
                continue
                
            # Parse .fill('selector', 'value')
            fill_match_1 = re.search(r'\.fill\([\'"]([^\'"]+)[\'"],\s*[\'"]([^\'"]+)[\'"]\)', line)
            if fill_match_1:
                self._add_action("type", fill_match_1.group(1), fill_match_1.group(2))
                continue
                
            # Parse .locator('selector').fill('value')
            fill_match_2 = re.search(r'\.locator\([\'"]([^\'"]+)[\'"]\)\.fill\([\'"]([^\'"]+)[\'"]\)', line)
            if fill_match_2:
                self._add_action("type", fill_match_2.group(1), fill_match_2.group(2))
                continue
                
            # Parse .selectOption('selector', 'value')
            select_match_1 = re.search(r'\.selectOption\([\'"]([^\'"]+)[\'"],\s*[\'"]([^\'"]+)[\'"]\)', line)
            if select_match_1:
                self._add_action("select", select_match_1.group(1), f"label={select_match_1.group(2)}")
                continue
                
            # Parse .locator('selector').selectOption('value')
            select_match_2 = re.search(r'\.locator\([\'"]([^\'"]+)[\'"]\)\.selectOption\([\'"]([^\'"]+)[\'"]\)', line)
            if select_match_2:
                self._add_action("select", select_match_2.group(1), f"label={select_match_2.group(2)}")
                continue
                
        # Manually invoke veracode best practice generation (this adds the waitForPageToLoad and post-verify)
        # Note: the SideGenerator automatically adds post-verify inside generate(), and conditionally adds open/wait.
        return self.generator.generate()
        
    def _add_action(self, command, target, value=""):
        processed_target = target
        if target.startswith('xpath='):
            pass
        elif target.startswith('//'):
            processed_target = f"xpath={target}"
        elif target.startswith('#'):
            processed_target = f"id={target[1:]}"
        elif target.startswith('.'):
            processed_target = f"css={target}"
        elif '=' not in target:
            # Assume css
            processed_target = f"css={target}"
            
        self.generator.add_command(command, processed_target, value)
