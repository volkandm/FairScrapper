# 🚀 FairScrapper API Startup Guide

## 📋 Quick Start

### 🚀 **Automated Installation (Recommended)**

First, run the installation script to set up everything automatically:

```bash
# Make scripts executable
chmod +x install.sh start.sh stop.sh

# Run automated installation
./install.sh

# Start the API
./start.sh
```

### 🐧 **Manual Start (Linux/macOS)**
```bash
./start.sh
```

### 🪟 **Manual Start (Windows)**
```cmd
start.bat
```

## ⚙️ Manual Setup (First Time)

**Note:** If you used the automated installation script (`./install.sh`), you can skip this section.

### 1. Create Virtual Environment
```bash
# Linux/macOS
python3 -m venv venv
source venv/bin/activate

# Windows
python -m venv venv
venv\Scripts\activate
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Install Playwright Browsers
```bash
playwright install
```

### 4. Install System Dependencies (Linux)
```bash
# Ubuntu/Debian
sudo apt-get install libnss3 libatk-bridge2.0-0 libdrm2 libxkbcommon0 libxcomposite1 libxdamage1 libxrandr2 libgbm1 libxss1 libasound2

# CentOS/RHEL
sudo yum install nss atk at-spi2-atk gtk3 libdrm libxkbcommon libXcomposite libXdamage libXrandr mesa-libgbm libXScrnSaver alsa-lib

# Fedora
sudo dnf install nss atk at-spi2-atk gtk3 libdrm libxkbcommon libXcomposite libXdamage libXrandr mesa-libgbm libXScrnSaver alsa-lib
```

## 🔧 Configuration

### .env File Settings
```env
# Server Settings
API_HOST=127.0.0.1    # Local: 127.0.0.1, Remote: 0.0.0.0
API_PORT=8888         # Your preferred port

# Proxy Settings
PROXY_ENABLED=true
PROXY_LIST=http://proxy1:8080,http://proxy2:8080

# API Security
VALID_API_KEYS=your-api-key-here
```

## 🌐 Server Types

### 🏠 Local Development
```env
API_HOST=127.0.0.1
API_PORT=8888
```
- **URL:** http://127.0.0.1:8888
- **Docs:** http://127.0.0.1:8888/docs

### 🌍 Production Server
```env
API_HOST=0.0.0.0
API_PORT=8888
```
- **URL:** http://your-server-ip:8888
- **Docs:** http://your-server-ip:8888/docs

## 📱 API Usage

### Health Check
```bash
curl -X POST "http://localhost:8888/health" \
     -H "X-API-Key: sk-demo-key-12345"
```

### Web Scraping
```bash
# Basic scraping
curl -X POST "http://localhost:8888/scrape" \
     -H "Content-Type: application/json" \
     -H "X-API-Key: sk-demo-key-12345" \
     -d '{
       "url": "https://example.com",
       "use_proxy": false,
       "get": {
         "title": "h1",
         "description": "meta[name=description](content)"
       }
     }'

# Image scraping with base64 extraction
curl -X POST "http://localhost:8888/scrape" \
     -H "Content-Type: application/json" \
     -H "X-API-Key: sk-demo-key-12345" \
     -d '{
       "url": "https://example-store.com/product",
       "use_proxy": true,
       "get": {
         "product_image": "img.product-image",
         "gallery_image": "img(src)"
       },
       "collect": {
         "gallery": {
           "selector": ".gallery img",
           "fields": {
             "image": "img"
           }
         }
       }
     }'

# Advanced navigation with query builder
curl -X POST "http://localhost:8888/scrape" \
     -H "Content-Type: application/json" \
     -H "X-API-Key: sk-demo-key-12345" \
     -d '{
       "url": "https://example.com/products",
       "use_proxy": true,
       "get": {
         "parent_title": "a.product-link<.product-card>h2",
         "sibling_price": ".current+.price",
         "link_url": "a(href)",
         "image_src": "img(src)"
       },
       "collect": {
         "products": {
           "selector": ".product-item",
           "fields": {
             "name": "h3",
             "price": ".price",
             "link": "a(href)",
             "image": "img(src)",
             "parent_category": ".item<.category>h4",
             "wildcard_link": "* a(href)"
           }
         }
       }
     }'
```

## 🛠️ Troubleshooting

### ❌ "Virtual environment not found"
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### ❌ "Python packages missing"
```bash
source venv/bin/activate
pip install -r requirements.txt
```

### ❌ "Playwright browsers missing"
```bash
source venv/bin/activate
playwright install
```

### ❌ "Port already in use"
Use a different port in `.env` file:
```env
API_PORT=8889
```

## 🖼️ New Features (2025)

### **Image Scraping**
- ✅ **Base64 extraction** - Images returned as data URLs
- ✅ **Size limits** - 5MB maximum protection
- ✅ **Multiple formats** - JPEG, PNG, WebP support
- ✅ **Browser extraction** - Direct from loaded images
- ✅ **URL fallback** - Downloads if browser extraction fails

### **Advanced Selectors**
- ✅ **Query Builder** - Parent (`<`), Child (`>`), Sibling (`+`) navigation
- ✅ **Attribute extraction** - `a(href)`, `img(src)`, `.element(data-value)`
- ✅ **Wildcard navigation** - `* a(href)` finds in any ancestor
- ✅ **Complex chains** - `a.test<.product_pod<section>div.alert>strong`

### **Enhanced Collection**
- ✅ **Multiple fields** - Extract various data from each item
- ✅ **Image collections** - Extract multiple images as base64
- ✅ **Parent navigation** - `.child<div<div>h1` syntax
- ✅ **Sibling navigation** - `.current+.next` syntax

## 📊 Script Features

### ✅ Automatic Checks
- Virtual environment existence
- Python packages
- Playwright browsers
- Environment variables

### 🎯 Smart Startup
- Automatic virtual environment activation
- Missing dependency detection
- User-friendly error messages
- Detailed startup information

### 🔒 Security
- Secure environment variable reading
- Default values
- Safe exit on error conditions

## 📞 Support

- **GitHub:** [volkandm](https://github.com/volkandm)
- **Email:** volkan@designmonkeys.net
- **Bitcoin:** bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh

---

**Made with ❤️ by Volkan AYDIN**
