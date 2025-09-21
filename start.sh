#!/bin/bash

# FairScrapper API Startup Script
# Author: Volkan AYDIN
# Year: 2025

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
python -c "from playwright.sync_api import sync_playwright; p = sync_playwright().start(); p.chromium.launch(); p.stop()" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "⚠️  Playwright browsers missing, installing..."
    playwright install
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

# If host is 127.0.0.1, change to 0.0.0.0 for external access
if [ "$API_HOST" = "127.0.0.1" ]; then
    API_HOST="0.0.0.0"
    echo "🌐 Host changed from 127.0.0.1 to 0.0.0.0 for external access"
fi

echo "🌍 Server settings:"
echo "   Host: $API_HOST"
echo "   Port: $API_PORT"
echo ""

# Start API
echo "🎯 Starting API..."
echo "📡 API URL: http://$API_HOST:$API_PORT"
echo "📚 Documentation: http://$API_HOST:$API_PORT/docs"
echo ""
echo "🛑 Press Ctrl+C to stop"
echo "=================================="

# Run API
python api.py
