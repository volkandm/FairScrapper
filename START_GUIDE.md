# 🚀 FairScrapper API Startup Guide

## 📋 Quick Start

### 🐧 Linux/macOS Users
```bash
./start.sh
```

### 🪟 Windows Users
```cmd
start.bat
```

## ⚙️ Manual Setup (First Time)

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
