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
  "click": ["button.accept", ".modal a.next"],
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

## 🖼️ Image Scraping Features

The API supports advanced image extraction with base64 encoding:

### **Image Extraction Methods**

1. **Direct Image Element Extraction:**
   ```json
   {
     "get": {
       "product_image": "img.product-image"
     }
   }
   ```

2. **Image with src Attribute:**
   ```json
   {
     "get": {
       "product_image": "img(src)"
     }
   }
   ```

3. **Image Collection:**
   ```json
   {
     "collect": {
       "gallery": {
         "selector": ".gallery img",
         "fields": {
           "image": "img"
         }
       }
     }
   }
   ```

### **Image Response Format**

Images are returned as base64 encoded data URLs:
```json
{
  "success": true,
  "data": {
    "get": {
      "product_image": "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQEAYABgAAD..."
    },
    "collect": {
      "gallery": [
        {
          "image": "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQEAYABgAAD..."
        }
      ]
    }
  }
}
```

### **Image Features**
- ✅ **Base64 encoding** - Ready for direct use
- ✅ **Size limits** - 5MB maximum (configurable)
- ✅ **Multiple formats** - JPEG, PNG, WebP, etc.
- ✅ **Browser extraction** - Direct from loaded images
- ✅ **URL fallback** - Downloads if browser extraction fails
- ✅ **Relative URL handling** - Converts to absolute URLs

## 🖱️ Click Operations

The API supports sequential click operations before scraping. This is useful for interacting with pages that require user actions (e.g., accepting cookies, opening modals, navigating through wizard steps).

### **Click Feature**

Click operations are executed **after** the page loads but **before** scraping begins. Each click operation:
- Waits for the element to be visible
- Clicks the element
- Waits at least 100ms
- Waits for navigation or DOM updates to complete
- Proceeds to the next click only after the previous one completes

### **Basic Click Usage**

```json
{
  "url": "https://example.com",
  "use_proxy": true,
  "wait_time": 3,
  "click": ["button.accept-cookies", ".modal a.next"],
  "get": {
    "content": ".main-content"
  }
}
```

### **Click with Navigation**

```json
{
  "url": "https://example.com/products",
  "use_proxy": true,
  "wait_time": 3,
  "click": ["a.category-link", "button.filter"],
  "collect": {
    "products": {
      "selector": ".product",
      "fields": {
        "name": "h3",
        "price": ".price"
      }
    }
  }
}
```

### **Click Workflow**

1. **Page loads** - Initial URL is navigated
2. **DOM ready** - Waits for page to be ready
3. **Click operations** - Executes clicks in sequence:
   - `click[0]` → wait for completion
   - `click[1]` → wait for completion
   - `click[2]` → wait for completion
4. **Scraping** - Extracts data from the final state

### **Click Timing**

- **Minimum wait**: 100ms after each click
- **Navigation detection**: Automatically detects if click causes navigation
- **Network idle**: Waits for network activity to complete after navigation
- **DOM stabilization**: Waits for DOM updates before next click

### **Example: Multi-Step Form**

```json
{
  "url": "https://example.com/form",
  "use_proxy": true,
  "wait_time": 3,
  "click": [
    "button.start-form",
    "#step1 button.next",
    "#step2 button.next",
    "#step3 button.submit"
  ],
  "get": {
    "result": ".success-message"
  }
}
```

### **Example: Cookie Acceptance + Modal**

```json
{
  "url": "https://example.com",
  "use_proxy": true,
  "wait_time": 3,
  "click": [
    "button#accept-cookies",
    ".modal button.close",
    "a.explore-button"
  ],
  "collect": {
    "items": {
      "selector": ".item",
      "fields": {
        "title": "h2",
        "description": "p"
      }
    }
  }
}
```

### **Error Handling**

If a click selector cannot be found:
- A warning is logged
- The click is skipped
- Execution continues with the next click
- Scraping proceeds with the current page state

