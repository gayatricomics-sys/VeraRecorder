#!/usr/bin/env bash
# Build the VeraRecorder backend on macOS/Linux. Run from python/: ./build_backend.sh
set -euo pipefail
cd "$(dirname "$0")"
[ -d venv ] || python3 -m venv venv
source venv/bin/activate
WHEELS=wheels
pip install --no-index --find-links="$WHEELS" -r requirements.txt pyinstaller 2>/dev/null \
  || pip install -r requirements.txt pyinstaller
pyinstaller --noconfirm --clean --onedir --noupx --name api \
  --paths . --collect-submodules uvicorn api/main.py
if [ -f drivers/chromedriver ]; then cp drivers/chromedriver dist/api/chromedriver; fi
if [ -d drivers/chrome ]; then cp -R drivers/chrome dist/api/chrome; fi
echo "Backend built: $(pwd)/dist/api/api"
