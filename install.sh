#!/bin/bash

# 🚀 FairScrapper API Installation Script
# Author: Volkan AYDIN
# Year: 2025
# License: CC BY-NC-SA 4.0 (Non-Commercial)

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Configuration
PYTHON_MIN_VERSION="3.8"
VENV_NAME="venv"
REQUIREMENTS_FILE="requirements.txt"
ENV_EXAMPLE_FILE="env_example.txt"
ENV_FILE=".env"

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
    echo -e "${PURPLE}🔧 $1${NC}"
}

# Check if running on supported OS
check_os() {
    log_step "Checking operating system..."
    
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        OS="linux"
        log_success "Linux detected"
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        OS="macos"
        log_success "macOS detected"
    else
        log_error "Unsupported operating system: $OSTYPE"
        log_info "Supported systems: Linux, macOS"
        exit 1
    fi
}

# Check if Python is installed and get version
check_python() {
    log_step "Checking Python installation..."
    
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2)
        log_success "Python $PYTHON_VERSION found"
        
        # Check if version meets minimum requirement
        if python3 -c "import sys; exit(0 if sys.version_info >= (3, 8) else 1)"; then
            log_success "Python version meets minimum requirement (3.8+)"
            return 0
        else
            log_warning "Python version $PYTHON_VERSION is below minimum requirement (3.8+)"
            return 1
        fi
    else
        log_warning "Python3 not found"
        return 1
    fi
}

# Install Python on different systems
install_python() {
    log_step "Installing Python..."
    
    if [[ "$OS" == "linux" ]]; then
        # Detect Linux distribution
        if command -v apt-get &> /dev/null; then
            # Ubuntu/Debian
            log_info "Installing Python on Ubuntu/Debian..."
            sudo apt-get update
            sudo apt-get install -y python3 python3-pip python3-venv python3-dev
        elif command -v yum &> /dev/null; then
            # CentOS/RHEL
            log_info "Installing Python on CentOS/RHEL..."
            sudo yum update -y
            sudo yum install -y python3 python3-pip python3-venv python3-devel
        elif command -v dnf &> /dev/null; then
            # Fedora
            log_info "Installing Python on Fedora..."
            sudo dnf update -y
            sudo dnf install -y python3 python3-pip python3-venv python3-devel
        elif command -v pacman &> /dev/null; then
            # Arch Linux
            log_info "Installing Python on Arch Linux..."
            sudo pacman -S --noconfirm python python-pip
        else
            log_error "Unsupported Linux distribution. Please install Python 3.8+ manually."
            exit 1
        fi
    elif [[ "$OS" == "macos" ]]; then
        # macOS
        log_info "Installing Python on macOS..."
        
        # Check if Homebrew is installed
        if command -v brew &> /dev/null; then
            log_info "Using Homebrew to install Python..."
            brew install python3
        else
            log_info "Installing Homebrew first..."
            /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
            brew install python3
        fi
    fi
    
    # Verify installation
    if check_python; then
        log_success "Python installation completed successfully"
    else
        log_error "Python installation failed"
        exit 1
    fi
}

# Create virtual environment
create_venv() {
    log_step "Creating virtual environment..."
    
    if [[ -d "$VENV_NAME" ]]; then
        log_warning "Virtual environment already exists. Removing old one..."
        rm -rf "$VENV_NAME"
    fi
    
    python3 -m venv "$VENV_NAME"
    log_success "Virtual environment created: $VENV_NAME"
}

# Activate virtual environment
activate_venv() {
    log_step "Activating virtual environment..."
    
    if [[ "$OS" == "linux" ]] || [[ "$OS" == "macos" ]]; then
        source "$VENV_NAME/bin/activate"
        log_success "Virtual environment activated"
    else
        log_error "Cannot activate virtual environment on this OS"
        exit 1
    fi
}

# Upgrade pip
upgrade_pip() {
    log_step "Upgrading pip..."
    python -m pip install --upgrade pip
    log_success "Pip upgraded to latest version"
}

# Install system dependencies
install_system_deps() {
    log_step "Installing system dependencies..."
    
    if [[ "$OS" == "linux" ]]; then
        # Install system packages required for Playwright
        if command -v apt-get &> /dev/null; then
            # Ubuntu/Debian
            sudo apt-get update
            sudo apt-get install -y \
                libnss3 \
                libatk-bridge2.0-0 \
                libdrm2 \
                libxkbcommon0 \
                libxcomposite1 \
                libxdamage1 \
                libxrandr2 \
                libgbm1 \
                libxss1 \
                libasound2 \
                libatspi2.0-0 \
                libgtk-3-0 \
                libgdk-pixbuf2.0-0
        elif command -v yum &> /dev/null; then
            # CentOS/RHEL
            sudo yum install -y \
                nss \
                atk \
                at-spi2-atk \
                gtk3 \
                libdrm \
                libxkbcommon \
                libXcomposite \
                libXdamage \
                libXrandr \
                mesa-libgbm \
                libXScrnSaver \
                alsa-lib
        elif command -v dnf &> /dev/null; then
            # Fedora
            sudo dnf install -y \
                nss \
                atk \
                at-spi2-atk \
                gtk3 \
                libdrm \
                libxkbcommon \
                libXcomposite \
                libXdamage \
                libXrandr \
                mesa-libgbm \
                libXScrnSaver \
                alsa-lib
        fi
    elif [[ "$OS" == "macos" ]]; then
        # macOS dependencies are usually handled by Homebrew
        log_info "macOS dependencies should be handled by Homebrew"
    fi
    
    log_success "System dependencies installed"
}

