@echo off
REM Build the VeraRecorder Windows installer with NO internet.
REM Prerequisite: offline\prepare-offline-kit.sh was run on a machine with
REM internet, and this whole folder was copied here.
setlocal
set "ROOT=%~dp0.."
set "KIT=%~dp0"

set "HAVEPY="
where py >nul 2>nul && set HAVEPY=1
where python >nul 2>nul && set HAVEPY=1
if not defined HAVEPY (
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
call npm ci --offline --include=dev --cache "%KIT%npm-cache" --no-audit --no-fund || goto :error
REM Fail early with a clear message instead of "'tsc' is not recognized".
for %%P in (typescript\bin\tsc vite\bin\vite.js electron-builder\cli.js) do (
  if not exist "node_modules\%%P" (
    echo ERROR: node_modules\%%P is missing after npm ci.
    echo The npm install did not complete. Check the npm errors above, and that
    echo antivirus is not removing files from "%cd%\node_modules".
    goto :error
  )
)
REM Run the tools through node directly, not through node_modules\.bin\*.cmd
REM launchers (those can be missing or blocked on locked-down PCs).
call node node_modules\typescript\bin\tsc -b || goto :error
call node node_modules\vite\bin\vite.js build || goto :error

echo === 3/3 Windows installer (from local Electron + NSIS cache)
set "ELECTRON_BUILDER_CACHE=%KIT%electron-builder-cache"
REM The Electron runtime zip sits in offline\electron-cache\<hash>\ (shared
REM with `npm run dev`); electron-builder takes that folder as electronDist.
set "EDIST="
for /d %%D in ("%KIT%electron-cache\*") do if exist "%%D\electron-v*-win32-x64.zip" set "EDIST=%%D"
if not defined EDIST (
  echo ERROR: Electron runtime not found in "%KIT%electron-cache".
  echo Run offline/prepare-offline-kit.sh on a machine with internet first.
  goto :error
)
call node node_modules\electron-builder\cli.js --win --x64 --config.electronDist="%EDIST%" || goto :error

echo.
echo Done. Installer: %ROOT%\electron\release\
echo Copy the "VeraRecorder Setup *.exe" to any offline Windows PC and run it.
exit /b 0

:error
echo Build failed.
exit /b 1
