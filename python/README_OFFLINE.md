# Offline Installation Guide (Windows)

VeraRecorder can be built and run on a Windows PC with **no internet**.
Everything it needs is downloaded once on a machine *with* internet, then the
whole `VeraRecorder` folder is copied over (USB drive, network share, etc.).

## What is bundled

| Part | Where | In git? |
|------|-------|---------|
| Python packages for Windows x64, **Python 3.10, 3.11 or 3.12**, + PyInstaller | `python/wheels/windows/` (Python 3.12 versions in `python/requirements-windows.lock.txt`) | Yes |
| Python packages for macOS (Apple Silicon, Python 3.9) | `python/wheels/` | Yes |
| Chrome for Testing + matching ChromeDriver (win64) | `python/drivers/` | No (too large) |
| Python and Node.js installers | `offline/installers/` | No |
| npm packages for Windows x64 | `offline/npm-cache/` | No |
| Electron runtime for Windows | `offline/electron-dist/` | No |
| NSIS installer tools | `offline/electron-builder-cache/` | No |

The items not in git are downloaded by `offline/prepare-offline-kit.sh`.

The app uses the bundled Chrome and ChromeDriver, so recording never tries to
download a driver. (Without them, Selenium downloads ChromeDriver on first
use, which fails offline.)

## Step 1: Prepare the kit (machine WITH internet)

On macOS, Linux, or Git Bash on Windows (needs `node`, `curl`, `unzip`, `python3`):

```bash
./offline/prepare-offline-kit.sh
```

Then copy the whole `VeraRecorder` folder to the offline Windows PC.

## Step 2: Build on the offline Windows PC

1. Install Python from `offline\installers\python-3.12.*-amd64.exe`
   (tick **Add python.exe to PATH**). It can sit next to another Python;
   the build picks 3.12 automatically through the `py` launcher.

   > **Python 3.13 or newer will not work.** The pinned `websockets==12.0` and
   > `pydantic-core==2.18.4` have no Windows builds for it, so pip reports
   > *"No matching distribution found for websockets==12.0"*. Use 3.10–3.12.
2. Install Node.js from `offline\installers\node-*-x64.msi`.
3. Open a new Command Prompt in the `VeraRecorder` folder and run:

```cmd
offline\build-windows.bat
```

This installs the Python wheels from `python\wheels\windows`, builds the
backend with PyInstaller, installs npm packages from the local cache, and
creates the installer in `electron\release\`.

## Step 3: Install on other offline PCs

Copy `electron\release\VeraRecorder Setup *.exe` to any offline Windows PC and
run it. Nothing else is needed; Python, Chrome and ChromeDriver are inside the app.

Recordings are saved to `%USERPROFILE%\VeraRecorder\exports`.

## Windows Defender

The backend is built to avoid common false positives:

- PyInstaller **folder build** (`--onedir`) instead of a single self-extracting
  `--onefile` exe, which Defender flags most often.
- No UPX compression (`--noupx`).
- Windows version information embedded in `api.exe` (`version_info.txt`).

The only complete fix for Defender and SmartScreen warnings is **code signing**
with a certificate. If your organisation has one, set `CSC_LINK` and
`CSC_KEY_PASSWORD` before running `build-windows.bat` and electron-builder will
sign the installer. If Defender still quarantines `api.exe`, an administrator
can add the install folder as an exclusion or submit the file to Microsoft as
a false positive.

## Installing only the Python packages

Use Python 3.10, 3.11 or 3.12 (here via the `py` launcher):

```cmd
cd python
py -3.12 -m venv venv
venv\Scripts\activate
python -m pip install --no-index --find-links=wheels\windows -r requirements.txt
```

macOS (Apple Silicon, Python 3.9):

```bash
pip install --no-index --find-links=wheels/ -r requirements.txt
```
