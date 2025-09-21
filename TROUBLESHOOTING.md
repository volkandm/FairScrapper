# 🔧 FairScrapper API - Troubleshooting Guide

## 🚨 Common Installation Issues

### 1. **Ubuntu/Debian Package Errors**

#### Problem: `Package 'libasound2' has no installation candidate`

**Solution:**
```bash
# Try the new package names
sudo apt-get update
sudo apt-get install -y libasound2t64 libatk-bridge2.0-0t64 libgtk-3-0t64

# Or install manually
sudo apt-get install -y \
    libnss3 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    libgbm1 \
    libxss1 \
    libgdk-pixbuf2.0-0
```

#### Problem: `libatk-bridge2.0-0` not found

**Solution:**
```bash
# Try different package name variants
sudo apt-get install -y libatk-bridge2.0-0t64 || \
sudo apt-get install -y libatk-bridge2.0-0
```

### 2. **Playwright Browser Issues**

#### Problem: Playwright browsers not working

**Solution:**
```bash
# Reinstall Playwright browsers
playwright install

# Install system dependencies
playwright install-deps

# Install specific browser
playwright install chromium
```

#### Problem: `playwright install-deps` fails

**Solution:**
```bash
# Manual installation for Ubuntu/Debian
sudo apt-get update
sudo apt-get install -y \
    libnss3 \
    libatk-bridge2.0-0t64 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    libgbm1 \
    libxss1 \
    libasound2t64 \
    libatspi2.0-0t64 \
    libgtk-3-0t64 \
    libgdk-pixbuf2.0-0
```

### 3. **Python Virtual Environment Issues**

#### Problem: Virtual environment not activating

**Solution:**
```bash
# Remove old virtual environment
rm -rf venv

# Create new one
python3 -m venv venv
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

#### Problem: `python3` not found

**Solution:**
```bash
# Install Python 3
sudo apt-get update
sudo apt-get install -y python3 python3-pip python3-venv

# Or on Ubuntu 20.04+
sudo apt-get install -y python3.8 python3.8-pip python3.8-venv
```

### 4. **Permission Issues**

#### Problem: Permission denied when running scripts

**Solution:**
```bash
# Make scripts executable
chmod +x install.sh start.sh stop.sh

# Run with proper permissions
./install.sh
```

#### Problem: `sudo` required for system packages

**Solution:**
```bash
# Add user to sudoers (if not already)
sudo usermod -aG sudo $USER

# Log out and back in, then try again
```

### 5. **Network Issues**

#### Problem: Package download fails

**Solution:**
```bash
# Update package lists
sudo apt-get update

# Clear package cache
sudo apt-get clean
sudo apt-get autoclean

# Try different mirror
sudo apt-get update --fix-missing
```

#### Problem: Playwright download fails

**Solution:**
```bash
# Set proxy if needed
export HTTP_PROXY=http://proxy:port
export HTTPS_PROXY=http://proxy:port

# Try again
playwright install
```

### 6. **API Startup Issues**

#### Problem: API won't start

**Solution:**
```bash
# Check if port is in use
sudo netstat -tlnp | grep :8888

# Kill process using port
sudo kill -9 $(sudo lsof -t -i:8888)

# Try different port in .env
echo "API_PORT=8889" >> .env
```

#### Problem: Module not found errors

**Solution:**
```bash
# Activate virtual environment
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt

# Check Python path
which python
python --version
```

## 🛠️ Manual Installation Steps

If the automated script fails, try manual installation:

### 1. **System Dependencies**

```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    python3-dev \
    libnss3 \
    libatk-bridge2.0-0t64 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    libgbm1 \
    libxss1 \
    libasound2t64 \
    libatspi2.0-0t64 \
    libgtk-3-0t64 \
    libgdk-pixbuf2.0-0
```

### 2. **Python Environment**

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Upgrade pip
python -m pip install --upgrade pip

# Install Python packages
pip install -r requirements.txt
```

### 3. **Playwright Setup**

```bash
# Install Playwright
playwright install

# Install system dependencies
playwright install-deps
```

### 4. **Configuration**

```bash
# Create environment file
cp env_example.txt .env

# Edit configuration
nano .env
```

### 5. **Test Installation**

```bash
# Test Python imports
python -c "import fastapi, playwright, aiohttp, beautifulsoup4; print('All imports successful')"

# Test Playwright
python -c "from playwright.sync_api import sync_playwright; print('Playwright test successful')"

# Start API
python api.py
```

## 🔍 Debugging Commands

### Check System Information
```bash
# OS version
cat /etc/os-release

# Python version
python3 --version

# Available packages
apt list --installed | grep -E "(libnss3|libatk|libgtk|libasound)"
```

### Check Playwright Status
```bash
# List installed browsers
playwright --version

# Test browser installation
playwright install --dry-run
```

### Check API Status
```bash
# Test API health
curl -X POST http://localhost:8888/health \
     -H "X-API-Key: sk-demo-key-12345"

# Check API logs
tail -f api.log
```

## 📞 Getting Help

If you're still having issues:

1. **Check the logs** for specific error messages
2. **Try manual installation** steps above
3. **Check system requirements** (Python 3.8+, supported OS)
4. **Contact support** with:
   - OS version (`cat /etc/os-release`)
   - Python version (`python3 --version`)
   - Error messages from logs
   - Steps you've already tried

### Support Channels
- **GitHub:** [volkandm](https://github.com/volkandm)
- **Email:** volkan@designmonkeys.net

---

**Made with ❤️ by Volkan AYDIN**

*Supporting ethical and fair web scraping technology since 2025*
