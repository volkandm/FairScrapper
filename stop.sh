#!/bin/bash

# Web Scraper API Stop Script
echo "🛑 Stopping Web Scraper API..."

# Find and kill Python API processes
API_PID=$(ps aux | grep "python.*api.py" | grep -v grep | awk '{print $2}')

if [ -n "$API_PID" ]; then
    echo "📍 Found API process with PID: $API_PID"
    echo "🔪 Killing process..."
    kill -9 $API_PID
    echo "✅ API stopped successfully"
else
    echo "ℹ️  No API process found running"
fi

# Also kill any Python HTTP server processes (test servers)
HTTP_PID=$(ps aux | grep "python.*http.server" | grep -v grep | awk '{print $2}')

if [ -n "$HTTP_PID" ]; then
    echo "📍 Found HTTP server process with PID: $HTTP_PID"
    echo "🔪 Killing HTTP server..."
    kill -9 $HTTP_PID
    echo "✅ HTTP server stopped"
fi

echo "🎉 All processes stopped!"

