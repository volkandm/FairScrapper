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

# Check if virtual environment exists and is valid
check_venv() {
    log_step "Checking virtual environment..."
    
    if [[ -d "$VENV_NAME" ]]; then
        # Check if it's a valid Python virtual environment
        if [[ -f "$VENV_NAME/bin/activate" ]] || [[ -f "$VENV_NAME/Scripts/activate" ]]; then
            log_success "Valid virtual environment found: $VENV_NAME"
            return 0
        else
            log_warning "Invalid virtual environment found, will recreate"
            return 1
        fi
    else
        log_info "No virtual environment found"
        return 1
    fi
}

# Check if Python packages are already installed
check_python_packages() {
    log_step "Checking Python packages..."
    
    if [[ -f "$REQUIREMENTS_FILE" ]]; then
        # Check if packages are installed in current environment
        if python -c "import fastapi, playwright, aiohttp, beautifulsoup4" 2>/dev/null; then
            log_success "Core Python packages already installed"
            return 0
        else
            log_info "Python packages need to be installed"
            return 1
        fi
    else
        log_warning "Requirements file not found: $REQUIREMENTS_FILE"
        return 1
    fi
}

# Check if Playwright browsers are installed
check_playwright() {
    log_step "Checking Playwright browsers..."
    
    if python -c "from playwright.sync_api import sync_playwright" 2>/dev/null; then
        # Check if browsers are installed
        if playwright --version &> /dev/null; then
            log_success "Playwright browsers already installed"
            return 0
        else
            log_info "Playwright installed but browsers missing"
            return 1
        fi
    else
        log_info "Playwright not installed"
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
    
    if check_venv; then
        log_success "Using existing virtual environment: $VENV_NAME"
        return 0
    fi
    
    if [[ -d "$VENV_NAME" ]]; then
        log_warning "Invalid virtual environment found. Removing and recreating..."
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

# Check if system dependencies are already installed
check_system_deps() {
    log_step "Checking system dependencies..."
    
    if [[ "$OS" == "linux" ]]; then
        if command -v apt-get &> /dev/null; then
            # Check if key packages are installed
            if dpkg -l | grep -q "libnss3" && \
               dpkg -l | grep -q "libdrm2" && \
               dpkg -l | grep -q "libxkbcommon0"; then
                log_success "Core system dependencies already installed"
                return 0
            fi
        fi
    fi
    
    log_info "System dependencies need to be installed"
    return 1
}

# Install system dependencies
install_system_deps() {
    log_step "Installing system dependencies..."
    
    if check_system_deps; then
        log_success "System dependencies already installed, skipping..."
        return 0
    fi
    
    if [[ "$OS" == "linux" ]]; then
        # Install system packages required for Playwright
        if command -v apt-get &> /dev/null; then
            # Ubuntu/Debian
            log_info "Installing system dependencies for Playwright on Ubuntu/Debian..."
            sudo apt-get update
            
            # Try to install packages with fallback for different Ubuntu versions
            # Core packages that should work on all versions
            if sudo apt-get install -y \
                libnss3 \
                libdrm2 \
                libxkbcommon0 \
                libxcomposite1 \
                libxdamage1 \
                libxrandr2 \
                libgbm1 \
                libxss1 \
                libgdk-pixbuf2.0-0; then
                log_success "Core system dependencies installed"
            else
                log_warning "Some core dependencies failed to install, continuing..."
            fi
            
            # Try different package name variants for problematic packages
            for pkg in "libatk-bridge2.0-0t64" "libatk-bridge2.0-0"; do
                if sudo apt-get install -y "$pkg" 2>/dev/null; then
                    log_success "Installed $pkg"
                    break
                fi
            done
            
            for pkg in "libasound2t64" "libasound2"; do
                if sudo apt-get install -y "$pkg" 2>/dev/null; then
                    log_success "Installed $pkg"
                    break
                fi
            done
            
            for pkg in "libatspi2.0-0t64" "libatspi2.0-0"; do
                if sudo apt-get install -y "$pkg" 2>/dev/null; then
                    log_success "Installed $pkg"
                    break
                fi
            done
            
            for pkg in "libgtk-3-0t64" "libgtk-3-0"; do
                if sudo apt-get install -y "$pkg" 2>/dev/null; then
                    log_success "Installed $pkg"
                    break
                fi
            done
            
        elif command -v yum &> /dev/null; then
            # CentOS/RHEL
            log_info "Installing system dependencies for Playwright on CentOS/RHEL..."
            if sudo yum install -y \
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
                alsa-lib; then
                log_success "System dependencies installed on CentOS/RHEL"
            else
                log_warning "Some dependencies failed to install on CentOS/RHEL"
            fi
        elif command -v dnf &> /dev/null; then
            # Fedora
            log_info "Installing system dependencies for Playwright on Fedora..."
            if sudo dnf install -y \
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
                alsa-lib; then
                log_success "System dependencies installed on Fedora"
            else
                log_warning "Some dependencies failed to install on Fedora"
            fi
        fi
    elif [[ "$OS" == "macOS" ]]; then
        # macOS dependencies are usually handled by Homebrew
        log_info "macOS dependencies should be handled by Homebrew"
    fi
    
    log_info "System dependency installation completed (some packages may have failed)"
}

# Install Python dependencies
install_python_deps() {
    log_step "Installing Python dependencies..."
    
    if [[ ! -f "$REQUIREMENTS_FILE" ]]; then
        log_error "Requirements file not found: $REQUIREMENTS_FILE"
        exit 1
    fi
    
    if check_python_packages; then
        log_success "Python packages already installed, skipping..."
        return 0
    fi
    
    # Install requirements
    pip install -r "$REQUIREMENTS_FILE"
    log_success "Python dependencies installed"
}

# Install Playwright browsers
install_playwright() {
    log_step "Installing Playwright browsers..."
    
    if check_playwright; then
        log_success "Playwright browsers already installed, skipping..."
        return 0
    fi
    
    # Install Playwright browsers
    playwright install
    
    # Install system dependencies for Playwright
    log_info "Installing Playwright system dependencies..."
    if playwright install-deps; then
        log_success "Playwright system dependencies installed successfully"
    else
        log_warning "Playwright install-deps failed, but browsers are installed"
        log_info "You may need to install system dependencies manually if you encounter issues"
    fi
    
    log_success "Playwright browsers installed"
}

# Create environment file
setup_env() {
    log_step "Setting up environment configuration..."
    
    if [[ -f "$ENV_FILE" ]]; then
        log_success "Environment file already exists: $ENV_FILE"
        return 0
    fi
    
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
    if python -c "import fastapi, playwright, aiohttp, beautifulsoup4; print('All imports successful')" 2>/dev/null; then
        log_success "Python imports test passed"
    else
        log_error "Python imports test failed"
        return 1
    fi
    
    # Test Playwright (this might fail if system deps are missing)
    if python -c "from playwright.sync_api import sync_playwright; print('Playwright import successful')" 2>/dev/null; then
        log_success "Playwright import test passed"
    else
        log_warning "Playwright import test failed - this is normal if system dependencies are missing"
    fi
    
    log_success "Installation test completed"
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
    echo -e "${YELLOW}⚠️  Troubleshooting:${NC}"
    echo -e "   If you encounter Playwright issues, try:"
    echo -e "   ${BLUE}playwright install-deps${NC}"
    echo -e "   ${BLUE}playwright install chromium${NC}"
    echo
    echo -e "   For Ubuntu/Debian, you may need:"
    echo -e "   ${BLUE}sudo apt-get install libasound2t64 libatk-bridge2.0-0t64 libgtk-3-0t64${NC}"
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
    
    # Create virtual environment (only if needed)
    create_venv
    
    # Activate virtual environment
    activate_venv
    
    # Upgrade pip (always do this)
    upgrade_pip
    
    # Install system dependencies (only if needed)
    install_system_deps
    
    # Install Python dependencies (only if needed)
    install_python_deps
    
    # Install Playwright (only if needed)
    install_playwright
    
    # Setup environment (only if needed)
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
