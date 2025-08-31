# 🌐 Web Scraper API Kullanım Kılavuzu

Bu kılavuz, REST API ile web scraping yapmayı açıklar.

## 🔐 Authentication

API, `X-API-Key` header'ı ile authentication gerektirir.

### Geçerli API Key'ler:
- `sk-1234567890abcdef`
- `sk-abcdef1234567890`
- `sk-test-api-key-2024`
- `sk-prod-api-key-2024`

## 🚀 API Başlatma

```bash
# API'yi başlat
python api.py

# Veya uvicorn ile
uvicorn api:app --host 0.0.0.0 --port 8888
```

API başladıktan sonra şu adreslerde erişebilirsiniz:
- **API**: `http://localhost:8888` (or your domain)
- **Dokümantasyon**: `http://localhost:8888/docs` (or your domain)
- **Health Check**: `http://localhost:8888/health` (POST only)

## 📋 Endpoint'ler (Sadece POST)

### 1. **POST /scrape** - Gelişmiş Scraping

**Headers:**
```
X-API-Key: sk-1234567890abcdef
Content-Type: application/json
```

**Request Body:**
```json
{
  "url": "https://example.com",
  "use_proxy": false,
  "proxy_url": null,
  "wait_time": 3,
  "take_screenshot": false,
  "extract_text": true,
  "extract_links": false,
  "extract_images": false
}
```

**Response:**
```json
{
  "success": true,
  "url": "https://example.com",
  "status_code": 200,
  "content_length": 12345,
  "html_content": "<!DOCTYPE html>...",
  "text_content": "Sayfa metni...",
  "links": [
    {
      "text": "Link metni",
      "href": "https://example.com/link",
      "title": "Link başlığı"
    }
  ],
  "images": [
    {
      "src": "https://example.com/image.jpg",
      "alt": "Resim açıklaması",
      "width": 300,
      "height": 200
    }
  ],
  "screenshot_path": "screenshot_abc123_1234567890.png",
  "proxy_used": "http://57.129.81.201:8080",
  "ip_address": "176.234.132.87",
  "load_time": 5.23,
  "timestamp": "2025-08-03 20:40:04"
}
```

### 2. **POST /scrape/simple** - Basit Scraping

**Headers:**
```
X-API-Key: sk-1234567890abcdef
```

**Query Parameters:**
- `url`: Scrape edilecek URL
- `use_proxy`: Proxy kullanımı (default: false)

**Example:**
```bash
curl -X POST "http://localhost:8888/scrape/simple?url=https://example.com&use_proxy=false" \
  -H "X-API-Key: sk-1234567890abcdef"
```

### 3. **POST /scrape/selector** - CSS Selector Tabanlı Scraping

**Headers:**
```
X-API-Key: sk-1234567890abcdef
Content-Type: application/json
```

**Request Body:**
```json
{
  "url": "https://example.com",
  "selector": "h1.title",
  "collection": false,
  "attr": null,
  "fields": null,
  "use_proxy": false,
  "proxy_url": null,
  "wait_time": 3
}
```

**Kullanım Senaryoları:**

#### A. Tekil Element
```json
{
  "url": "https://example.com",
  "selector": "h1.title"
}
```

**Response:**
```json
{
  "success": true,
  "url": "https://example.com",
  "data": "Sayfa Başlığı",
  "load_time": 2.45,
  "timestamp": "2025-08-04 02:23:40"
}
```

#### B. Tekil Element + Attribute
```json
{
  "url": "https://example.com",
  "selector": "a.logo",
  "attr": "href"
}
```

**Response:**
```json
{
  "success": true,
  "url": "https://example.com",
  "data": "https://example.com/logo.png",
  "load_time": 2.45,
  "timestamp": "2025-08-04 02:23:40"
}
```

#### C. Collection (Tekrar Eden)
```json
{
  "url": "https://example.com",
  "selector": "ul>li",
  "collection": true
}
```

**Response:**
```json
{
  "success": true,
  "url": "https://example.com",
  "data": ["Öğe 1", "Öğe 2", "Öğe 3"],
  "load_time": 2.45,
  "timestamp": "2025-08-04 02:23:40"
}
```

