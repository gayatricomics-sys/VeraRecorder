# VeraRecorder

VeraRecorder is a powerful, desktop-based web application interaction recorder designed specifically for Veracode DAST (Dynamic Analysis Security Testing) compatibility. 

It provides an intuitive interface to record your browser interactions, auto-crawl websites, and automatically generate perfectly formatted `.side`, Playwright (`.spec.ts`), and Cypress (`.cy.js`) scripts—all with native Veracode Scanner Variables support built-in.

## Features
- **Manual Recording**: Spin up a controlled browser session and click through your application. VeraRecorder tracks every move and converts it into scripts.
- **Autonomous Crawling**: Enter a URL and let VeraRecorder explore the application, automatically finding forms and filling them out to generate comprehensive coverage scripts.
- **Multi-Format Export**: Generates `.side` (Selenium IDE), `.spec.ts` (Playwright), and `.cy.js` (Cypress) files concurrently.
- **Native Veracode Support**: Built from the ground up to ensure all generated `.side` files use only Veracode-accepted commands (`open`, `click`, `type`, `select`).
- **Built-in Scanner Variable Editor**: Add Veracode Scanner Variables (like `${TOTP_SECRET}`) directly into your recorded scripts without ever leaving the app.
- **100% Offline Capable**: Bundled into a standalone architecture that requires zero dependencies, Python environments, or internet connections to run.

## Architecture

VeraRecorder is built with a dual-stack architecture:
1. **Frontend**: React + Vite + TailwindCSS, packaged via **Electron** for native desktop capabilities.
2. **Backend**: Python + FastAPI + Selenium.

For production, the Python backend is bundled into a standalone executable using **PyInstaller**. The Electron app silently spawns this background service upon launch, enabling a seamless, single-click boot process.

## Building from Source

### Prerequisites
- Node.js (v18+)
- Python (3.9+)

### 1. Build the Backend (Mac/Linux)
```bash
cd python
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install pyinstaller
pyinstaller --name api --onefile api/main.py
```

### 2. Build the Backend (Windows)
```cmd
cd python
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
pip install pyinstaller
pyinstaller --name api --onefile api\main.py
```

### 3. Package the App
Once the PyInstaller backend binary (`api` or `api.exe`) is generated in the `python/dist/` directory, build the Electron frontend:
```bash
cd electron
npm install
# To build for your current OS:
npm run dist
# To build for Windows (must be on a Windows machine):
npm run dist:win
```

The output standalone installer will be placed in `electron/release/`.
