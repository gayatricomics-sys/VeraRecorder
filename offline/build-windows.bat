@echo off
REM Build the VeraRecorder Windows installer with NO internet.
REM Prerequisite: offline\prepare-offline-kit.sh was run on a machine with
REM internet, and this whole folder was copied here.
setlocal
set "ROOT=%~dp0.."
set "KIT=%~dp0"

where python >nul 2>nul || (
  echo Python not found. Install it from "%KIT%installers\python-*-amd64.exe"
  echo  ^(tick "Add python.exe to PATH"^), then open a new terminal and re-run.
  exit /b 1
)
where npm >nul 2>nul || (
  echo Node.js not found. Install it from "%KIT%installers\node-*-x64.msi",
  echo  then open a new terminal and re-run.
  exit /b 1
)

echo === 1/3 Backend (Python, from local wheels)
call "%ROOT%\python\build_backend.bat" || goto :error

echo === 2/3 Frontend packages (from local npm cache)
cd /d "%ROOT%\electron"
set ELECTRON_SKIP_BINARY_DOWNLOAD=1
call npm ci --offline --cache "%KIT%npm-cache" --no-audit --no-fund || goto :error
call npm run build || goto :error

echo === 3/3 Windows installer (from local Electron + NSIS cache)
set "ELECTRON_BUILDER_CACHE=%KIT%electron-builder-cache"
call npx --offline electron-builder --win --x64 --config.electronDist="%KIT%electron-dist" || goto :error

echo.
echo Done. Installer: %ROOT%\electron\release\
echo Copy the "VeraRecorder Setup *.exe" to any offline Windows PC and run it.
exit /b 0

:error
echo Build failed.
exit /b 1
