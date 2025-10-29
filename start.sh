#!/bin/bash

# FairScrapper API Startup Script
# Author: Volkan AYDIN
# Year: 2025

# Parse args
DEBUG=0
if [ "$1" = "--debug" ]; then
    DEBUG=1
fi

echo "🚀 Starting FairScrapper API..."
echo "=================================="

# Navigate to project directory
cd "$(dirname "$0")"

# Check virtual environment
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found!"
    echo "💡 Please create virtual environment first:"
    echo "   python3 -m venv venv"
    echo "   source venv/bin/activate"
    echo "   pip install -r requirements.txt"
    echo "   playwright install"
    exit 1
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Check Python dependencies
echo "📦 Checking Python packages..."
python -c "import fastapi, playwright, requests, bs4, socks" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "❌ Some Python packages are missing!"
    echo "💡 Please install dependencies:"
    echo "   pip install -r requirements.txt"
    echo "   playwright install"
    exit 1
fi

# Check Playwright browsers
echo "🌐 Checking Playwright browsers..."
PLAYWRIGHT_CACHE_FILE=".playwright_installed"

# Check if we've already verified Playwright installation recently (within last 24 hours)
if [ -f "$PLAYWRIGHT_CACHE_FILE" ]; then
    CACHE_AGE=$(($(date +%s) - $(stat -f %m "$PLAYWRIGHT_CACHE_FILE" 2>/dev/null || stat -c %Y "$PLAYWRIGHT_CACHE_FILE" 2>/dev/null || echo 0)))
    if [ $CACHE_AGE -lt 86400 ]; then  # 24 hours = 86400 seconds
        echo "✅ Playwright browsers already installed (cached)"
    else
        # Cache expired, check again
        rm -f "$PLAYWRIGHT_CACHE_FILE"
    fi
fi

# If no cache file, check Playwright installation
if [ ! -f "$PLAYWRIGHT_CACHE_FILE" ]; then
    if playwright --version >/dev/null 2>&1 && python -c "from playwright.sync_api import sync_playwright; p = sync_playwright().start(); p.chromium.executable_path; p.stop()" >/dev/null 2>&1; then
        echo "✅ Playwright browsers already installed"
        touch "$PLAYWRIGHT_CACHE_FILE"
    else
        echo "⚠️  Playwright browsers missing, installing..."
        if [ $DEBUG -eq 1 ]; then
            playwright install
        else
            # Suppress install output in non-debug mode
            playwright install >/dev/null 2>&1
        fi
        # Create cache file after successful installation
        if playwright --version >/dev/null 2>&1 && python -c "from playwright.sync_api import sync_playwright; p = sync_playwright().start(); p.chromium.executable_path; p.stop()" >/dev/null 2>&1; then
            touch "$PLAYWRIGHT_CACHE_FILE"
            echo "✅ Playwright browsers installed successfully"
        else
            echo "❌ Playwright installation failed"
        fi
    fi
fi

# Load environment variables
echo "⚙️  Loading environment variables..."
if [ -f ".env" ]; then
    # Load .env file and export variables
    set -a
    source .env
    set +a
    echo "✅ .env file loaded"
else
    echo "⚠️  .env file not found, using default settings"
fi

# Show Host and Port information
API_HOST=${API_HOST:-"127.0.0.1"}
API_PORT=${API_PORT:-"8888"}
SSL_ENABLED=${SSL_ENABLED:-"false"}

# If host is 127.0.0.1, change to 0.0.0.0 for external access
if [ "$API_HOST" = "127.0.0.1" ]; then
    API_HOST="0.0.0.0"
    echo "🌐 Host changed from 127.0.0.1 to 0.0.0.0 for external access"
fi

# Determine protocol based on SSL_ENABLED
PROTOCOL="http"
if [ "$SSL_ENABLED" = "true" ]; then
    PROTOCOL="https"
    echo "🔒 SSL/HTTPS enabled"
    
    # Check if SSL certificates exist
    if [ ! -f "./ssl/cert.pem" ] || [ ! -f "./ssl/key.pem" ]; then
        echo "⚠️  SSL certificates not found!"
        echo "💡 Please run: ./install.sh"
        echo "   Or generate manually:"
        echo "   mkdir -p ssl"
        echo "   openssl req -x509 -newkey rsa:4096 -nodes -out ssl/cert.pem -keyout ssl/key.pem -days 365"
        echo ""
        echo "🔓 Falling back to HTTP mode..."
        PROTOCOL="http"
    fi
fi

echo "🌍 Server settings:"
echo "   Protocol: $PROTOCOL"
echo "   Host: $API_HOST"
echo "   Port: $API_PORT"
echo ""

# Start API
echo "🎯 Starting API..."
echo "📡 API URL: $PROTOCOL://$API_HOST:$API_PORT"
echo "📚 Documentation: $PROTOCOL://$API_HOST:$API_PORT/docs"
if [ "$PROTOCOL" = "https" ]; then
    echo "🔐 HTTPS enabled (self-signed certificate)"
    echo "   For curl: use -k flag to ignore SSL verification"
    echo "   For browser: accept the self-signed certificate warning"
fi
echo ""
echo "🛑 Press Ctrl+C to stop"
echo "=================================="

# Run API (background by default, foreground with --debug)
if [ $DEBUG -eq 1 ]; then
    echo "🪲 Debug mode: running in foreground"
    python api.py
else
    echo "🌓 Running in background (nohup)"
    # Disable job control messages to keep terminal clean
    set +m
    nohup python api.py </dev/null >> api.log 2>&1 &
    APP_PID=$!
    echo "✅ Started in background. PID: $APP_PID"
    echo "📝 Logs: tail -f api.log"
fi
