# SSL/HTTPS Setup Guide for FairScrapper API

This guide explains how to set up and use HTTPS/SSL certificates with FairScrapper API.

## 🔒 Overview

FairScrapper supports HTTPS for secure API communication. By default, the installation script generates self-signed SSL certificates for development and testing purposes.

## 📋 Table of Contents

- [Quick Start](#quick-start)
- [Automated Setup](#automated-setup)
- [Manual Setup](#manual-setup)
- [Configuration](#configuration)
- [Using HTTPS](#using-https)
- [Production Deployment](#production-deployment)
- [Troubleshooting](#troubleshooting)

## 🚀 Quick Start

The easiest way to enable HTTPS is through the automated installation:

```bash
# Full installation (includes SSL setup)
./install.sh

# Or just SSL setup
./install_ssl.sh
```

This automatically:
- Generates a 4096-bit RSA private key
- Creates a self-signed certificate valid for 365 days
- Sets proper file permissions
- Updates your `.env` configuration

## 🔧 SSL-Only Installation

If you only want to setup/regenerate SSL certificates:

```bash
# Basic usage
./install_ssl.sh

# Interactive mode (customize certificate details)
./install_ssl.sh --interactive

# Force regeneration (overwrite existing certificates)
./install_ssl.sh --force

# Show help
./install_ssl.sh --help
```

## 🔧 Automated Setup

### Step 1: Run Installation Script

```bash
./install.sh
```

The script will:
1. Check if OpenSSL is installed (installs if missing)
2. Create `./ssl/` directory
3. Generate certificate and key files
4. Set secure file permissions:
   - `ssl/key.pem`: 600 (read/write for owner only)
   - `ssl/cert.pem`: 644 (readable by all, writable by owner)

### Step 2: Verify Installation

Check that certificates were created:

```bash
ls -la ssl/
# Should show:
# -rw-r--r-- 1 user group 2065 Jan 10 12:00 cert.pem
# -rw------- 1 user group 3272 Jan 10 12:00 key.pem
```

View certificate details:

```bash
openssl x509 -in ssl/cert.pem -noout -text
```

### Step 3: Start the API

```bash
./start.sh
```

The API will start with HTTPS enabled on port 8888 (or your configured port).

## 🛠️ Manual Setup

If you need to manually generate SSL certificates:

### Step 1: Install OpenSSL

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install openssl
```

**CentOS/RHEL:**
```bash
sudo yum install openssl
```

**macOS:**
```bash
brew install openssl
```

### Step 2: Create SSL Directory

```bash
mkdir -p ssl
cd ssl
```

### Step 3: Generate Self-Signed Certificate

```bash
openssl req -x509 -newkey rsa:4096 -nodes \
    -out cert.pem \
    -keyout key.pem \
    -days 365 \
    -subj "/C=US/ST=State/L=City/O=FairScrapper/OU=API/CN=localhost"
```

**Parameters explained:**
- `-x509`: Output a self-signed certificate
- `-newkey rsa:4096`: Create a new 4096-bit RSA key
- `-nodes`: Don't encrypt the private key (no password)
- `-days 365`: Certificate validity period (1 year)
- `-subj`: Certificate subject information

### Step 4: Set File Permissions

```bash
chmod 600 key.pem    # Private key: owner read/write only
chmod 644 cert.pem   # Certificate: readable by all
```

### Step 5: Configure Environment

Edit `.env` file:

```env
SSL_ENABLED=true
SSL_CERT_FILE=./ssl/cert.pem
SSL_KEY_FILE=./ssl/key.pem
```

## ⚙️ Configuration

### Environment Variables

Add these to your `.env` file:

```env
# Enable/disable SSL
SSL_ENABLED=true

# Certificate files
SSL_CERT_FILE=./ssl/cert.pem
SSL_KEY_FILE=./ssl/key.pem

# API settings
API_HOST=0.0.0.0
API_PORT=8888
```

### Disable HTTPS

To use HTTP only:

```env
SSL_ENABLED=false
```

## 🌐 Using HTTPS

### With curl

```bash
# Ignore self-signed certificate warning with -k flag
curl -X POST https://localhost:8888/health \
     -H "X-API-Key: sk-demo-key-12345" \
     -k

# Or use full certificate verification (will fail with self-signed)
curl -X POST https://localhost:8888/health \
     -H "X-API-Key: sk-demo-key-12345" \
     --cacert ssl/cert.pem
```

### With Python requests

```python
import requests

# Ignore SSL verification (self-signed certificate)
response = requests.post(
    'https://localhost:8888/health',
    headers={'X-API-Key': 'sk-demo-key-12345'},
    verify=False  # Ignore SSL certificate
)

# Or specify certificate file
response = requests.post(
    'https://localhost:8888/health',
    headers={'X-API-Key': 'sk-demo-key-12345'},
    verify='./ssl/cert.pem'
)
```

### With Browser

1. Navigate to `https://localhost:8888/docs`
2. Browser will show a security warning (self-signed certificate)
3. Click "Advanced" → "Proceed to localhost" (Chrome)
4. Or "Accept the Risk and Continue" (Firefox)

### With Postman/Insomnia

1. Open settings
2. Disable "SSL certificate verification"
3. Make requests to `https://localhost:8888`

## 🏭 Production Deployment

### Using Let's Encrypt (Recommended)

For production, use proper SSL certificates from Let's Encrypt:

```bash
# Install Certbot
sudo apt-get update
sudo apt-get install certbot

# Generate certificates (replace yourdomain.com)
sudo certbot certonly --standalone -d yourdomain.com

# Certificates will be stored in:
# /etc/letsencrypt/live/yourdomain.com/fullchain.pem
# /etc/letsencrypt/live/yourdomain.com/privkey.pem
```

Update `.env`:

```env
SSL_ENABLED=true
SSL_CERT_FILE=/etc/letsencrypt/live/yourdomain.com/fullchain.pem
SSL_KEY_FILE=/etc/letsencrypt/live/yourdomain.com/privkey.pem
```

### Auto-renewal

Set up automatic certificate renewal:

```bash
# Test renewal
sudo certbot renew --dry-run

# Add to crontab
sudo crontab -e

# Add this line to renew twice daily
0 0,12 * * * certbot renew --quiet
```

### Using Commercial SSL

If you have a commercial SSL certificate:

1. Copy your certificate and key files to `./ssl/`
2. Update `.env`:

```env
SSL_ENABLED=true
SSL_CERT_FILE=./ssl/your-certificate.pem
SSL_KEY_FILE=./ssl/your-private-key.pem
```

## 🔍 Troubleshooting

### Certificate Not Found Error

**Error:**
```
❌ SSL files not found! Please run install.sh to generate SSL certificates.
```

**Solution:**
```bash
# Run installation script
./install.sh

# Or generate manually
mkdir -p ssl
openssl req -x509 -newkey rsa:4096 -nodes -out ssl/cert.pem -keyout ssl/key.pem -days 365
```

### Permission Denied Error

**Error:**
```
Permission denied: ssl/key.pem
```

**Solution:**
```bash
# Fix permissions
chmod 600 ssl/key.pem
chmod 644 ssl/cert.pem
```

### OpenSSL Not Found

**Error:**
```
OpenSSL not found
```

**Solution:**
```bash
# Ubuntu/Debian
sudo apt-get install openssl

# CentOS/RHEL
sudo yum install openssl

# macOS
brew install openssl
```

### Certificate Expired

**Error:**
```
SSL certificate has expired
```

**Solution:**
```bash
# Remove old certificates
rm ssl/cert.pem ssl/key.pem

# Generate new ones
openssl req -x509 -newkey rsa:4096 -nodes \
    -out ssl/cert.pem \
    -keyout ssl/key.pem \
    -days 365 \
    -subj "/C=US/ST=State/L=City/O=FairScrapper/OU=API/CN=localhost"
```

### Port Already in Use

**Error:**
```
Address already in use: port 8888
```

**Solution:**
```bash
# Find process using the port
lsof -i :8888

# Kill the process
kill -9 <PID>

# Or use a different port in .env
API_PORT=8889
```

## 📝 Certificate Information

### View Certificate Details

```bash
# View full certificate
openssl x509 -in ssl/cert.pem -text -noout

# View expiration date
openssl x509 -in ssl/cert.pem -noout -dates

# View subject
openssl x509 -in ssl/cert.pem -noout -subject

# View issuer
openssl x509 -in ssl/cert.pem -noout -issuer
```

### Certificate Validity

Default self-signed certificates are valid for **365 days**.

To generate a certificate with different validity:

```bash
# 2 years validity
openssl req -x509 -newkey rsa:4096 -nodes \
    -out ssl/cert.pem \
    -keyout ssl/key.pem \
    -days 730 \
    -subj "/C=US/ST=State/L=City/O=FairScrapper/OU=API/CN=localhost"
```

## 🔐 Security Best Practices

### Development/Testing
- ✅ Self-signed certificates are acceptable
- ✅ Use `-k` flag with curl to ignore warnings
- ✅ Disable SSL verification in client code

### Production
- ❌ Never use self-signed certificates
- ✅ Use Let's Encrypt or commercial CA certificates
- ✅ Enable auto-renewal
- ✅ Use proper domain names (not localhost)
- ✅ Keep private keys secure (600 permissions)
- ✅ Never commit private keys to git
- ✅ Regularly update certificates before expiration

### File Permissions

```bash
# Private key: Owner read/write only
chmod 600 ssl/key.pem

# Certificate: Readable by all, writable by owner
chmod 644 ssl/cert.pem

# Directory: Owner full access, others read/execute
chmod 755 ssl
```

## 📚 Additional Resources

- [OpenSSL Documentation](https://www.openssl.org/docs/)
- [Let's Encrypt Documentation](https://letsencrypt.org/docs/)
- [SSL/TLS Best Practices](https://github.com/ssllabs/research/wiki/SSL-and-TLS-Deployment-Best-Practices)
- [Mozilla SSL Configuration Generator](https://ssl-config.mozilla.org/)

## 💡 Tips

1. **Development**: Use self-signed certificates with SSL verification disabled
2. **Staging**: Use Let's Encrypt certificates for testing
3. **Production**: Use Let's Encrypt or commercial certificates with auto-renewal
4. **Monitoring**: Set up alerts for certificate expiration
5. **Backup**: Keep backup copies of your certificates and keys (securely)

## 📞 Support

For issues or questions:
- 📧 Email: volkan@designmonkeys.net
- 📖 Documentation: [README.md](README.md)
- 🐛 Issues: Report via GitHub or email

---

**Author:** Volkan AYDIN  
**Year:** 2025  
**License:** CC BY-NC-SA 4.0 (Non-Commercial)

