#!/bin/bash

# 🔒 FairScrapper SSL Certificate Setup Script
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
SSL_DIR="ssl"
CERT_FILE="$SSL_DIR/cert.pem"
KEY_FILE="$SSL_DIR/key.pem"
CERT_VALIDITY_DAYS=365

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

# Check if OpenSSL is installed
check_openssl() {
    if command -v openssl &> /dev/null; then
        OPENSSL_VERSION=$(openssl version 2>&1 | cut -d' ' -f2)
        log_success "OpenSSL $OPENSSL_VERSION found"
        return 0
    else
        log_warning "OpenSSL not found"
        return 1
    fi
}

# Install OpenSSL
install_openssl() {
    log_step "Installing OpenSSL..."
    
    # Detect OS
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        if command -v apt-get &> /dev/null; then
            # Ubuntu/Debian
            sudo apt-get update
            sudo apt-get install -y openssl
        elif command -v yum &> /dev/null; then
            # CentOS/RHEL
            sudo yum install -y openssl
        elif command -v dnf &> /dev/null; then
            # Fedora
            sudo dnf install -y openssl
        elif command -v pacman &> /dev/null; then
            # Arch Linux
            sudo pacman -S --noconfirm openssl
        else
            log_error "Unsupported Linux distribution. Please install OpenSSL manually."
            return 1
        fi
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        if command -v brew &> /dev/null; then
            brew install openssl
        else
            log_error "Homebrew not found. Please install OpenSSL manually."
            return 1
        fi
    else
        log_error "Unsupported operating system: $OSTYPE"
        return 1
    fi
    
    # Verify installation
    if check_openssl; then
        log_success "OpenSSL installation completed successfully"
        return 0
    else
        log_error "OpenSSL installation failed"
        return 1
    fi
}

# Check if certificates already exist
check_existing_certificates() {
    if [[ -f "$CERT_FILE" ]] && [[ -f "$KEY_FILE" ]]; then
        log_info "Existing SSL certificates found:"
        log_info "  📜 Certificate: $CERT_FILE"
        log_info "  🔑 Private key: $KEY_FILE"
        
        # Check certificate expiration
        if openssl x509 -in "$CERT_FILE" -noout -checkend 0 &> /dev/null; then
            # Certificate is still valid
            EXPIRY_DATE=$(openssl x509 -in "$CERT_FILE" -noout -enddate 2>/dev/null | cut -d= -f2)
            log_success "Certificate is valid until: $EXPIRY_DATE"
            
            # Ask user if they want to regenerate
            echo ""
            read -p "$(echo -e ${YELLOW}Do you want to regenerate certificates? [y/N]:${NC} )" -n 1 -r
            echo
            if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                log_info "Keeping existing certificates"
                return 0
            fi
        else
            log_warning "Certificate has expired!"
            log_info "Regenerating certificates..."
        fi
    fi
    
    return 1
}

# Generate SSL certificate
generate_certificate() {
    log_step "Generating SSL certificate..."
    
    # Create SSL directory if it doesn't exist
    if [[ ! -d "$SSL_DIR" ]]; then
        mkdir -p "$SSL_DIR"
        log_info "Created SSL directory: $SSL_DIR"
    fi
    
    # Get certificate information
    echo ""
    log_info "Certificate will be generated with the following details:"
    
    # Default values
    COUNTRY="${SSL_COUNTRY:-US}"
    STATE="${SSL_STATE:-State}"
    CITY="${SSL_CITY:-City}"
    ORG="${SSL_ORG:-FairScrapper}"
    ORG_UNIT="${SSL_ORG_UNIT:-API}"
    COMMON_NAME="${SSL_COMMON_NAME:-localhost}"
    
    # Interactive mode (optional)
    if [[ "$1" == "--interactive" ]] || [[ "$1" == "-i" ]]; then
        read -p "Country (2 letter code) [$COUNTRY]: " input
        COUNTRY="${input:-$COUNTRY}"
        
        read -p "State/Province [$STATE]: " input
        STATE="${input:-$STATE}"
        
        read -p "City [$CITY]: " input
        CITY="${input:-$CITY}"
        
        read -p "Organization [$ORG]: " input
        ORG="${input:-$ORG}"
        
        read -p "Organization Unit [$ORG_UNIT]: " input
        ORG_UNIT="${input:-$ORG_UNIT}"
        
        read -p "Common Name (domain/IP) [$COMMON_NAME]: " input
        COMMON_NAME="${input:-$COMMON_NAME}"
    fi
    
    echo ""
    log_info "Generating certificate with:"
    log_info "  Country: $COUNTRY"
    log_info "  State: $STATE"
    log_info "  City: $CITY"
    log_info "  Organization: $ORG"
    log_info "  Unit: $ORG_UNIT"
    log_info "  Common Name: $COMMON_NAME"
    log_info "  Validity: $CERT_VALIDITY_DAYS days"
    echo ""
    
    # Generate self-signed certificate
    openssl req -x509 -newkey rsa:4096 -nodes \
        -out "$CERT_FILE" \
        -keyout "$KEY_FILE" \
        -days "$CERT_VALIDITY_DAYS" \
        -subj "/C=$COUNTRY/ST=$STATE/L=$CITY/O=$ORG/OU=$ORG_UNIT/CN=$COMMON_NAME" \
        2>/dev/null
    
    if [[ -f "$CERT_FILE" ]] && [[ -f "$KEY_FILE" ]]; then
        log_success "SSL certificates generated successfully!"
        
        # Set proper permissions
        chmod 600 "$KEY_FILE"
        chmod 644 "$CERT_FILE"
        log_success "File permissions set correctly"
        
        # Display certificate information
        echo ""
        log_info "📁 Certificate location:"
        log_info "   • Certificate: $CERT_FILE"
        log_info "   • Private key: $KEY_FILE"
        log_info "   • Validity: $CERT_VALIDITY_DAYS days"
        
        echo ""
        log_info "📜 Certificate details:"
        openssl x509 -in "$CERT_FILE" -noout -subject -dates 2>/dev/null | while IFS= read -r line; do
            log_info "   $line"
        done
        
        return 0
    else
        log_error "Failed to generate SSL certificates"
        return 1
    fi
}