#### D. Collection + Çoklu Alan
```json
{
  "url": "https://example.com",
  "selector": "div.product-item",
  "collection": true,
  "fields": {
    "title": "h3.title",
    "price": "span.price",
    "link": {
      "selector": "a",
      "attr": "href"
    },
    "image": {
      "selector": "img",
      "attr": "src"
    }
  }
}
```

**Response:**
```json
{
  "success": true,
  "url": "https://example.com",
  "data": [
    {
      "title": "Ürün 1",
      "price": "100 TL",
      "link": "/urun1",
      "image": "/resim1.jpg"
    },
    {
      "title": "Ürün 2",
      "price": "200 TL", 
      "link": "/urun2",
      "image": "/resim2.jpg"
    }
  ],
  "load_time": 2.45,
  "timestamp": "2025-08-04 02:23:40"
}
```

**Response:**
```json
{
  "success": true,
  "url": "https://example.com",
  "html": "<!DOCTYPE html>...",
  "length": 12345,
  "load_time": 5.23
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
  "timestamp": "2025-08-03 20:40:04",
  "scraper_pool_size": 1,
  "api_key": "sk-1234567..."
}
```

### 4. **POST /proxies** - Mevcut Proxy'ler

**Headers:**
```
X-API-Key: sk-1234567890abcdef
```

**Response:**
```json
{
  "proxies": [
    {
      "url": "http://57.129.81.201:8080",
      "country": "DE",
      "type": "HTTP",
      "status": "working"
    },
    {
      "url": "http://158.69.185.37:3129",
      "country": "CA",
      "type": "HTTP", 
      "status": "working"
    }
  ]
}
```

### 5. **POST /test-proxy** - Proxy Test

**Headers:**
```
X-API-Key: sk-1234567890abcdef
```

**Query Parameters:**
- `proxy_url`: Test edilecek proxy URL

**Example:**
```bash
curl -X POST "http://localhost:8888/test-proxy?proxy_url=http://57.129.81.201:8080" \
  -H "X-API-Key: sk-1234567890abcdef"
```

**Response:**
```json
{
  "proxy": "http://57.129.81.201:8080",
  "working": true,
  "ip": "176.234.132.87",
  "load_time": 3.45
}
```

## 💡 Kullanım Örnekleri

### 1. **Basit Scraping (cURL)**

```bash
# Basit scraping
curl -X POST "http://localhost:8888/scrape/simple?url=https://httpbin.org/html" \
  -H "X-API-Key: sk-1234567890abcdef"

# Proxy ile scraping
curl -X POST "http://localhost:8888/scrape/simple?url=https://httpbin.org/ip&use_proxy=true" \
  -H "X-API-Key: sk-1234567890abcdef"
```

### 2. **Gelişmiş Scraping (cURL)**

```bash
curl -X POST "http://localhost:8888/scrape" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: sk-1234567890abcdef" \
  -d '{
    "url": "https://quotes.toscrape.com/",
    "use_proxy": false,
    "wait_time": 2,
    "take_screenshot": true,
    "extract_text": true,
    "extract_links": true,
    "extract_images": false
  }'
```

### 3. **Python ile Kullanım**

```python
import requests
import json

# Headers
headers = {
    "X-API-Key": "sk-1234567890abcdef",
    "Content-Type": "application/json"
}

# Basit scraping
response = requests.post(
    "http://localhost:8888/scrape/simple",
    params={"url": "https://example.com", "use_proxy": False},
    headers=headers
)
result = response.json()
print(f"HTML: {result['html'][:200]}...")

# Gelişmiş scraping
data = {
    "url": "https://quotes.toscrape.com/",
    "use_proxy": True,
    "wait_time": 3,
    "take_screenshot": True,
    "extract_links": True
}

response = requests.post(
    "http://localhost:8888/scrape",
    json=data,
    headers=headers
)
result = response.json()

if result["success"]:
    print(f"Content length: {result['content_length']}")
    print(f"Links found: {len(result['links'])}")
    print(f"Proxy used: {result['proxy_used']}")
```

