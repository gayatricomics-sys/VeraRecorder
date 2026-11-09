class CypressGenerator:
    def __init__(self, project_name):
        self.project_name = project_name

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
            return target[6:]
        return target

    def generate(self, commands):
        script = [
            f"describe('{self._q(self.project_name)} Recorded Session', () => {{",
            "  it('plays back successfully', () => {"
        ]
        
        for cmd in commands:
            c = cmd.get('command')
            t = cmd.get('target') or ''
            v = cmd.get('value') or ''
            
            if not c:
                continue
                
            if c == 'open':
                script.append(f"    cy.visit('{self._q(t)}');")
            elif c == 'click':
                if t.startswith('xpath='):
                    script.append(f"    cy.xpath('{self._format_target(t)}').click();")
                elif t.startswith('linkText='):
                    script.append(f"    cy.contains('{self._q(t[9:])}').click();")
                else:
                    script.append(f"    cy.get('{self._format_target(t)}').click();")
            elif c == 'type':
                if t.startswith('xpath='):
                    script.append(f"    cy.xpath('{self._format_target(t)}').type('{self._q(v)}');")
                else:
                    script.append(f"    cy.get('{self._format_target(t)}').type('{self._q(v)}');")
            elif c == 'select':
                val = v.replace('label=', '')
                if t.startswith('xpath='):
                    script.append(f"    cy.xpath('{self._format_target(t)}').select('{self._q(val)}');")
                else:
                    script.append(f"    cy.get('{self._format_target(t)}').select('{self._q(val)}');")
            elif c == 'assertElementPresent' or c == 'waitForElementPresent':
                if t.startswith('xpath='):
                    script.append(f"    cy.xpath('{self._format_target(t)}').should('be.visible');")
                else:
                    script.append(f"    cy.get('{self._format_target(t)}').should('be.visible');")
            elif c == 'pause':
                script.append(f"    cy.wait({int(v) if str(v).isdigit() else 0});")

        script.append("  });")
        script.append("});")
        return "\n".join(script)
