#!/usr/bin/env bash
# Run this ONCE on a machine WITH internet (macOS, Linux, or Git Bash on Windows).
# It downloads everything a Windows machine WITHOUT internet needs to build and
# run VeraRecorder. Afterwards copy the whole VeraRecorder folder (USB etc.)
# to the offline Windows machine and run offline\build-windows.bat there.
#
# Needs: node/npm, curl, unzip, python3.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
KIT="$ROOT/offline"
PYTHON_VERSION="${PYTHON_VERSION:-3.12.10}"   # must match wheels/windows (cp312)

mkdir -p "$KIT/installers" "$KIT/npm-cache" "$KIT/electron-dist" "$KIT/electron-builder-cache"

fetch() { # dest url [fallback-url...]  -- stops the script if every URL fails
  local dest="$1"; shift
  if [ -s "$dest" ]; then echo "  already have $(basename "$dest")"; return 0; fi
  for url in "$@"; do
    echo "  downloading $(basename "$dest") from $url"
    if curl -fL --retry 3 --progress-bar -o "$dest.part" "$url"; then mv "$dest.part" "$dest"; return 0; fi
    echo "  failed, trying next source..."
  done
  rm -f "$dest.part"; echo "ERROR: could not download $(basename "$dest")" >&2; exit 1
}

echo "== 1/5 Python and Node.js installers for Windows"
fetch "$KIT/installers/python-$PYTHON_VERSION-amd64.exe" \
      "https://www.python.org/ftp/python/$PYTHON_VERSION/python-$PYTHON_VERSION-amd64.exe"
NODE_VERSION="${NODE_VERSION:-$(curl -fsSL https://nodejs.org/dist/index.json | python3 -c '
import json,sys
print(next(r["version"] for r in json.load(sys.stdin) if r["lts"] and int(r["version"][1:].split(".")[0])>=22))')}"
fetch "$KIT/installers/node-$NODE_VERSION-x64.msi" "https://nodejs.org/dist/$NODE_VERSION/node-$NODE_VERSION-x64.msi"

