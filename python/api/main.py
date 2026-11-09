import os
import sys

# Make the `python/` folder importable when run as `python api/main.py`
# (and when bundled by PyInstaller from that script).
_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _BASE_DIR not in sys.path:
    sys.path.insert(0, _BASE_DIR)

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import asyncio
import json
import uuid
import subprocess
import re
from pydantic import BaseModel
from recorder.engine import RecorderEngine
from recorder.crawler import AutoCrawler
from converter.playwright_converter import PlaywrightConverter
from converter.cypress_converter import CypressConverter

app = FastAPI(title="VeraRecorder API")


def _resolve_exports_dir() -> str:
    override = os.environ.get("VERARECORDER_EXPORTS_DIR")
    if override:
        return os.path.abspath(override)
    if getattr(sys, "frozen", False):
        # PyInstaller --onefile unpacks into a temp dir that is wiped on exit,
        # so persist exports in the user's home folder instead.
        return os.path.join(os.path.expanduser("~"), "VeraRecorder", "exports")
    return os.path.join(_BASE_DIR, "exports")


EXPORTS_DIR = _resolve_exports_dir()
os.makedirs(EXPORTS_DIR, exist_ok=True)


def _export_path(filename: str):
    """Return an absolute path inside EXPORTS_DIR, or None for unsafe names."""
    name = os.path.basename(filename or "")
    if not name or name != filename:
        return None
    return os.path.join(EXPORTS_DIR, name)


def _safe_project_name(name: str) -> str:
    name = os.path.basename((name or "").strip()) or "VeraRecording"
    return re.sub(r'[<>:"/\\|?*]', "_", name)

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
        if websocket in self.active_connections:
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

class RecordEventPayload(BaseModel):
    command: str
    target: str
    value: str = ""
    confidence: float = 0.95

async def broadcast_command(command: str, target: str, value: str = "", confidence: float = 0.95):
    event_data = {
        "type": "COMMAND",
        "payload": {
            "id": str(uuid.uuid4()),
            "command": command,
            "target": target,
            "value": value or "",
            "confidence": confidence,
        },
    }
    print(f"RECORD EVENT: {command} {target} {value!r}")
    await manager.broadcast(json.dumps(event_data))


def _bind_recorder_events(loop):
    """Forward steps from the browser (DevTools bridge, runs in its own thread)
    to the app's WebSocket clients on the server's event loop."""
    def on_event(ev: dict):
        asyncio.run_coroutine_threadsafe(
            broadcast_command(ev.get("command"), ev.get("target") or "", ev.get("value") or "",
                              ev.get("confidence", 0.95)),
            loop,
        )
    recorder_engine.on_event = on_event


@app.post("/api/record")
async def record_event(payload: RecordEventPayload):
    # HTTP fallback, used only when the DevTools bridge could not start.
    await broadcast_command(payload.command, payload.target, payload.value, payload.confidence)
    return {"status": "success"}

@app.get("/api/exports")
def get_exports():
    import glob
    files = []
    for ext in ["*.side", "*.spec.ts", "*.cy.js"]:
        files.extend(glob.glob(os.path.join(EXPORTS_DIR, ext)))
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
    file_path = _export_path(filename)
    if file_path and os.path.exists(file_path):
        if sys.platform == "darwin":
            subprocess.run(["open", "-R", file_path])
        elif sys.platform == "win32":
            subprocess.run(["explorer", "/select,", file_path])
        else:
            subprocess.run(["xdg-open", os.path.dirname(file_path)])
        return {"status": "opened"}
    return {"status": "not found"}

@app.get("/api/exports/read")
async def read_export(filename: str):
    file_path = _export_path(filename)
    if file_path and os.path.exists(file_path) and filename.endswith(".side"):
        with open(file_path, "r") as f:
            data = json.load(f)
        return {"status": "success", "data": data}
    return {"status": "error", "message": "File not found or invalid type"}

class SaveExportRequest(BaseModel):
    filename: str
    commands: list

@app.post("/api/exports/save")
async def save_export(req: SaveExportRequest):
    from recorder.export.playwright_gen import PlaywrightGenerator
    from recorder.export.cypress_gen import CypressGenerator

    exports_dir = EXPORTS_DIR
    file_path = _export_path(req.filename)

    if file_path and os.path.exists(file_path) and req.filename.endswith(".side"):
        with open(file_path, "r") as f:
            data = json.load(f)
            
        # Update commands in the first test
        if "tests" in data and len(data["tests"]) > 0:
            data["tests"][0]["commands"] = req.commands
            
            with open(file_path, "w") as f:
                json.dump(data, f, indent=2)
                
            # Regenerate PW and Cypress files
            project_name = req.filename[: -len(".side")]
            pw_gen = PlaywrightGenerator(project_name, data.get("url", ""))
            pw_content = pw_gen.generate(req.commands)
            cy_gen = CypressGenerator(project_name, data.get("url", ""))
            cy_content = cy_gen.generate(req.commands)
            
            pw_path = os.path.join(exports_dir, f"{project_name}.spec.ts")
            cy_path = os.path.join(exports_dir, f"{project_name}.cy.js")
            
            with open(pw_path, "w") as f:
                f.write(pw_content)
            with open(cy_path, "w") as f:
                f.write(cy_content)
                
            return {"status": "success", "message": "Saved successfully"}
    return {"status": "error", "message": "File not found"}