## 🔧 Advanced Selector Syntax

### **Query Builder Navigation**

The API supports advanced CSS selector navigation with special operators:

#### **Parent Navigation (`<`)**
Navigate to parent elements:
```json
{
  "get": {
    "parent_title": "a.test<.product_pod>h1"
  }
}
```
- Finds `a.test` element
- Goes to parent `.product_pod`
- Finds child `h1` within that parent

#### **Child Navigation (`>`)**
Navigate to child elements:
```json
{
  "get": {
    "child_text": ".container>div.content>p"
  }
}
```
- Starts with `.container`
- Goes to child `div.content`
- Finds child `p` within that

#### **Sibling Navigation (`+`)**
Navigate to sibling elements:
```json
{
  "get": {
    "next_element": ".current+.next"
  }
}
```
- Finds `.current` element
- Goes to next sibling
- Finds `.next` within that sibling

#### **Complex Navigation Chains**
```json
{
  "get": {
    "complex_selector": "a.test<.product_pod<section>div.alert>strong"
  }
}
```

### **Attribute Extraction**

Extract specific attributes from elements:

#### **Basic Attribute Extraction**
```json
{
  "get": {
    "link_url": "a(href)",
    "image_src": "img(src)",
    "data_value": ".element(data-value)"
  }
}
```

#### **Wildcard Navigation**
Find attributes in any ancestor:
```json
{
  "collect": {
    "products": {
      "selector": ".product-item",
      "fields": {
        "link": "* a(href)",
        "image": "* img(src)"
      }
    }
  }
}
```

#### **Parent Navigation with Attributes**
```json
{
  "collect": {
    "items": {
      "selector": ".item",
      "fields": {
        "parent_link": ".child<div<div>a(href)"
      }
    }
  }
}
```

### **Text and HTML Extraction**

#### **Text Only (Default)**
```json
{
  "get": {
    "title": "h1",
    "description": ".description"
  }
}
```

#### **HTML Content**
```json
{
  "get": {
    "content_html": {
      "selector": ".content",
      "attr": null
    }
  }
}
```