echo "== 2/5 Matching Chrome + ChromeDriver (Chrome for Testing, win64)"
CFT_JSON="$(curl -fsSL https://googlechromelabs.github.io/chrome-for-testing/last-known-good-versions-with-downloads.json)"
cft_url() { echo "$CFT_JSON" | python3 -c "
import json,sys
d=json.load(sys.stdin)['channels']['Stable']
print(next(x['url'] for x in d['downloads']['$1'] if x['platform']=='win64'))"; }
CFT_VERSION="$(echo "$CFT_JSON" | python3 -c "import json,sys;print(json.load(sys.stdin)['channels']['Stable']['version'])")"
fetch "$KIT/installers/chrome-win64-$CFT_VERSION.zip"       "$(cft_url chrome)"
fetch "$KIT/installers/chromedriver-win64-$CFT_VERSION.zip" "$(cft_url chromedriver)"
DRV="$ROOT/python/drivers"
rm -rf "$DRV/chrome" "$DRV/chromedriver.exe" "$KIT/_tmp" && mkdir -p "$KIT/_tmp"
unzip -q "$KIT/installers/chrome-win64-$CFT_VERSION.zip" -d "$KIT/_tmp"
unzip -q "$KIT/installers/chromedriver-win64-$CFT_VERSION.zip" -d "$KIT/_tmp"
mv "$KIT/_tmp/chrome-win64" "$DRV/chrome"
mv "$KIT/_tmp/chromedriver-win64/chromedriver.exe" "$DRV/chromedriver.exe"
rm -rf "$KIT/_tmp"
echo "$CFT_VERSION" > "$DRV/VERSION.txt"

echo "== 3/5 npm packages for Windows x64 (offline cache)"
TMP_NPM="$(mktemp -d)"
cp "$ROOT/electron/package.json" "$ROOT/electron/package-lock.json" "$TMP_NPM/"
( cd "$TMP_NPM" && ELECTRON_SKIP_BINARY_DOWNLOAD=1 npm ci --os=win32 --cpu=x64 \
    --cache "$KIT/npm-cache" --ignore-scripts --no-audit --no-fund )
ELECTRON_VERSION="$(node -p "require('$TMP_NPM/node_modules/electron/package.json').version")"
rm -rf "$TMP_NPM"

echo "== 4/5 Electron $ELECTRON_VERSION runtime for Windows"
EZ="electron-v$ELECTRON_VERSION-win32-x64.zip"
fetch "$KIT/electron-dist/$EZ" \
      "https://github.com/electron/electron/releases/download/v$ELECTRON_VERSION/$EZ" \
      "https://npmmirror.com/mirrors/electron/$ELECTRON_VERSION/$EZ"

echo "== 5/5 electron-builder tools for Windows (NSIS, rcedit/winCodeSign, 7-Zip)"
# Pre-fetch the exact archives electron-builder needs when building on
# Windows. They are kept in <cache>/<release>/<file>, which electron-builder
# checks (with checksum) before going online, so the Windows build is offline.
cat > "$KIT/.prefetch.cjs" <<'JS'
// Resolve electron-builder from electron/node_modules (the working directory).
const req = require("module").createRequire(require("path").join(process.cwd(), "package.json"));
const { getBinFromUrl } = req("app-builder-lib/out/binDownload");
const { downloadBuilderToolset } = req("app-builder-lib/out/util/electronGet");
const tools = [
  () => getBinFromUrl("nsis-3.0.4.1", "nsis-3.0.4.1.7z", "9877df902530f96357d13a7a31ae2b9df67f48b11ffc9a1700a7c961574ec5fa"),
  () => getBinFromUrl("nsis-resources-3.4.1", "nsis-resources-3.4.1.7z", "593a9a92ef958321293ac6a2ee61e64bf1bd543142a5bd6b3d310709cc924103"),
  () => getBinFromUrl("winCodeSign-2.6.0", "winCodeSign-2.6.0.7z", "cdaec7154dda7cc31f88d886e2489379a0625a737d610b5ae7f62a12f16743a4"),
  () => downloadBuilderToolset({ releaseName: "7zip@1.0.0", filenameWithExt: "7zip-win-x64.tar.gz",
          checksums: { "7zip-win-x64.tar.gz": "be071f15bd6da2f78fe81c6ddef2009b0c4d8a51f36b780cb806c7e6df95e1b3" } }),
];
(async () => { for (const t of tools) console.log("  ok", await t()); })()
  .catch(e => { console.error("  failed:", e.message); process.exit(1); });
JS
EB_FILES="nsis-3.0.4.1/nsis-3.0.4.1.7z nsis-resources-3.4.1/nsis-resources-3.4.1.7z winCodeSign-2.6.0/winCodeSign-2.6.0.7z 7zip@1.0.0/7zip-win-x64.tar.gz"
missing() { for f in $EB_FILES; do [ -s "$KIT/electron-builder-cache/$f" ] || return 0; done; return 1; }
if missing; then
  for MIRROR in "" "https://npmmirror.com/mirrors/electron-builder-binaries/"; do
    ( cd "$ROOT/electron" && [ -d node_modules ] || npm ci --no-audit --no-fund )
    # Extracted folders without their archive would hide a missing archive; drop them.
    for f in $EB_FILES; do [ -s "$KIT/electron-builder-cache/$f" ] || rm -rf "$KIT/electron-builder-cache/$(dirname "$f")"; done
    ( cd "$ROOT/electron" && ELECTRON_BUILDER_CACHE="$KIT/electron-builder-cache" \
        ELECTRON_BUILDER_BINARIES_MIRROR="$MIRROR" node "$KIT/.prefetch.cjs" ) && ! missing && break
    echo "  retrying via mirror..."
  done
fi
missing && { echo "ERROR: electron-builder tools incomplete" >&2; exit 1; }
# Prove the cache works with no network: resolve every tool from a copy
# whose extracted folders are removed, with downloads pointed nowhere.
SIM="$(mktemp -d)"; cp -R "$KIT/electron-builder-cache/." "$SIM/"
find "$SIM" -mindepth 2 -maxdepth 2 \( -type d -o -name "*.state" \) -exec rm -rf {} +; rm -rf "$SIM/downloads"
( cd "$ROOT/electron" && ELECTRON_BUILDER_CACHE="$SIM" ELECTRON_BUILDER_BINARIES_MIRROR="http://127.0.0.1:9/" \
    node "$KIT/.prefetch.cjs" >/dev/null ) && echo "  verified: all tools resolve with no network" \
  || { echo "ERROR: offline check of electron-builder cache failed" >&2; exit 1; }
rm -rf "$SIM" "$KIT/.prefetch.cjs"

echo
echo "Offline kit ready. Copy the whole folder to the Windows machine:"
echo "  $ROOT"
echo "Chrome/ChromeDriver $CFT_VERSION, Python $PYTHON_VERSION, Node $NODE_VERSION, Electron $ELECTRON_VERSION"
du -sh "$KIT" "$ROOT/python/drivers" 2>/dev/null || true
