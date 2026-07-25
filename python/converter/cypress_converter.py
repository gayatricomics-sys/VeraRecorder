import re
from recorder.side.generator import SideGenerator

class CypressConverter:
    def __init__(self, script_content, project_name="Cypress_Converted", url=""):
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
                
            # Parse cy.visit('url')
            visit_match = re.search(r'cy\.visit\([\'"]([^\'"]+)[\'"]\)', line)
            if visit_match:
                url_val = visit_match.group(1)
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
                
            # Parse cy.get('selector').click()
            click_match = re.search(r'cy\.get\([\'"]([^\'"]+)[\'"]\)\.click\(\)', line)
            if click_match:
                self._add_action("click", click_match.group(1))
                continue
                
            # Parse cy.contains('text').click()
            contains_match = re.search(r'cy\.contains\([\'"]([^\'"]+)[\'"]\)\.click\(\)', line)
            if contains_match:
                text = contains_match.group(1)
                xpath = f"xpath=//*[contains(text(), '{text}')]"
                self._add_action("click", xpath)
                continue
                
            # Parse cy.get('selector').type('value')
            type_match = re.search(r'cy\.get\([\'"]([^\'"]+)[\'"]\)\.type\([\'"]([^\'"]+)[\'"]\)', line)
            if type_match:
                self._add_action("type", type_match.group(1), type_match.group(2))
                continue
                
            # Parse cy.get('selector').select('value')
            select_match = re.search(r'cy\.get\([\'"]([^\'"]+)[\'"]\)\.select\([\'"]([^\'"]+)[\'"]\)', line)
            if select_match:
                self._add_action("select", select_match.group(1), f"label={select_match.group(2)}")
                continue
                
        # Manually invoke veracode best practice generation (this adds the waitForPageToLoad and post-verify)
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
