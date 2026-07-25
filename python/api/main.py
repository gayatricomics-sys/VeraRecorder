from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import asyncio
import json
from recorder.engine import RecorderEngine
import uuid
from pydantic import BaseModel
import os
import subprocess
from recorder.crawler import AutoCrawler
from recorder.side.generator import SideGenerator
from converter.playwright_converter import PlaywrightConverter
from converter.cypress_converter import CypressConverter

app = FastAPI(title="VeraRecorder API")

# Allow CORS for Electron frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict this
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in list(self.active_connections):
            try:
                await connection.send_text(message)
            except Exception:
                if connection in self.active_connections:
                    self.active_connections.remove(connection)

manager = ConnectionManager()
recorder_engine = RecorderEngine(manager)

@app.get("/")
def read_root():
    return {"status": "VeraRecorder Backend Running"}

from pydantic import BaseModel
class RecordEventPayload(BaseModel):
    command: str
    target: str
    value: str
    confidence: float = 0.95

@app.post("/api/record")
async def record_event(payload: RecordEventPayload):
    event_data = {
        "type": "COMMAND",
        "payload": {
            "id": str(uuid.uuid4()),
            "command": payload.command,
            "target": payload.target,
            "value": payload.value,
            "confidence": payload.confidence
        }
    }
    print(f"HTTP RECORD EVENT: {event_data}")
    await manager.broadcast(json.dumps(event_data))
    return {"status": "success"}

@app.get("/api/exports")
def get_exports():
    import os
    import glob
    exports_dir = os.path.join(os.path.dirname(__file__), "..", "exports")
    if not os.path.exists(exports_dir):
        return {"files": []}
    
    files = []
    for ext in ["*.side", "*.spec.ts", "*.cy.js"]:
        files.extend(glob.glob(os.path.join(exports_dir, ext)))
    result = []
    for f in files:
        stat = os.stat(f)
        result.append({
            "name": os.path.basename(f),
            "size": stat.st_size,
            "modified": stat.st_mtime,
            "path": os.path.abspath(f)
        })
    result.sort(key=lambda x: x["modified"], reverse=True)
    return {"files": result}

@app.post("/api/exports/open")
async def open_export(filename: str):
    import os
    import subprocess
    exports_dir = os.path.join(os.path.dirname(__file__), "..", "exports")
    file_path = os.path.abspath(os.path.join(exports_dir, filename))
    if os.path.exists(file_path):
        subprocess.run(["open", "-R", file_path])
        return {"status": "opened"}
    return {"status": "not found"}

@app.get("/api/exports/read")
async def read_export(filename: str):
    import os
    import json
    exports_dir = os.path.join(os.path.dirname(__file__), "..", "exports")
    file_path = os.path.abspath(os.path.join(exports_dir, filename))
    if os.path.exists(file_path) and filename.endswith(".side"):
        with open(file_path, "r") as f:
            data = json.load(f)
        return {"status": "success", "data": data}
    return {"status": "error", "message": "File not found or invalid type"}

class SaveExportRequest(BaseModel):
    filename: str
    commands: list