# Update .env file
update_env_file() {
    log_step "Updating .env configuration..."
    
    ENV_FILE=".env"
    
    if [[ ! -f "$ENV_FILE" ]]; then
        log_warning ".env file not found"
        
        if [[ -f "env_example.txt" ]]; then
            log_info "Creating .env from env_example.txt..."
            cp env_example.txt "$ENV_FILE"
            log_success ".env file created"
        else
            log_info "Creating default .env file..."
            cat > "$ENV_FILE" << EOF
# API Configuration
API_HOST=127.0.0.1
API_PORT=8888

# SSL/HTTPS Configuration
SSL_ENABLED=true
SSL_CERT_FILE=./$CERT_FILE
SSL_KEY_FILE=./$KEY_FILE

# API Security
VALID_API_KEYS=sk-demo-key-12345,sk-test-key-67890
EOF
            log_success "Default .env file created"
        fi
    else
        # Check if SSL configuration exists
        if grep -q "SSL_ENABLED" "$ENV_FILE"; then
            log_info "SSL configuration already exists in .env"
        else
            log_info "Adding SSL configuration to .env..."
            echo "" >> "$ENV_FILE"
            echo "# SSL/HTTPS Configuration" >> "$ENV_FILE"
            echo "SSL_ENABLED=true" >> "$ENV_FILE"
            echo "SSL_CERT_FILE=./$CERT_FILE" >> "$ENV_FILE"
            echo "SSL_KEY_FILE=./$KEY_FILE" >> "$ENV_FILE"
            log_success "SSL configuration added to .env"
        fi
    fi
}

# Display usage instructions
show_usage() {
    echo ""
    log_info "📚 Usage instructions:"
    echo ""
    echo -e "${CYAN}1. Start the API server:${NC}"
    echo -e "   ${BLUE}./start.sh${NC}"
    echo ""
    echo -e "${CYAN}2. Test HTTPS connection:${NC}"
    echo -e "   ${BLUE}curl -X POST https://localhost:8888/health -H 'X-API-Key: sk-demo-key-12345' -k${NC}"
    echo ""
    echo -e "${CYAN}3. View certificate details:${NC}"
    echo -e "   ${BLUE}openssl x509 -in $CERT_FILE -text -noout${NC}"
    echo ""
    echo -e "${CYAN}4. Check certificate expiration:${NC}"
    echo -e "   ${BLUE}openssl x509 -in $CERT_FILE -noout -dates${NC}"
    echo ""
    echo -e "${YELLOW}⚠️  Note:${NC}"
    echo -e "   • This is a self-signed certificate for development/testing"
    echo -e "   • For production, use Let's Encrypt or commercial CA certificates"
    echo -e "   • Browsers will show security warnings for self-signed certificates"
    echo -e "   • Use ${BLUE}-k${NC} flag with curl to ignore SSL verification"
    echo ""
}

# Display completion message
show_completion() {
    echo ""
    echo -e "${GREEN}🎉 SSL Certificate Setup Completed!${NC}"
    echo ""
    echo -e "${PURPLE}🔒 SSL/HTTPS is now configured for FairScrapper API${NC}"
    echo ""
    show_usage
}

# Main function
main() {
    echo -e "${PURPLE}🔒 FairScrapper SSL Certificate Setup${NC}"
    echo -e "${PURPLE}======================================${NC}"
    echo ""
    
    # Parse arguments
    INTERACTIVE=false
    FORCE=false
    
    for arg in "$@"; do
        case $arg in
            -i|--interactive)
                INTERACTIVE=true
                ;;
            -f|--force)
                FORCE=true
                ;;
            -h|--help)
                echo "Usage: $0 [OPTIONS]"
                echo ""
                echo "Options:"
                echo "  -i, --interactive   Interactive mode (ask for certificate details)"
                echo "  -f, --force         Force regeneration (skip existing certificate check)"
                echo "  -h, --help          Show this help message"
                echo ""
                exit 0
                ;;
        esac
    done
    
    # Check if OpenSSL is installed
    if ! check_openssl; then
        install_openssl || exit 1
    fi
    
    # Check existing certificates (unless force flag is used)
    if [[ "$FORCE" != true ]] && check_existing_certificates; then
        show_usage
        exit 0
    fi
    
    # Generate certificate
    if [[ "$INTERACTIVE" == true ]]; then
        generate_certificate --interactive || exit 1
    else
        generate_certificate || exit 1
    fi
    
    # Update .env file
    update_env_file
    
    # Show completion message
    show_completion
}

# Run main function
main "$@"

