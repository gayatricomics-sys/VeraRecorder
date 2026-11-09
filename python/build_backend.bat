@echo off
REM Build the VeraRecorder backend on Windows, fully offline.
REM Run from the python\ folder:  build_backend.bat
setlocal
cd /d "%~dp0"

REM A venv copied from macOS/Linux has no Scripts\ folder; recreate it.
if exist venv if not exist venv\Scripts\activate.bat rmdir /S /Q venv
if not exist venv (
  python -m venv venv || goto :error
)
call venv\Scripts\activate.bat || goto :error

echo Installing Python packages from local wheels (no internet)...
pip install --no-index --find-links=wheels\windows -r requirements.txt pyinstaller || goto :error

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
