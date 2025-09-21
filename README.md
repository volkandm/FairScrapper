# FairScrapper

A powerful and ethical web scraping API built with FastAPI and Playwright, featuring proxy rotation and comprehensive error handling.

## 🎯 FairScrapper - Fair Web Scraping Platform

FairScrapper provides a sustainable web scraping solution with proxy rotation and ethical scraping practices.

## Table of Contents

- [Features](#features)
- [Quick Start](#quick-start)
- [Installation](#installation)
- [Configuration](#configuration)
- [API Documentation](#api-documentation)
- [Advanced Selector Syntax](#advanced-selector-syntax)
- [Examples](#examples)
- [Deployment](#deployment)
- [Author](#author)
- [License](#license)
- [Commercial License](#commercial-license)
- [Donations & Support](#donations--support)
- [Contact](#contact)

## Features

✨ **Core Features**
- 🎯 Unified API with `get` and `collect` operations
- 🔍 Advanced CSS selector syntax with parent navigation
- 📦 Attribute extraction support
- 🌐 Proxy rotation and load balancing
- 📸 Screenshot capabilities
- 🐛 Debug mode with HTML output
- ⚡ High-performance async operations
- ⚖️ Ethical scraping practices
- 🔄 Automatic proxy rotation
- 🛡️ Rate limiting and fair use

🎨 **Advanced Selector Syntax**
- Standard CSS selectors
- Attribute extraction: `selector(attribute)`
- Parent navigation: `selector<parent1<parent2>target`
- Ancestor navigation: `>> selector`, `* selector`, `parent selector`

## Quick Start

### 🚀 **Automated Installation (Recommended)**

1. **Run the installation script:**
   ```bash
   ./install.sh
   ```

2. **Start the API:**
   ```bash
   ./start.sh
   ```

3. **Test the installation:**
   ```bash
   curl -X POST "http://localhost:8888/health" \
        -H "X-API-Key: sk-demo-key-12345"
   ```

### 📋 **Manual Installation**

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   playwright install
   ```

2. **Start the API:**
   ```bash
   python api.py
   ```

3. **Make your first request:**
   ```bash
   curl -X POST "http://localhost:8888/scrape" \
        -H "Content-Type: application/json" \
        -H "X-API-Key: sk-demo-key-12345" \
        -d '{
          "url": "https://example.com",
          "use_proxy": false,
          "wait_time": 2,
          "get": {
            "title": "h1",
            "description": "meta[name=description](content)"
          }
        }'
   ```

## Installation

### 🚀 **Automated Installation (Recommended)**

The easiest way to get started is using our automated installation script:

```bash
# Make the script executable
chmod +x install.sh

# Run the installation
./install.sh
```

**What the script does:**
- ✅ Checks and installs Python 3.8+ if needed
- ✅ Creates virtual environment
- ✅ Installs all Python dependencies
- ✅ Installs Playwright browsers and system dependencies
- ✅ Sets up environment configuration
- ✅ Makes all scripts executable
- ✅ Tests the installation

**Supported Operating Systems:**
- 🐧 **Linux** (Ubuntu, Debian, CentOS, RHEL, Fedora, Arch)
- 🍎 **macOS** (with Homebrew)

### 📋 **Manual Installation**

If you prefer manual installation or the automated script doesn't work:

#### Prerequisites

- Python 3.8+
- Node.js (for Playwright browsers)

#### Step-by-Step Installation

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd scraper
   ```

2. **Create virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Install Playwright browsers:**
   ```bash
   playwright install
   ```

5. **Install system dependencies (Linux):**
   ```bash
   # Ubuntu/Debian
   sudo apt-get install libnss3 libatk-bridge2.0-0 libdrm2 libxkbcommon0 libxcomposite1 libxdamage1 libxrandr2 libgbm1 libxss1 libasound2
   
   # CentOS/RHEL
   sudo yum install nss atk at-spi2-atk gtk3 libdrm libxkbcommon libXcomposite libXdamage libXrandr mesa-libgbm libXScrnSaver alsa-lib
   ```

6. **Configure environment (optional):**
   ```bash
   cp env_example.txt .env
   # Edit .env with your settings
   ```

7. **Start the application:**
   ```bash
   python api.py
   ```

The API will be available at `http://localhost:8888` (or your domain)

## Configuration

### Environment Variables

Create a `.env` file based on `env_example.txt`:

```env
# API Configuration
API_HOST=0.0.0.0
API_PORT=8888
DEBUG=False

# Browser Configuration
HEADLESS=True
TIMEOUT=30000
VIEWPORT_WIDTH=1920
VIEWPORT_HEIGHT=1080

# Proxy Configuration (Optional)
PROXY_ENABLED=true

# Multiple Proxy Support
PROXY_LIST=http://proxy1.example.com:8080,http://proxy2.example.com:8080,http://proxy3.example.com:8080
PROXY_ROTATION_ENABLED=true
PROXY_MAX_FAILURES=3
PROXY_TEST_INTERVAL=3600
```

### Proxy Setup

#### Method 1: Environment Variables (Recommended)

FairScrapper supports multiple proxy configuration formats for flexible deployment:

```env
# Enable/disable proxy usage
PROXY_ENABLED=true

# Format 1: Simple proxy URLs (no authentication)
PROXY_LIST=http://proxy1.example.com:8080,http://proxy2.example.com:8080

# Format 2: Proxy URLs with individual credentials
PROXY_LIST=http://proxy1.example.com:8080:user1:pass1,http://proxy2.example.com:8080:user2:pass2

# Format 3: Mixed (some with credentials, some without)
PROXY_LIST=http://proxy1.example.com:8080:user1:pass1,http://proxy2.example.com:8080,http://proxy3.example.com:8080:user3:pass3

# Proxy settings
PROXY_ROTATION_ENABLED=true
PROXY_MAX_FAILURES=3
PROXY_TEST_INTERVAL=3600
```

#### Method 2: JSON File (Deprecated)

**Note:** JSON file method is deprecated. FairScrapper now uses environment variables for better security and flexibility.

## API Documentation

### Base URL
```
http://localhost:8888
```

### Endpoints

#### POST /scrape

**Unified Scraping Endpoint**

**Request Body:**
```json
{
  "url": "https://example.com",
  "use_proxy": false,
  "wait_time": 2,
  "debug": false,
  "screenshot": false,
  "get": {
    "field_name": "css_selector"
  },
  "collect": {
    "collection_name": {
      "selector": "item_selector",
      "fields": {
        "field1": "sub_selector1",
        "field2": "sub_selector2(attribute)"
      }
    }
  }
}
```

**Response:**
```json
{
  "success": true,
  "url": "https://example.com",
  "data": {
    "get_results": {},
    "collect_results": {}
  },
  "load_time": 2.45,
  "timestamp": "2025-01-09 12:34:56",
  "screenshot_path": null,
  "links": []
}
```

#### GET /health

**Health Check Endpoint**

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-01-09 12:34:56"
}
```

## Advanced Selector Syntax

This API supports several advanced selector syntaxes beyond standard CSS selectors:

### 1. Attribute Extraction

Extract HTML attributes from elements:

**Syntax:** `selector(attribute)`

**Examples:**
```json
{
  "get": {
    "link_url": "a(href)",
    "image_src": "img(src)",
    "element_class": ".container(class)",
    "data_id": "[data-item](data-id)"
  }
}
```

### 2. Parent Navigation with `<` Syntax

Navigate up the DOM tree and then select child elements:

**Syntax:** `start_selector<parent1<parent2>target_selector`

**Examples:**
```json
{
  "get": {
    "parent_title": ".content<div<div>h1",
    "grandparent_link": ".button<section<article>a(href)"
  }
}
```

### 3. Ancestor Navigation

#### Direct Parent: `parent`
```json
{
  "get": {
    "parent_link": "parent a(href)"
  }
}
```

#### Grandparent: `>>`
```json
{
  "get": {
    "grandparent_title": ">> h1"
  }
}
```

#### Any Ancestor: `*`
```json
{
  "get": {
    "ancestor_link": "* a(href)"
  }
}
```

### 4. Collection with Advanced Selectors

Use advanced selectors in collection operations:

```json
{
  "collect": {
    "products": {
      "selector": ".product",
      "fields": {
        "name": "h2",
        "price": ".price",
        "link": "a(href)",
        "category": "parent .category",
        "brand": ">> .brand-name"
      }
    }
  }
}
```

## Examples

### Basic Text Extraction

```json
{
  "url": "https://example.com",
  "use_proxy": false,
  "wait_time": 2,
  "get": {
    "title": "h1",
    "description": "p.description"
  }
}
```

### Attribute Extraction

```json
{
  "url": "https://example.com",
  "use_proxy": false,
  "wait_time": 2,
  "get": {
    "main_link": "a.main-link(href)",
    "image_source": "img.hero(src)",
    "page_language": "html(lang)"
  }
}
```

### Parent Navigation

```json
{
  "url": "https://example.com",
  "use_proxy": false,
  "wait_time": 2,
  "get": {
    "section_title": ".content<div<section>h2",
    "parent_class": ".button<div(class)",
    "ancestor_link": "* a.main-nav(href)"
  }
}
```

### Collection Scraping

```json
{
  "url": "https://example.com",
  "use_proxy": false,
  "wait_time": 2,
  "collect": {
    "articles": {
      "selector": "article",
      "fields": {
        "title": "h2",
        "author": ".author",
        "date": ".date",
        "link": "a(href)",
        "category": "parent .category-tag"
      }
    }
  }
}
```

### Complex Example with All Features

```json
{
  "url": "https://news.ycombinator.com",
  "use_proxy": false,
  "wait_time": 3,
  "debug": true,
  "screenshot": true,
  "get": {
    "site_title": "title",
    "main_logo": ".hnname a(href)"
  },
  "collect": {
    "stories": {
      "selector": ".athing",
      "fields": {
        "title": ".titleline > a",
        "url": ".titleline > a(href)",
        "points": "parent .score",
        "comments": "parent .subtext a:last-child",
        "domain": ".sitestr"
      }
    }
  }
}
```

## Deployment

### Ubuntu Server Deployment

1. **System Dependencies:**
   ```bash
   sudo apt update
   sudo apt install python3 python3-pip python3-venv nodejs npm
   ```

2. **Install Playwright Dependencies:**
   ```bash
   sudo apt install libnss3 libnspr4 libatk-bridge2.0-0 libdrm2 libxkbcommon0 \
                    libgtk-3-0 libx11-xcb1 libxcomposite1 libxdamage1 libxrandr2 \
                    libasound2 libpangocairo-1.0-0 libatk1.0-0 libcairo-gobject2 \
                    libgtk-3-0 libgdk-pixbuf2.0-0
   ```

3. **Setup Application:**
   ```bash
   cd /opt
   sudo git clone <repository-url> scraper
   cd scraper
   sudo python3 -m venv venv
   sudo venv/bin/pip install -r requirements.txt
   sudo venv/bin/playwright install
   ```

4. **Create Systemd Service:**
   ```bash
   sudo nano /etc/systemd/system/scraper-api.service
   ```

   ```ini
   [Unit]
   Description=Web Scraper API
   After=network.target

   [Service]
   Type=simple
   User=www-data
   WorkingDirectory=/opt/scraper
   Environment=PATH=/opt/scraper/venv/bin
   ExecStart=/opt/scraper/venv/bin/python api.py
   Restart=always

   [Install]
   WantedBy=multi-user.target
   ```

5. **Start Service:**
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable scraper-api
   sudo systemctl start scraper-api
   ```

### Docker Deployment

```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
RUN playwright install --with-deps

COPY . .
EXPOSE 8888

CMD ["python", "api.py"]
```

### Environment Variables for Production

```env
API_HOST=0.0.0.0
API_PORT=8888
DEBUG=False
HEADLESS=True
TIMEOUT=30000
```

## Troubleshooting

If you encounter issues during installation or usage, check our comprehensive troubleshooting guide:

### **Common Issues:**
- **Ubuntu/Debian package errors** - Package name changes in newer versions
- **Playwright browser issues** - System dependencies missing
- **Python virtual environment problems** - Environment not activating
- **Permission issues** - Scripts not executable
- **Network issues** - Package download failures
- **API startup problems** - Port conflicts or module errors

### **Quick Fixes:**
```bash
# Fix package issues on Ubuntu/Debian
sudo apt-get install -y libasound2t64 libatk-bridge2.0-0t64 libgtk-3-0t64

# Reinstall Playwright
playwright install
playwright install-deps

# Fix permissions
chmod +x install.sh start.sh stop.sh

# Check API status
curl -X POST http://localhost:8888/health -H "X-API-Key: sk-demo-key-12345"
```

### **Detailed Guide:**
📖 **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)** - Complete troubleshooting guide with step-by-step solutions

### **Still Need Help?**
- **GitHub:** [volkandm](https://github.com/volkandm)
- **Email:** volkan@designmonkeys.net

## Author

**Volkan AYDIN**
- **Year:** 2025
- **Email:** volkan@designmonkeys.net
- **GitHub:** [volkandm](https://github.com/volkandm)

### Key Contributions
- Advanced CSS selector syntax implementation
- Parent navigation system with `<` syntax
- Attribute extraction capabilities
- Unified API design for both single and collection operations
- High-performance async architecture
- Ethical proxy rotation system
- Fair use rate limiting implementation

## License

This project is licensed under the **Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License (CC BY-NC-SA 4.0)**.

### What this means:

✅ **You CAN:**
- Use for personal projects
- Modify and adapt the code
- Share with others
- Create derivative works
- Use for educational purposes

❌ **You CANNOT:**
- Use for commercial purposes
- Sell this software or derivatives
- Use in commercial products/services

📋 **You MUST:**
- Give appropriate credit to the author
- Indicate if changes were made
- Share derivatives under the same license
- Include license notice

### Commercial Use

This software is **FREE for personal use only**. Commercial use is **prohibited** under this license.

For commercial licensing, please contact: **volkan@designmonkeys.net**

### Disclaimer

This software is provided "as is" without warranty of any kind. The author is not responsible for any damages or issues arising from its use.

## Commercial License

For commercial use of this software, you need a separate commercial license.

**Commercial licensing includes:**
- ✅ Permission for commercial use
- ✅ Priority support
- ✅ Custom feature development
- ✅ Integration assistance
- ✅ No attribution requirements

**Contact for commercial licensing:**
📧 **volkan@designmonkeys.net**

## Donations & Support

If you find this project useful, consider supporting its development:

### Bitcoin Donations
```
bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh
```

### Why Donate?
- 🚀 **Accelerate development** of new features
- 🐛 **Priority bug fixes** and improvements
- 📚 **Better documentation** and examples
- 🔧 **Enhanced tooling** and utilities
- 💡 **Support innovation** in web scraping technology

Your support helps maintain and improve this open-source project for everyone!

### Support Options
- **Personal users:** Donations appreciated but not required
- **Commercial users:** Commercial license required + donations welcome
- **Contributors:** Code contributions always welcome

## Contact

- **GitHub:** [volkandm](https://github.com/volkandm)
- **Email:** volkan@designmonkeys.net
- **Commercial Inquiries:** volkan@designmonkeys.net

---

**Made with ❤️ by Volkan AYDIN**

*Supporting ethical and fair web scraping technology since 2025*