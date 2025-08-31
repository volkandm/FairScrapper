# 🔒 FairScrapper Proxy Kullanım Kılavuzu

Bu kılavuz, FairScrapper projenizde proxy kullanımını açıklar.

## 📋 İçindekiler

1. [Ücretsiz Proxy Seçenekleri](#ücretsiz-proxy-seçenekleri)
2. [Proxy Bulma](#proxy-bulma)
3. [Proxy Test Etme](#proxy-test-etme)
4. [Proxy ile Scraping](#proxy-ile-scraping)
5. [Güvenlik Önerileri](#güvenlik-önerileri)

## 🆓 Ücretsiz Proxy Seçenekleri

### 1. **Free Proxy List'ler**
- **free-proxy-list.net** - En popüler
- **proxynova.com** - Güncel listeler
- **proxy-list.download** - Hızlı proxy'ler

### 2. **Tor Network (En Güvenli)**
```bash
# Tor browser yükle
brew install tor-browser  # macOS
# veya https://www.torproject.org/ adresinden indir
```

### 3. **Test Proxy'leri**
```env
# Test için
PROXY_LIST=http://httpbin.org:80
```

## 🔍 Proxy Bulma

### Otomatik Proxy Bulucu

```bash
# Ücretsiz proxy'leri bul ve test et
python free_proxy_finder.py
```

**Çıktı:**
```
✅ Found 3 working proxies:
1. http://57.129.81.201:8080 (DE)
2. http://176.126.103.194:44214 (RU)
3. http://158.69.185.37:3129 (CA)
```

### Manuel Proxy Bulma

1. **free-proxy-list.net** adresine git
2. HTTPS proxy'leri filtrele
3. IP ve port bilgilerini kopyala
4. Test et

## 🧪 Proxy Test Etme

### Hızlı Test

```bash
# Bulunan proxy'leri test et
python proxy_test.py
```

### Manuel Test

```python
from scraper import WebScraper
import asyncio

async def test_proxy():
    scraper = WebScraper()
    # Proxy will be loaded from environment variables
    
    await scraper.setup_browser()
    await scraper.navigate_to_url("https://httpbin.org/ip")
    ip = await scraper.get_element_text("pre")
    print(f"IP: {ip}")
    await scraper.close()

asyncio.run(test_proxy())
```

## 🚀 Proxy ile Scraping

### 1. .env Dosyası ile

```env
# .env dosyası
PROXY_ENABLED=true
PROXY_LIST=http://57.129.81.201:8080
```

### 2. Kod ile

```python
from scraper import WebScraper

scraper = WebScraper()
# Proxy automatically loaded from environment variables
# Proxy will be loaded from environment variables

await scraper.setup_browser()
# Normal scraping işlemleri...
```

### 3. Çoklu Proxy

```python
# .env dosyasında tanımla
PROXY_LIST=http://57.129.81.201:8080,http://158.69.185.37:3129

# Kod otomatik olarak proxy rotasyonu yapar
scraper = WebScraper()
await scraper.setup_browser()
# Scraping işlemi...
```

## 🔒 Güvenlik Önerileri

### ✅ Yapılacaklar

1. **Proxy Rotasyonu**
   ```python
   import random
   
   proxy_list = ["proxy1", "proxy2", "proxy3"]
   selected_proxy = random.choice(proxy_list)
   ```

2. **Rate Limiting**
   ```python
   import asyncio
   
   await asyncio.sleep(2)  # 2 saniye bekle
   ```

3. **User-Agent Değiştirme**
   ```python
   user_agents = [
       "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0",
       "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) Safari/605.1.15"
   ]
   ```

4. **Timeout Ayarları**
   ```python
   scraper.config.TIMEOUT = 30000  # 30 saniye
   ```

### ❌ Yapılmayacaklar

1. **Aynı proxy'yi sürekli kullanma**
2. **Çok hızlı istek gönderme**
3. **Güvenilir olmayan proxy'ler kullanma**
4. **Kişisel bilgileri proxy ile gönderme**

## 📊 Proxy Performansı

### Test Sonuçları

| Proxy | Hız | Güvenilirlik | Ülke |
|-------|-----|--------------|------|
| 57.129.81.201:8080 | ⭐⭐⭐ | ⭐⭐⭐⭐ | DE |
| 158.69.185.37:3129 | ⭐⭐⭐⭐ | ⭐⭐⭐ | CA |

### Önerilen Kullanım

```env
# En iyi proxy'leri önce kullan
PROXY_LIST=http://57.129.81.201:8080,http://158.69.185.37:3129
```

## 🛠️ Sorun Giderme

### Yaygın Hatalar

1. **Connection Refused**
   ```
   ❌ Proxy artık çalışmıyor
   ✅ Yeni proxy bul
   ```

2. **Timeout**
   ```
   ❌ Proxy yavaş
   ✅ Timeout süresini artır
   ```

3. **SSL Errors**
   ```
   ❌ HTTPS sorunu
   ✅ HTTP proxy kullan
   ```

### Debug Komutları

```bash
# Proxy test
python proxy_test.py

# IP kontrolü
python -c "
import requests
proxies = {'http': 'http://proxy:port'}
r = requests.get('https://httpbin.org/ip', proxies=proxies)
print(r.json())
"
```

## 📝 Örnek Kullanım

### Basit Örnek

```python
from scraper import WebScraper
import asyncio

async def scrape_with_proxy():
    scraper = WebScraper()
    # Proxy will be loaded from environment variables
    
    await scraper.setup_browser()
    await scraper.navigate_to_url("https://example.com")
    
    title = await scraper.get_element_text("h1")
    print(f"Title: {title}")
    
    await scraper.take_screenshot("screenshot.png")
    await scraper.close()

asyncio.run(scrape_with_proxy())
```

### Gelişmiş Örnek

```python
import asyncio
from scraper import WebScraper

async def smart_scraping():
    scraper = WebScraper()
    # Proxy list will be loaded from environment variables
    # Automatic rotation and fallback is handled by the scraper
    
    try:
        await scraper.setup_browser()
        
        # Scraping işlemleri...
        await scraper.navigate_to_url("https://target-site.com")
        
        # Rate limiting
        await asyncio.sleep(2)
        
    except Exception as e:
        print(f"Scraping failed: {e}")
    finally:
        await scraper.close()

asyncio.run(smart_scraping())
```

## 🎯 Sonuç

Proxy kullanımı web scraping'de önemlidir:

- ✅ **IP gizleme**
- ✅ **Rate limiting bypass**
- ✅ **Coğrafi kısıtlamaları aşma**
- ✅ **Bot tespitini zorlaştırma**

**Önerilen yaklaşım:** Ücretsiz proxy'leri test edin, çalışanları kaydedin ve rotasyon yapın. 