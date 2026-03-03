#!/bin/bash

# Web Scraper API Restart Script
# Stops the API and starts it again

echo "🔄 Restarting Web Scraper API..."
echo "=================================="

cd "$(dirname "$0")"

# Stop existing process
./stop.sh

# Brief wait for ports/processes to release
sleep 2

# Start again (pass through any args, e.g. --debug)
echo ""
./start.sh "$@"
