@echo off
setlocal
title Smart Transit - Setup and Run
cd /d "%~dp0"

echo.
echo ============================================
echo       SMART TRANSIT - SETUP AND RUN
echo ============================================
echo.

where py >nul 2>nul
if errorlevel 1 (
  echo ERROR: Python launcher "py" was not found.
  echo Install Python 3.12 or newer from https://www.python.org/downloads/windows/
  echo During installation, enable "Add Python to PATH".
  echo Then run this file again.
  pause
  exit /b 1
)

if not exist ".venv\Scripts\python.exe" (
  echo [1/4] Creating Python virtual environment...
  py -m venv .venv
  if errorlevel 1 goto failed
) else (
  echo [1/4] Virtual environment already exists.
)

echo.
echo [2/4] Installing required packages. Internet is required the first time...
".venv\Scripts\python.exe" -m pip install --upgrade pip
if errorlevel 1 goto failed
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 goto failed

echo.
echo [3/4] Checking the application...
".venv\Scripts\python.exe" -c "from app import create_app; c=create_app().test_client(); r=c.get('/health'); print(r.get_data(as_text=True)); raise SystemExit(0 if r.status_code == 200 else 1)"
if errorlevel 1 goto failed

echo.
echo [4/4] Starting Smart Transit at http://127.0.0.1:8000
echo Keep this black window open while using the website.
echo To stop the server, press Ctrl+C in this window.
start "" /b cmd /c "timeout /t 3 /nobreak >nul & start http://127.0.0.1:8000/"
".venv\Scripts\python.exe" wsgi.py
goto end

:failed
echo.
echo SETUP FAILED. Read the error above.
echo Common causes: no internet, Python missing, or antivirus/network restrictions.
echo If it fails, take a screenshot of this window and send it to ChatGPT.
pause
exit /b 1

:end
pause
