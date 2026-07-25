import json

class SideGenerator:
    def __init__(self, project_name: str, url: str):
        self.project_name = project_name
        self.url = url
        self.tests = []
        self.current_test = {
            "id": "test-id-placeholder",
            "name": "Login Flow",
            "commands": []
        }
        
    def add_command(self, command: str, target: str, value: str = ""):
        self.current_test["commands"].append({
            "id": f"cmd-{len(self.current_test['commands'])}",
            "comment": "",
            "command": command,
            "target": target,
            "targets": [[target, "xpath"]],
            "value": value
        })
        
    def generate(self) -> str:
        # Enforce Veracode Best Practices
        commands = self.current_test["commands"]
        
        # 1. Ensure the script starts with 'open'
        if not commands or commands[0]["command"] != "open":
            commands.insert(0, {
                "id": f"cmd-prep-open",
                "comment": "Veracode Best Practice: Always open base URL",
                "command": "open",
                "target": "/",
                "targets": [],
                "value": ""
            })
            
        # Removed unsupported waitFor... commands as Veracode DAST does not accept them.

        # Construct .side JSON structure
        side_file = {
            "id": "project-id-placeholder",
            "version": "2.0",
            "name": self.project_name,
            "url": self.url,
            "tests": [self.current_test],
            "suites": [{
                "id": "suite-id",
                "name": "Default Suite",
                "persistSession": False,
                "parallel": False,
                "timeout": 300,
                "tests": [self.current_test["id"]]
            }],
            "urls": [self.url],
            "plugins": []
        }
        return json.dumps(side_file, indent=2)
