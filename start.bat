@echo off
REM FairScrapper API Startup Script (Windows)
REM Author: Volkan AYDIN
REM Year: 2025

echo 🚀 Starting FairScrapper API...
echo ==================================

REM Navigate to project directory
cd /d "%~dp0"

REM Check virtual environment
if not exist "venv" (
    echo ❌ Virtual environment not found!
    echo 💡 Please create virtual environment first:
    echo    python -m venv venv
    echo    venv\Scripts\activate
    echo    pip install -r requirements.txt
    echo    playwright install
    pause
    exit /b 1
)

REM Activate virtual environment
echo 🔧 Activating virtual environment...
call venv\Scripts\activate.bat

REM Check Python dependencies
echo 📦 Checking Python packages...
python -c "import fastapi, playwright, requests" >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Some Python packages are missing!
    echo 💡 Please install dependencies:
    echo    pip install -r requirements.txt
    echo    playwright install
    pause
    exit /b 1
)

REM Check Playwright browsers
echo 🌐 Checking Playwright browsers...
python -c "from playwright.sync_api import sync_playwright; p = sync_playwright().start(); p.chromium.launch(); p.stop()" >nul 2>&1
if %errorlevel% neq 0 (
    echo ⚠️  Playwright browsers missing, installing...
    playwright install
)

REM Load environment variables
echo ⚙️  Loading environment variables...
if exist ".env" (
    echo ✅ .env file loaded
) else (
    echo ⚠️  .env file not found, using default settings
)

REM Show Host and Port information
if defined API_HOST (
    set HOST=%API_HOST%
) else (
    set HOST=127.0.0.1
)

if defined API_PORT (
    set PORT=%API_PORT%
) else (
    set PORT=8888
)

echo 🌍 Server settings:
echo    Host: %HOST%
echo    Port: %PORT%
echo.

REM Start API
echo 🎯 Starting API...
echo 📡 API URL: http://%HOST%:%PORT%
echo 📚 Documentation: http://%HOST%:%PORT%/docs
echo.
echo 🛑 Press Ctrl+C to stop
echo ==================================

REM Run API
python api.py

pause