@app.post("/api/exports/save")
async def save_export(req: SaveExportRequest):
    import os
    import json
    from recorder.export.playwright_gen import PlaywrightGenerator
    from recorder.export.cypress_gen import CypressGenerator
    
    exports_dir = os.path.join(os.path.dirname(__file__), "..", "exports")
    file_path = os.path.abspath(os.path.join(exports_dir, req.filename))
    
    if os.path.exists(file_path) and req.filename.endswith(".side"):
        with open(file_path, "r") as f:
            data = json.load(f)
            
        # Update commands in the first test
        if "tests" in data and len(data["tests"]) > 0:
            data["tests"][0]["commands"] = req.commands
            
            with open(file_path, "w") as f:
                json.dump(data, f, indent=2)
                
            # Regenerate PW and Cypress files
            project_name = req.filename.replace(".side", "")
            pw_gen = PlaywrightGenerator(project_name)
            pw_content = pw_gen.generate(req.commands)
            cy_gen = CypressGenerator(project_name)
            cy_content = cy_gen.generate(req.commands)
            
            pw_path = os.path.join(exports_dir, f"{project_name}.spec.ts")
            cy_path = os.path.join(exports_dir, f"{project_name}.cy.js")
            
            with open(pw_path, "w") as f:
                f.write(pw_content)
            with open(cy_path, "w") as f:
                f.write(cy_content)
                
            return {"status": "success", "message": "Saved successfully"}
    return {"status": "error", "message": "File not found"}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            command = json.loads(data)
            action = command.get("action")
            payload = command.get("payload", {})
            
            if action == "START_RECORDING":
                recorder_engine.start_recording(payload.get("url", "https://google.com"))
            elif action == "START_AUTO_CRAWL":
                if not recorder_engine.driver:
                    url = payload.get("url", "https://google.com")
                    recorder_engine.start_recording(url)
                else:
                    print("Auto Crawl triggered on existing browser session")
                
                import threading
                from recorder.crawler import AutoCrawler
                crawler = AutoCrawler(recorder_engine.driver, max_steps=6)
                threading.Thread(target=crawler.crawl, daemon=True).start()
            elif action == "STOP_RECORDING":
                recorder_engine.stop_recording()
            elif action == "RECORDED_EVENT":
                # Forward to frontend clients
                event_data = {
                    "type": "COMMAND",
                    "payload": {
                        "id": str(uuid.uuid4()),
                        "command": payload.get("command"),
                        "target": payload.get("target"),
                        "value": payload.get("value"),
                        "confidence": payload.get("confidence", 0.95)
                    }
                }
                print(f"BROADCASTING EVENT: {event_data}")
                await manager.broadcast(json.dumps(event_data))
            elif action == "EXPORT_SIDE":
                # Create a SIDE generator and save it
                from recorder.side.generator import SideGenerator
                import os
                
                project_name = payload.get("projectName", "VeraRecording")
                url = payload.get("url", "https://example.com")
                generator = SideGenerator(project_name, url)
                
                # We would typically retrieve the commands from state or frontend
                # For this prototype, we rely on the frontend sending the commands to export,
                # OR the backend storing them. Let's assume the frontend sends them in payload.commands.
                commands = payload.get("commands", [])
                for cmd in commands:
                    generator.add_command(cmd.get("command"), cmd.get("target"), cmd.get("value", ""))
                    
                side_content = generator.generate()
                
                # Generate Playwright and Cypress
                from recorder.export.playwright_gen import PlaywrightGenerator
                from recorder.export.cypress_gen import CypressGenerator
                
                pw_gen = PlaywrightGenerator(project_name)
                pw_content = pw_gen.generate(commands)
                
                cy_gen = CypressGenerator(project_name)
                cy_content = cy_gen.generate(commands)
                
                export_dir = os.path.join(os.path.dirname(__file__), "..", "exports")
                os.makedirs(export_dir, exist_ok=True)
                
                export_path = os.path.join(export_dir, f"{project_name}.side")
                pw_path = os.path.join(export_dir, f"{project_name}.spec.ts")
                cy_path = os.path.join(export_dir, f"{project_name}.cy.js")
                
                with open(export_path, "w") as f:
                    f.write(side_content)
                with open(pw_path, "w") as f:
                    f.write(pw_content)
                with open(cy_path, "w") as f:
                    f.write(cy_content)
                
                print(f"Exported to {export_path}, {pw_path}, {cy_path}")
                await manager.send_personal_message(json.dumps({"type": "EXPORT_SUCCESS", "path": export_path}), websocket)
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)

def start_server():
    uvicorn.run("api.main:app", host="127.0.0.1", port=8000, reload=True)


class PlaywrightConvertRequest(BaseModel):
    scriptContent: str
    projectName: str
    targetUrl: str

@app.post("/api/convert/playwright")
async def convert_playwright(req: PlaywrightConvertRequest):
    try:
        converter = PlaywrightConverter(req.scriptContent, req.projectName, req.targetUrl)
        side_content = converter.convert()
        
        # Save to exports
        export_dir = os.path.join(os.path.dirname(__file__), "..", "exports")
        os.makedirs(export_dir, exist_ok=True)
        filename = f"{req.projectName}_playwright_converted.side"
        export_path = os.path.join(export_dir, filename)
        
        with open(export_path, "w") as f:
            f.write(side_content)
            
        return {"status": "success", "message": f"Saved {filename}", "path": export_path}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/api/convert/cypress")
async def convert_cypress(req: PlaywrightConvertRequest):
    try:
        converter = CypressConverter(req.scriptContent, req.projectName, req.targetUrl)
        side_content = converter.convert()
        
        # Save to exports
        export_dir = os.path.join(os.path.dirname(__file__), "..", "..", "exports")
        os.makedirs(export_dir, exist_ok=True)
        filename = f"{req.projectName}_cypress_converted.side"
        export_path = os.path.join(export_dir, filename)
        
        with open(export_path, "w") as f:
            f.write(side_content)
            
        return {"status": "success", "message": f"Saved {filename}", "path": export_path}
    except Exception as e:
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    start_server()