# Install Python dependencies
install_python_deps() {
    log_step "Installing Python dependencies..."
    
    if [[ ! -f "$REQUIREMENTS_FILE" ]]; then
        log_error "Requirements file not found: $REQUIREMENTS_FILE"
        exit 1
    fi
    
    # Install requirements
    pip install -r "$REQUIREMENTS_FILE"
    log_success "Python dependencies installed"
}

# Install Playwright browsers
install_playwright() {
    log_step "Installing Playwright browsers..."
    
    # Install Playwright browsers
    playwright install
    
    # Install system dependencies for Playwright
    playwright install-deps
    
    log_success "Playwright browsers and dependencies installed"
}

# Create environment file
setup_env() {
    log_step "Setting up environment configuration..."
    
    if [[ ! -f "$ENV_FILE" ]]; then
        if [[ -f "$ENV_EXAMPLE_FILE" ]]; then
            log_info "Creating .env file from example..."
            cp "$ENV_EXAMPLE_FILE" "$ENV_FILE"
            log_success "Environment file created: $ENV_FILE"
        else
            log_info "Creating default .env file..."
            cat > "$ENV_FILE" << EOF
# Server Settings
API_HOST=127.0.0.1
API_PORT=8888

# Proxy Settings
PROXY_ENABLED=true
PROXY_LIST=http://proxy1:8080,http://proxy2:8080

# API Security
VALID_API_KEYS=sk-demo-key-12345,sk-test-key-67890
EOF
            log_success "Default environment file created: $ENV_FILE"
        fi
    else
        log_info "Environment file already exists: $ENV_FILE"
    fi
}

# Make scripts executable
make_executable() {
    log_step "Making scripts executable..."
    
    chmod +x start.sh
    chmod +x stop.sh
    chmod +x install.sh
    
    log_success "Scripts made executable"
}

# Test installation
test_installation() {
    log_step "Testing installation..."
    
    # Test Python import
    python -c "import fastapi, playwright, aiohttp, beautifulsoup4; print('All imports successful')"
    
    # Test Playwright
    python -c "from playwright.sync_api import sync_playwright; print('Playwright test successful')"
    
    log_success "Installation test passed"
}

# Display final information
show_completion() {
    echo
    echo -e "${GREEN}🎉 Installation completed successfully!${NC}"
    echo
    echo -e "${CYAN}📋 Next steps:${NC}"
    echo -e "1. ${YELLOW}Edit .env file${NC} to configure your settings:"
    echo -e "   ${BLUE}nano .env${NC}"
    echo
    echo -e "2. ${YELLOW}Start the API server:${NC}"
    echo -e "   ${BLUE}./start.sh${NC}"
    echo
    echo -e "3. ${YELLOW}Test the installation:${NC}"
    echo -e "   ${BLUE}curl -X POST http://localhost:8888/health -H \"X-API-Key: sk-demo-key-12345\"${NC}"
    echo
    echo -e "4. ${YELLOW}View API documentation:${NC}"
    echo -e "   ${BLUE}http://localhost:8888/docs${NC}"
    echo
    echo -e "${PURPLE}🔧 Configuration files:${NC}"
    echo -e "   • ${BLUE}.env${NC} - Environment configuration"
    echo -e "   • ${BLUE}requirements.txt${NC} - Python dependencies"
    echo -e "   • ${BLUE}start.sh${NC} - Start script"
    echo -e "   • ${BLUE}stop.sh${NC} - Stop script"
    echo
    echo -e "${GREEN}✨ FairScrapper API is ready to use!${NC}"
    echo
}

# Main installation function
main() {
    echo -e "${PURPLE}🚀 FairScrapper API Installation Script${NC}"
    echo -e "${PURPLE}==========================================${NC}"
    echo
    
    # Check OS
    check_os
    
    # Check Python
    if ! check_python; then
        log_warning "Python not found or version too old. Installing Python..."
        install_python
    fi
    
    # Create virtual environment
    create_venv
    
    # Activate virtual environment
    activate_venv
    
    # Upgrade pip
    upgrade_pip
    
    # Install system dependencies
    install_system_deps
    
    # Install Python dependencies
    install_python_deps
    
    # Install Playwright
    install_playwright
    
    # Setup environment
    setup_env
    
    # Make scripts executable
    make_executable
    
    # Test installation
    test_installation
    
    # Show completion message
    show_completion
}

# Run main function
main "$@"