def _export_side(payload: dict) -> str:
    from recorder.side.generator import SideGenerator
    from recorder.export.playwright_gen import PlaywrightGenerator
    from recorder.export.cypress_gen import CypressGenerator

    project_name = _safe_project_name(payload.get("projectName", "VeraRecording"))
    url = payload.get("url") or "https://example.com"
    commands = payload.get("commands") or []

    generator = SideGenerator(project_name, url)
    for cmd in commands:
        generator.add_command(cmd.get("command"), cmd.get("target", ""), cmd.get("value") or "")
    side_content = generator.generate()

    pw_content = PlaywrightGenerator(project_name, url).generate(commands)
    cy_content = CypressGenerator(project_name, url).generate(commands)

    export_path = os.path.join(EXPORTS_DIR, f"{project_name}.side")
    with open(export_path, "w") as f:
        f.write(side_content)
    with open(os.path.join(EXPORTS_DIR, f"{project_name}.spec.ts"), "w") as f:
        f.write(pw_content)
    with open(os.path.join(EXPORTS_DIR, f"{project_name}.cy.js"), "w") as f:
        f.write(cy_content)
    print(f"Exported {project_name} (.side/.spec.ts/.cy.js) to {EXPORTS_DIR}")
    return export_path


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            try:
                command = json.loads(data)
                action = command.get("action")
                payload = command.get("payload") or {}

                # Selenium calls block, so run them off the event loop to keep
                # /api/record and other sockets responsive.
                if action in ("START_RECORDING", "START_AUTO_CRAWL"):
                    _bind_recorder_events(asyncio.get_running_loop())

                if action == "START_RECORDING":
                    await asyncio.to_thread(recorder_engine.start_recording, payload.get("url") or "https://google.com")
                elif action == "START_AUTO_CRAWL":
                    if not recorder_engine.driver:
                        await asyncio.to_thread(recorder_engine.start_recording, payload.get("url") or "https://google.com")
                    else:
                        print("Auto Crawl triggered on existing browser session")

                    import threading
                    crawler = AutoCrawler(recorder_engine.driver, max_steps=6)
                    threading.Thread(target=crawler.crawl, daemon=True).start()
                elif action == "STOP_RECORDING":
                    await asyncio.to_thread(recorder_engine.stop_recording)
                elif action == "RECORDED_EVENT":
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
                    await manager.broadcast(json.dumps(event_data))
                elif action == "EXPORT_SIDE":
                    export_path = await asyncio.to_thread(_export_side, payload)
                    await manager.send_personal_message(json.dumps({"type": "EXPORT_SUCCESS", "path": export_path}), websocket)
            except WebSocketDisconnect:
                raise
            except Exception as e:
                # One failing action (e.g. user closed Chrome manually) must not
                # kill the socket, otherwise the following EXPORT_SIDE is lost.
                print(f"Error handling websocket message: {e!r}")
                try:
                    await manager.send_personal_message(json.dumps({"type": "ERROR", "message": str(e)}), websocket)
                except Exception:
                    pass
    except WebSocketDisconnect:
        pass
    finally:
        manager.disconnect(websocket)

def start_server():
    # Pass the app object (not an import string) and no reload: both break
    # inside a PyInstaller-frozen binary.
    uvicorn.run(app, host="127.0.0.1", port=8000)


class PlaywrightConvertRequest(BaseModel):
    scriptContent: str
    projectName: str
    targetUrl: str

@app.post("/api/convert/playwright")
async def convert_playwright(req: PlaywrightConvertRequest):
    try:
        converter = PlaywrightConverter(req.scriptContent, req.projectName, req.targetUrl)
        side_content = converter.convert()
        
        filename = f"{_safe_project_name(req.projectName)}_playwright_converted.side"
        export_path = os.path.join(EXPORTS_DIR, filename)
        
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
        
        filename = f"{_safe_project_name(req.projectName)}_cypress_converted.side"
        export_path = os.path.join(EXPORTS_DIR, filename)
        
        with open(export_path, "w") as f:
            f.write(side_content)
            
        return {"status": "success", "message": f"Saved {filename}", "path": export_path}
    except Exception as e:
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    start_server()