### 4. **JavaScript ile Kullanım**

```javascript
// Headers
const headers = {
    'X-API-Key': 'sk-1234567890abcdef',
    'Content-Type': 'application/json'
};

// Basit scraping
fetch('http://localhost:8888/scrape/simple?url=https://example.com', {
    method: 'POST',
    headers: headers
})
.then(response => response.json())
.then(data => {
    console.log('HTML:', data.html.substring(0, 200));
});

// Gelişmiş scraping
fetch('http://localhost:8888/scrape', {
    method: 'POST',
    headers: headers,
    body: JSON.stringify({
        url: 'https://quotes.toscrape.com/',
        use_proxy: true,
        extract_links: true
    })
})
.then(response => response.json())
.then(data => {
    console.log('Links:', data.links);
});
```

## 🔧 Parametreler

### ScrapeRequest Parametreleri

| Parametre | Tip | Varsayılan | Açıklama |
|-----------|-----|------------|----------|
| `url` | string | - | Scrape edilecek URL (zorunlu) |
| `use_proxy` | boolean | false | Proxy kullanımı |
| `proxy_url` | string | null | Özel proxy URL |
| `wait_time` | integer | 3 | Sayfa yükleme sonrası bekleme süresi (saniye) |
| `take_screenshot` | boolean | false | Screenshot alma |
| `extract_text` | boolean | true | Metin içeriği çıkarma |
| `extract_links` | boolean | false | Link'leri çıkarma |
| `extract_images` | boolean | false | Resim'leri çıkarma |

## 🛡️ Güvenlik

### Authentication
- Tüm endpoint'ler API key gerektirir
- `X-API-Key` header'ı zorunlu
- Geçersiz API key'ler 403 hatası döner

### Method Restrictions
- Sadece POST methodları kabul edilir
- GET methodları 405 (Method Not Allowed) döner

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

## 📊 Performans

### Önerilen Kullanım

1. **Küçük siteler için:**
   ```json
   {
     "wait_time": 1,
     "extract_text": true,
     "extract_links": false
   }
   ```

2. **Büyük siteler için:**
   ```json
   {
     "wait_time": 5,
     "extract_text": true,
     "extract_links": true,
     "take_screenshot": true
   }
   ```

3. **Proxy ile:**
   ```json
   {
     "use_proxy": true,
     "wait_time": 3
   }
   ```

## 🚨 Hata Kodları

| Kod | Açıklama |
|-----|----------|
| 200 | Başarılı |
| 401 | API key eksik |
| 403 | Geçersiz API key |
| 405 | Method not allowed (GET kullanıldığında) |
| 500 | Sunucu hatası |

## 📝 Örnek Senaryolar

### 1. **E-ticaret Sitesi Scraping**

```python
data = {
    "url": "https://example-store.com/products",
    "use_proxy": True,
    "wait_time": 5,
    "extract_links": True,
    "extract_images": True
}
```

### 2. **Haber Sitesi Scraping**

```python
data = {
    "url": "https://news-site.com",
    "use_proxy": False,
    "extract_text": True,
    "extract_links": True
}
```

### 3. **Sosyal Medya Scraping**

```python
data = {
    "url": "https://social-media.com/profile",
    "use_proxy": True,
    "wait_time": 10,
    "take_screenshot": True
}
```

## 🎯 Sonuç

Bu API ile:
- ✅ **Güvenli kullanım** - API key authentication
- ✅ **POST only** - Sadece POST methodları
- ✅ **Proxy desteği** - IP gizleme
- ✅ **Esnek parametreler** - İhtiyaca göre ayarlama
- ✅ **Hızlı sonuç** - Asenkron işlemler
- ✅ **Detaylı çıktı** - HTML, metin, link'ler, resimler

**API URL**: `http://localhost:8888` (or your domain)
**Dokümantasyon**: `http://localhost:8888/docs` (or your domain)
**Authentication**: X-API-Key header required 