# 🌐 Web Scraper API Usage Guide

This guide explains how to perform web scraping using the REST API.

## 🔐 Authentication

The API requires authentication using the `X-API-Key` header.

### Valid API Keys:
- `sk-1234567890abcdef`
- `sk-abcdef1234567890`
- `sk-test-api-key-2024`
- `sk-prod-api-key-2024`

## 🚀 Starting the API

```bash
# Start the API
python api.py

# Or with uvicorn
uvicorn api:app --host 0.0.0.0 --port 8888
```

After starting the API, you can access it at:
- **API**: `http://localhost:8888` (or your domain)
- **Documentation**: `http://localhost:8888/docs` (or your domain)
- **Health Check**: `http://localhost:8888/health` (POST only)

## 📋 Endpoints (POST Only)

### 1. **POST /scrape** - Advanced Scraping

**Headers:**
```
X-API-Key: sk-1234567890abcdef
Content-Type: application/json
```

**Request Body:**
```json
{
  "url": "https://example.com",
  "use_proxy": true,
  "proxy_url": null,
  "wait_time": 3,
  "wait_for_element": false,
  "element_timeout": 30,
  "debug": false,
  "take_screenshot": false,
  "extract_links": false,
  "get": {
    "title": "h1",
    "description": "meta[name='description']",
    "price": ".price"
  },
  "collect": {
    "products": {
      "selector": ".product",
      "fields": {
        "name": "h3",
        "price": ".price",
        "link": "a(href)"
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
    "get": {
      "title": "Page Title",
      "description": "Page description",
      "price": "$99.99"
    },
    "collect": {
      "products": [
        {
          "name": "Product 1",
          "price": "$29.99",
          "link": "/product1"
        },
        {
          "name": "Product 2", 
          "price": "$39.99",
          "link": "/product2"
        }
      ]
    }
  },
  "load_time": 5.23,
  "timestamp": "2025-01-11 02:45:00",
  "screenshot_path": null,
  "links": null,
  "proxy_used": {
    "url": "http://198.23.239.134:6540",
    "type": "HTTP",
    "index": 3,
    "total": 10
  }
}
```

### 2. **POST /scrape** - Simple HTML Source

If no `get` or `collect` fields are provided, returns the complete HTML source code:

**Request Body:**
```json
{
  "url": "https://example.com",
  "use_proxy": true,
  "wait_time": 3,
  "take_screenshot": false,
  "extract_links": false
}
```

**Response:**
```json
{
  "success": true,
  "url": "https://example.com",
  "html_source": "<!DOCTYPE html><html>...</html>",
  "content_length": 12345,
  "load_time": 2.5,
  "timestamp": "2025-01-11 02:45:00",
  "screenshot_path": null,
  "links": null,
  "proxy_used": {
    "url": "http://198.23.239.134:6540",
    "type": "HTTP",
    "index": 3,
    "total": 10
  }
}
```

### 3. **POST /health** - Health Check

**Headers:**
```
X-API-Key: sk-1234567890abcdef
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-01-11 02:45:00",
  "scraper_pool_size": 0,
  "api_key": "sk-1234567..."
}
```

### 4. **POST /proxies** - Available Proxies

**Headers:**
```
X-API-Key: sk-1234567890abcdef
```

**Response:**
```json
{
  "proxies": [
    "http://198.23.239.134:6540",
    "http://45.38.107.97:6014",
    "http://107.172.163.27:6543"
  ],
  "default": "http://198.23.239.134:6540"
}
```

### 5. **POST /test-proxy** - Proxy Test

**Headers:**
```
X-API-Key: sk-1234567890abcdef
```

**Query Parameters:**
- `proxy_url`: Proxy URL to test

**Example:**
```bash
curl -X POST "http://localhost:8888/test-proxy?proxy_url=http://198.23.239.134:6540" \
  -H "X-API-Key: sk-1234567890abcdef"
```

**Response:**
```json
{
  "proxy": "http://198.23.239.134:6540",
  "working": true,
  "ip": "198.23.239.134"
}
```

## 💡 Usage Examples

### 1. **Simple Scraping (cURL)**

```bash
# Simple HTML source scraping
curl -X POST "http://localhost:8888/scrape" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: sk-1234567890abcdef" \
  -d '{
    "url": "https://httpbin.org/html",
    "use_proxy": true,
    "wait_time": 3
  }'

# Advanced scraping with element extraction
curl -X POST "http://localhost:8888/scrape" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: sk-1234567890abcdef" \
  -d '{
    "url": "https://quotes.toscrape.com/",
    "use_proxy": true,
    "wait_time": 3,
    "take_screenshot": true,
    "extract_links": true,
    "get": {
      "title": "h1",
      "quote": ".quote .text"
    }
  }'
```

### 2. **Python Usage**

```python
import requests
import json

# Headers
headers = {
    "X-API-Key": "sk-1234567890abcdef",
    "Content-Type": "application/json"
}

# Simple HTML source scraping
data = {
    "url": "https://example.com",
    "use_proxy": True,
    "wait_time": 3
}

response = requests.post(
    "http://localhost:8888/scrape",
    json=data,
    headers=headers
)
result = response.json()

if result["success"]:
    print(f"HTML length: {result['content_length']}")
    print(f"Proxy used: {result['proxy_used']['url']}")
    print(f"Load time: {result['load_time']}s")

# Advanced scraping with element extraction
data = {
    "url": "https://quotes.toscrape.com/",
    "use_proxy": True,
    "wait_time": 3,
    "take_screenshot": True,
    "extract_links": True,
    "get": {
        "title": "h1",
        "first_quote": ".quote .text"
    },
    "collect": {
        "quotes": {
            "selector": ".quote",
            "fields": {
                "text": ".text",
                "author": ".author",
                "tags": ".tags .tag"
            }
        }
    }
}

response = requests.post(
    "http://localhost:8888/scrape",
    json=data,
    headers=headers
)
result = response.json()

if result["success"]:
    print(f"Title: {result['data']['get']['title']}")
    print(f"Quotes found: {len(result['data']['collect']['quotes'])}")
    print(f"Proxy used: {result['proxy_used']['url']}")
```

