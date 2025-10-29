#!/bin/bash

# Playwright Browser Installation Script
# Author: Volkan AYDIN
# Year: 2025

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

log_step() {
    echo -e "${BLUE}🔧 $1${NC}"
}

echo -e "${BLUE}🌐 Playwright Browser Installation Script${NC}"
echo -e "${BLUE}==========================================${NC}"
echo

# Navigate to project directory
cd "$(dirname "$0")"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    log_error "Virtual environment not found!"
    log_info "Please run ./install.sh first to set up the environment"
    exit 1
fi

# Activate virtual environment
log_step "Activating virtual environment..."
source venv/bin/activate
log_success "Virtual environment activated"

# Check if Playwright is installed
log_step "Checking Playwright installation..."
if ! python -c "import playwright" 2>/dev/null; then
    log_error "Playwright not installed!"
    log_info "Please run ./install.sh first to install dependencies"
    exit 1
fi
log_success "Playwright is installed"

# Install Playwright browsers
log_step "Installing Playwright browsers..."
log_info "This may take several minutes depending on your internet connection..."
log_info "Installing Chromium, Firefox, and WebKit browsers..."

if playwright install; then
    log_success "Playwright browsers installed successfully"
else
    log_error "Failed to install Playwright browsers"
    exit 1
fi

# Install system dependencies
log_step "Installing system dependencies..."
log_info "Installing system packages required for Playwright..."

if playwright install-deps; then
    log_success "System dependencies installed successfully"
else
    log_warning "System dependencies installation had issues"
    log_info "You may need to install them manually if you encounter problems"
fi

# Create cache file
touch ".playwright_installed"
log_success "Cache file created to avoid repeated checks"

# Test installation
log_step "Testing Playwright installation..."
if python -c "from playwright.sync_api import sync_playwright; p = sync_playwright().start(); p.chromium.executable_path; p.stop()" 2>/dev/null; then
    log_success "Playwright test passed - browsers are working correctly"
else
    log_warning "Playwright test failed - there may be issues with the installation"
fi

echo
echo -e "${GREEN}🎉 Playwright browsers installation completed!${NC}"
echo
echo -e "${BLUE}📋 Next steps:${NC}"
echo -e "1. ${YELLOW}Start the API server:${NC}"
echo -e "   ${BLUE}./start.sh${NC}"
echo
echo -e "2. ${YELLOW}Test the installation:${NC}"
echo -e "   ${BLUE}curl -X POST http://localhost:8888/health -H \"X-API-Key: sk-demo-key-12345\"${NC}"
echo
echo -e "${GREEN}✨ Playwright is ready to use!${NC}"
echo
