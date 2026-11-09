@echo off
REM Build the VeraRecorder backend on Windows, fully offline.
REM Run from the python\ folder:  build_backend.bat
setlocal
cd /d "%~dp0"

REM The bundled wheels (wheels\windows) support Python 3.10, 3.11 and 3.12 only.
REM Python 3.13+ has no websockets 12.0 / pydantic-core 2.18.4 builds, which
REM shows up as "No matching distribution found for websockets==12.0".
set "PY="
for %%V in (3.12 3.11 3.10) do (
  if not defined PY py -%%V -c "import sys" >nul 2>nul && set "PY=py -%%V"
)
if not defined PY (
  python -c "import sys; sys.exit(0 if (3,10) <= sys.version_info[:2] <= (3,12) else 1)" >nul 2>nul && set "PY=python"
)
if not defined PY (
  echo ERROR: Python 3.10, 3.11 or 3.12 is required. Found:
  python --version 2>nul
  echo Install "%~dp0..\offline\installers\python-3.12.10-amd64.exe" ^(it installs
  echo next to any other Python^), then open a new Command Prompt and re-run.
  goto :error
)
for /f "delims=" %%I in ('%PY% -c "import sys; print(sys.version.split()[0])"') do set "PYVER=%%I"
echo Using Python %PYVER% ^(%PY%^)

REM Recreate the venv if it was copied from macOS/Linux or made with another Python.
set "VENVVER="
if exist venv\Scripts\python.exe for /f "delims=" %%I in ('venv\Scripts\python.exe -c "import sys; print(sys.version.split()[0])"') do set "VENVVER=%%I"
if exist venv if not "%VENVVER%"=="%PYVER%" (
  echo Recreating venv for Python %PYVER%...
  rmdir /S /Q venv
)
if not exist venv (
  %PY% -m venv venv || goto :error
)
call venv\Scripts\activate.bat || goto :error

echo Installing Python packages from local wheels (no internet)...
python -m pip install --no-index --find-links=wheels\windows -r requirements.txt pyinstaller || goto :error

echo Building backend (folder build, no UPX - avoids Windows Defender false positives)...
pyinstaller --noconfirm --clean --onedir --noupx --name api ^
  --paths . --collect-submodules uvicorn ^
  --version-file version_info.txt ^
  api\main.py || goto :error

if exist drivers\chrome\chrome.exe (
  xcopy /E /I /Q /Y drivers\chrome dist\api\chrome >nul
  echo Bundled Chrome for Testing into dist\api\chrome\
)
if exist drivers\chromedriver.exe (
  copy /Y drivers\chromedriver.exe dist\api\chromedriver.exe >nul
  echo Bundled ChromeDriver into dist\api\
) else (
  echo WARNING: drivers\chromedriver.exe not found - recording will need internet to fetch ChromeDriver.
)

echo.
echo Backend built: %cd%\dist\api\api.exe
exit /b 0

:error
echo Build failed.
exit /b 1