#### **Both Text and HTML**
```json
{
  "get": {
    "content": {
      "selector": ".content",
      "include_html": true
    }
  }
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

# Image scraping example
curl -X POST "http://localhost:8888/scrape" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: sk-1234567890abcdef" \
  -d '{
    "url": "https://example-store.com/product",
    "use_proxy": true,
    "wait_time": 3,
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

# Query builder navigation example
curl -X POST "http://localhost:8888/scrape" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: sk-1234567890abcdef" \
  -d '{
    "url": "https://example.com/products",
    "use_proxy": true,
    "wait_time": 3,
    "get": {
      "parent_title": "a.product-link<.product-card>h2",
      "sibling_price": ".current+.price"
    },
    "collect": {
      "products": {
        "selector": ".product-item",
        "fields": {
          "name": "h3",
          "price": ".price",
          "link": "a(href)",
          "image": "img(src)",
          "parent_category": ".item<.category>h4"
        }
      }
    }
  }'

# Click operations example
curl -X POST "http://localhost:8888/scrape" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: sk-1234567890abcdef" \
  -d '{
    "url": "https://example.com",
    "use_proxy": true,
    "wait_time": 3,
    "click": ["button.accept-cookies", ".modal button.close"],
    "get": {
      "title": "h1",
      "content": ".main-content"
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

# Image scraping example
data = {
    "url": "https://example-store.com/product",
    "use_proxy": True,
    "wait_time": 3,
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
}

response = requests.post(
    "http://localhost:8888/scrape",
    json=data,
    headers=headers
)
result = response.json()

if result["success"]:
    # Save base64 image to file
    import base64
    
    product_image = result['data']['get']['product_image']
    if product_image.startswith('data:image'):
        # Extract base64 data
        header, data = product_image.split(',', 1)
        image_data = base64.b64decode(data)
        
        with open('product_image.jpg', 'wb') as f:
            f.write(image_data)
        print("✅ Product image saved as product_image.jpg")
    
    print(f"Gallery images: {len(result['data']['collect']['gallery'])}")

# Query builder navigation example
data = {
    "url": "https://example.com/products",
    "use_proxy": True,
    "wait_time": 3,
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
}

response = requests.post(
    "http://localhost:8888/scrape",
    json=data,
    headers=headers
)
result = response.json()

if result["success"]:
    print(f"Parent title: {result['data']['get']['parent_title']}")
    print(f"Sibling price: {result['data']['get']['sibling_price']}")
    print(f"Products found: {len(result['data']['collect']['products'])}")
    
    # Process images from collection
    for i, product in enumerate(result['data']['collect']['products']):
        if product.get('image') and product['image'].startswith('data:image'):
            # Save each product image
            header, data = product['image'].split(',', 1)
            image_data = base64.b64decode(data)
            
            with open(f'product_{i}.jpg', 'wb') as f:
                f.write(image_data)
            print(f"✅ Product {i} image saved")
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

// Image scraping example
fetch('http://localhost:8888/scrape', {
    method: 'POST',
    headers: headers,
    body: JSON.stringify({
        url: 'https://example-store.com/product',
        use_proxy: true,
        wait_time: 3,
        get: {
            product_image: 'img.product-image',
            gallery_image: 'img(src)'
        },
        collect: {
            gallery: {
                selector: '.gallery img',
                fields: {
                    image: 'img'
                }
            }
        }
    })
})
.then(response => response.json())
.then(data => {
    if (data.success) {
        // Display image directly in browser
        const productImage = data.data.get.product_image;
        if (productImage.startsWith('data:image')) {
            const img = document.createElement('img');
            img.src = productImage;
            img.style.maxWidth = '300px';
            document.body.appendChild(img);
        }
        
        console.log('Gallery images:', data.data.collect.gallery.length);
    }
});

// Query builder navigation example
fetch('http://localhost:8888/scrape', {
    method: 'POST',
    headers: headers,
    body: JSON.stringify({
        url: 'https://example.com/products',
        use_proxy: true,
        wait_time: 3,
        get: {
            parent_title: 'a.product-link<.product-card>h2',
            sibling_price: '.current+.price',
            link_url: 'a(href)',
            image_src: 'img(src)'
        },
        collect: {
            products: {
                selector: '.product-item',
                fields: {
                    name: 'h3',
                    price: '.price',
                    link: 'a(href)',
                    image: 'img(src)',
                    parent_category: '.item<.category>h4',
                    wildcard_link: '* a(href)'
                }
            }
        }
    })
})
.then(response => response.json())
.then(data => {
    if (data.success) {
        console.log('Parent title:', data.data.get.parent_title);
        console.log('Sibling price:', data.data.get.sibling_price);
        console.log('Products found:', data.data.collect.products.length);
        
        // Process images
        data.data.collect.products.forEach((product, index) => {
            if (product.image && product.image.startsWith('data:image')) {
                console.log(`Product ${index} image available`);
                // You can display or save the image here
            }
        });
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
| `click` | array | null | Array of CSS selectors to click in sequence before scraping |
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

### 1. **E-commerce Site Scraping with Images**

```python
data = {
    "url": "https://example-store.com/products",
    "use_proxy": True,
    "wait_time": 5,
    "extract_links": True,
    "take_screenshot": True,
    "collect": {
        "products": {
            "selector": ".product-item",
            "fields": {
                "name": "h3",
                "price": ".price",
                "image": "img(src)",  # Returns base64 data
                "link": "a(href)",
                "category": ".item<.category>h4",  # Parent navigation
                "rating": ".rating+.stars"  # Sibling navigation
            }
        }
    }
}
```

### 2. **News Site Scraping with Images**

```python
data = {
    "url": "https://news-site.com",
    "use_proxy": True,
    "wait_time": 3,
    "get": {
        "headline": "h1",
        "summary": ".summary",
        "featured_image": "img.featured(src)"  # Base64 image
    },
    "collect": {
        "articles": {
            "selector": ".article",
            "fields": {
                "title": "h2",
                "link": "a(href)",
                "date": ".date",
                "thumbnail": "img(src)",  # Base64 image
                "author": ".author<.meta>span"  # Parent navigation
            }
        }
    }
}
```

### 3. **Social Media Scraping with Profile Images**

```python
data = {
    "url": "https://social-media.com/profile",
    "use_proxy": True,
    "wait_time": 10,
    "take_screenshot": True,
    "get": {
        "username": ".username",
        "followers": ".followers-count",
        "profile_image": "img.avatar(src)"  # Base64 image
    },
    "collect": {
        "posts": {
            "selector": ".post",
            "fields": {
                "content": ".content",
                "image": "img(src)",  # Base64 image
                "likes": ".likes+.count"  # Sibling navigation
            }
        }
    }
}
```

### 4. **Image Gallery Scraping**

```python
data = {
    "url": "https://gallery-site.com/album",
    "use_proxy": True,
    "wait_time": 5,
    "collect": {
        "images": {
            "selector": ".gallery img",
            "fields": {
                "image": "img",  # Direct base64 extraction
                "caption": ".caption",
                "download_link": "a(href)"
            }
        }
    }
}
```

### 5. **Complex Navigation Scraping**

```python
data = {
    "url": "https://complex-site.com/products",
    "use_proxy": True,
    "wait_time": 5,
    "get": {
        "page_title": "h1",
        "parent_category": "a.product<.category>h2",  # Parent navigation
        "sibling_info": ".current+.info",  # Sibling navigation
        "wildcard_link": "* a(href)"  # Wildcard navigation
    },
    "collect": {
        "products": {
            "selector": ".product-item",
            "fields": {
                "name": "h3",
                "price": ".price",
                "image": "img(src)",  # Base64 image
                "link": "a(href)",
                "parent_brand": ".item<.brand>span",  # Parent navigation
                "next_availability": ".stock+.availability",  # Sibling navigation
                "any_category": "* .category"  # Wildcard navigation
            }
        }
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
- ✅ **Image scraping** - Base64 encoded image extraction
- ✅ **Advanced selectors** - Query builder with parent/child/sibling navigation
- ✅ **Attribute extraction** - Support for any HTML attribute
- ✅ **Wildcard navigation** - Find elements in any ancestor
- ✅ **Complex selectors** - Chain multiple navigation operations
- ✅ **Size limits** - Configurable image size limits (5MB default)
- ✅ **Multiple formats** - Support for all image formats (JPEG, PNG, WebP, etc.)
- ✅ **Click operations** - Sequential click operations before scraping
- ✅ **Navigation detection** - Automatic detection of page navigation after clicks
- ✅ **DOM stabilization** - Waits for page updates after each click

### **Key Features Summary**

#### **Image Scraping**
- Direct base64 extraction from browser
- URL-based download fallback
- Size limit protection (5MB default)
- Support for all image formats
- Relative URL handling

#### **Query Builder Navigation**
- **Parent Navigation (`<`)**: `a.test<.product_pod>h1`
- **Child Navigation (`>`)**: `.container>div.content>p`
- **Sibling Navigation (`+`)**: `.current+.next`
- **Wildcard Navigation (`*`)**: `* a(href)`
- **Complex Chains**: `a.test<.product_pod<section>div.alert>strong`

#### **Attribute Extraction**
- **Basic**: `a(href)`, `img(src)`, `.element(data-value)`
- **With Navigation**: `.child<div<div>a(href)`
- **Wildcard**: `* a(href)`

**API URL**: `http://localhost:8888` (or your domain)
**Documentation**: `http://localhost:8888/docs` (or your domain)
**Authentication**: X-API-Key header required