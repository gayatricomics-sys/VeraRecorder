class CypressGenerator:
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
        return target

    def generate(self, commands):
        script = [
            f"describe('{self.project_name} Recorded Session', () => {{",
            "  it('plays back successfully', () => {"
        ]
        
        for cmd in commands:
            c = cmd.get('command')
            t = cmd.get('target', '')
            v = cmd.get('value', '')
            
            if not c:
                continue
                
            if c == 'open':
                script.append(f"    cy.visit('{t}');")
            elif c == 'click':
                if t.startswith('xpath='):
                    script.append(f"    cy.xpath('{self._format_target(t)}').click();")
                elif t.startswith('linkText='):
                    script.append(f"    cy.contains('{t[9:]}').click();")
                else:
                    script.append(f"    cy.get('{self._format_target(t)}').click();")
            elif c == 'type':
                if t.startswith('xpath='):
                    script.append(f"    cy.xpath('{self._format_target(t)}').type('{v}');")
                else:
                    script.append(f"    cy.get('{self._format_target(t)}').type('{v}');")
            elif c == 'select':
                val = v.replace('label=', '')
                if t.startswith('xpath='):
                    script.append(f"    cy.xpath('{self._format_target(t)}').select('{val}');")
                else:
                    script.append(f"    cy.get('{self._format_target(t)}').select('{val}');")
            elif c == 'assertElementPresent' or c == 'waitForElementPresent':
                if t.startswith('xpath='):
                    script.append(f"    cy.xpath('{self._format_target(t)}').should('be.visible');")
                else:
                    script.append(f"    cy.get('{self._format_target(t)}').should('be.visible');")
            elif c == 'pause':
                script.append(f"    cy.wait({v});")

        script.append("  });")
        script.append("});")
        return "\n".join(script)
