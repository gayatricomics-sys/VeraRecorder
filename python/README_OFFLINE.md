# Offline Installation Guide (Windows)

VeraRecorder can be built and run on a Windows x64 PC with **no internet**.
Everything it needs comes in one Windows-only download,
`VeraRecorder-offline-windows.zip` (about 570 MB). Nothing in it is for macOS.

## Step 1: Get the offline kit (on any machine WITH internet)

**Option A: download it from GitHub Releases (easiest).**

Download `VeraRecorder-offline-windows.zip` from the
[latest release](https://github.com/gayatricomics-sys/VeraRecorder/releases/latest)
(direct link:
<https://github.com/gayatricomics-sys/VeraRecorder/releases/latest/download/VeraRecorder-offline-windows.zip>).
Copy it to the offline Windows PC (USB drive, network share, etc.) and unzip it.
You get a `VeraRecorder` folder.

> Don't use GitHub's green **Code > Download ZIP** button or `git clone` for the
> offline PC. Those only contain the source; the large Windows files (Chrome,
> Electron, npm packages, installers) are too big for git and exist only in the
> release zip.

**Option B: make the kit yourself** (macOS, Linux, or Git Bash on Windows;
needs `node`, `curl`, `unzip`, `python3`):

```bash
./offline/prepare-offline-kit.sh --zip
```

This fills `offline/` and `python/drivers/` and writes
`dist-offline/VeraRecorder-offline-windows.zip`. Copy the zip (or the whole
folder) to the offline PC.

## What is in the kit

| Part | Where | In git? |
|------|-------|---------|
| Python packages for Windows x64, **Python 3.10, 3.11 or 3.12**, + PyInstaller | `python/wheels/windows/` (Python 3.12 versions in `python/requirements-windows.lock.txt`) | Yes |
| Chrome for Testing + matching ChromeDriver (win64) | `python/drivers/` | No (zip only) |
| Python and Node.js installers for Windows | `offline/installers/` | No (zip only) |
| npm packages for Windows x64 | `offline/npm-cache/` (used automatically via `electron/.npmrc`) | No (zip only) |
| Electron runtime for Windows: `npm run dev` and the installer build | `offline/electron-cache/` | No (zip only) |
| Installer build tools (NSIS, rcedit, 7-Zip) for Windows | `offline/electron-builder-cache/` | No (zip only) |

Exact versions are listed in `offline/KIT_VERSIONS.txt` inside the zip.

The app uses the bundled Chrome and ChromeDriver, so recording never tries to
download a driver. (Without them, Selenium downloads ChromeDriver on first
use, which fails offline.)

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

## Using npm directly (development)

You can also run npm yourself in the `electron` folder with no internet:

```cmd
cd electron
npm install
npm run dev
```

- `electron\.npmrc` points npm at `..\offline\npm-cache`, so `npm install`
  and `npm ci` install every package from the bundled cache.
- Electron 43 downloads its runtime the first time it starts. `vite.config.ts`
  points that download at `..\offline\electron-cache`, so `npm run dev` works
  offline too.
- If you see `ENOTCACHED`, the folder didn't come from the offline kit zip
  (e.g. it was cloned from GitHub), or `package-lock.json` changed after the
  kit was made. Get the latest kit zip, or re-run
  `offline/prepare-offline-kit.sh --zip` on a machine with internet.

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

The repository also has macOS wheels (Apple Silicon, Python 3.9) in
`python/wheels/` for development on a Mac; they are not part of the Windows kit.