### 3. **JavaScript Usage**

```javascript
// Headers
const headers = {
    'X-API-Key': 'sk-1234567890abcdef',
    'Content-Type': 'application/json'
};

// Simple HTML source scraping
fetch('http://localhost:8888/scrape', {
    method: 'POST',
    headers: headers,
    body: JSON.stringify({
        url: 'https://example.com',
        use_proxy: true,
        wait_time: 3
    })
})
.then(response => response.json())
.then(data => {
    if (data.success) {
        console.log('HTML length:', data.content_length);
        console.log('Proxy used:', data.proxy_used.url);
    }
});

// Advanced scraping with element extraction
fetch('http://localhost:8888/scrape', {
    method: 'POST',
    headers: headers,
    body: JSON.stringify({
        url: 'https://quotes.toscrape.com/',
        use_proxy: true,
        wait_time: 3,
        get: {
            title: 'h1',
            first_quote: '.quote .text'
        },
        collect: {
            quotes: {
                selector: '.quote',
                fields: {
                    text: '.text',
                    author: '.author'
                }
            }
        }
    })
})
.then(response => response.json())
.then(data => {
    if (data.success) {
        console.log('Title:', data.data.get.title);
        console.log('Quotes:', data.data.collect.quotes);
    }
});
```

## 🔧 Parameters

### UnifiedScrapeRequest Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `url` | string | - | URL to scrape (required) |
| `use_proxy` | boolean | true | Use proxy |
| `proxy_url` | string | null | Custom proxy URL |
| `wait_time` | integer | 3 | Wait time after page load (seconds) |
| `wait_for_element` | boolean | false | Wait for specific element |
| `element_timeout` | integer | 30 | Timeout for element waiting (seconds) |
| `debug` | boolean | false | Include debug HTML in response |
| `take_screenshot` | boolean | false | Take screenshot |
| `extract_links` | boolean | false | Extract all links from page |
| `get` | object | null | Single element extractions |
| `collect` | object | null | Collection extractions |

### Supported Proxy Types

- **HTTP**: `http://proxy.com:8080`
- **HTTPS**: `https://proxy.com:8080`
- **SOCKS4**: `socks4://proxy.com:1080`
- **SOCKS5**: `socks5://proxy.com:1080`
- **With credentials**: `socks5://proxy.com:1080:username:password`

## 🛡️ Security

### Authentication
- All endpoints require API key
- `X-API-Key` header is mandatory
- Invalid API keys return 401 error

### Method Restrictions
- Only POST methods are accepted
- GET methods return 405 (Method Not Allowed)

### Error Handling
```python
try:
    response = requests.post("http://localhost:8888/scrape", json=data, headers=headers)
    result = response.json()
    
    if result["success"]:
        print("✅ Scraping successful")
    else:
        print(f"❌ Error: {result['error']}")
        
except requests.exceptions.RequestException as e:
    print(f"❌ Network error: {e}")
```

## 📊 Performance

### Recommended Usage

1. **For small sites:**
   ```json
   {
     "wait_time": 1,
     "use_proxy": true
   }
   ```

2. **For large sites:**
   ```json
   {
     "wait_time": 5,
     "use_proxy": true,
     "take_screenshot": true,
     "extract_links": true
   }
   ```

3. **With proxy rotation:**
   ```json
   {
     "use_proxy": true,
     "wait_time": 3
   }
   ```

## 🚨 Error Codes

| Code | Description |
|------|-------------|
| 200 | Success |
| 401 | API key missing |
| 403 | Invalid API key |
| 405 | Method not allowed (when GET is used) |
| 500 | Server error |

## 📝 Example Scenarios

### 1. **E-commerce Site Scraping**

```python
data = {
    "url": "https://example-store.com/products",
    "use_proxy": True,
    "wait_time": 5,
    "extract_links": True,
    "collect": {
        "products": {
            "selector": ".product-item",
            "fields": {
                "name": "h3",
                "price": ".price",
                "image": "img(src)",
                "link": "a(href)"
            }
        }
    }
}
```

### 2. **News Site Scraping**

```python
data = {
    "url": "https://news-site.com",
    "use_proxy": True,
    "wait_time": 3,
    "get": {
        "headline": "h1",
        "summary": ".summary"
    },
    "collect": {
        "articles": {
            "selector": ".article",
            "fields": {
                "title": "h2",
                "link": "a(href)",
                "date": ".date"
            }
        }
    }
}
```

### 3. **Social Media Scraping**

```python
data = {
    "url": "https://social-media.com/profile",
    "use_proxy": True,
    "wait_time": 10,
    "take_screenshot": True,
    "get": {
        "username": ".username",
        "followers": ".followers-count"
    }
}
```

## 🎯 Conclusion

This API provides:
- ✅ **Secure usage** - API key authentication
- ✅ **POST only** - Only POST methods
- ✅ **Proxy support** - IP hiding with random rotation
- ✅ **Flexible parameters** - Customizable settings
- ✅ **Fast results** - Asynchronous operations
- ✅ **Detailed output** - HTML, elements, links, screenshots
- ✅ **Proxy information** - Shows which proxy was used

**API URL**: `http://localhost:8888` (or your domain)
**Documentation**: `http://localhost:8888/docs` (or your domain)
**Authentication**: X-API-Key header required