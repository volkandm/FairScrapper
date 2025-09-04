# Proxy Test Sonuçları

## GitHub'dan Bulunan Çalışan Proxy'ler

GitHub'daki [TheSpeedX/PROXY-List](https://github.com/TheSpeedX/PROXY-List/blob/master/socks4.txt) listesinden test edilen ve çalışan proxy'ler.

### Test Sonuçları
- **Toplam Test Edilen:** 500 proxy
- **Çalışan Proxy Sayısı:** 15/20 (ilk 20'den)
- **Başarı Oranı:** %75

### Çalışan Proxy Listesi (Response Time'a Göre Sıralı)

| Proxy | Response Time | Durum | IP |
|-------|---------------|-------|----|
| `4.245.123.244:80` | 0.27s | ✅ Working | 20.56.66.202 |
| `89.58.57.45:80` | 0.29s | ✅ Working | 89.58.57.45 |
| `23.247.136.254:80` | 0.50s | ✅ Working | 23.247.136.254 |
| `62.182.204.81:88` | 0.62s | ✅ Working | 62.182.204.81 |
| `84.247.188.39:8888` | 0.72s | ✅ Working | 176.234.134.121, 193.19.205.94 |
| `104.222.32.98:80` | 0.73s | ✅ Working | 104.222.32.98 |
| `134.209.29.120:80` | 1.17s | ✅ Working | 134.209.29.120 |
| `65.108.203.37:28080` | 1.82s | ✅ Working | 77.111.246.23 |
| `89.117.145.245:3128` | 1.75s | ✅ Working | 89.117.145.245 |
| `38.188.178.1:999` | 2.07s | ✅ Working | 176.234.134.121, 190.242.157.206 |
| `39.104.27.89:8001` | 2.56s | ✅ Working | 39.104.27.89 |
| `103.172.42.227:8080` | 3.57s | ✅ Working | 176.234.134.121, 103.172.42.247 |
| `209.121.164.51:31147` | 4.22s | ✅ Working | 172.30.209.0, 209.121.164.53 |
| `41.59.90.175:80` | 6.00s | ✅ Working | 41.59.65.202 |
| `41.191.203.167:80` | 7.66s | ✅ Working | 41.191.206.129 |

### Çalışmayan Proxy'ler
- `123.141.181.7:5031` - Server disconnected
- `8.137.62.53:8443` - Connection reset by peer
- `170.81.171.189:8282` - Connection failed
- `202.5.37.104:17382` - Connection failed
- `114.130.175.18:8080` - Connection failed

### Kullanım

Bu proxy'ler `config.py` dosyasında otomatik olarak yapılandırılmıştır:

```python
PROXY_LIST = [
    "4.245.123.244:80",
    "209.121.164.51:31147",
    "104.222.32.98:80",
    # ... diğer proxy'ler
]
```

### Test Tarihi
- **Test Tarihi:** 3 Eylül 2025
- **Test URL:** http://httpbin.org/ip
- **Timeout:** 10 saniye
- **Test Metodu:** SOCKS4 proxy ile HTTP request

### Notlar
- En hızlı proxy: `4.245.123.244:80` (0.27s)
- En yavaş proxy: `41.191.203.167:80` (7.66s)
- Tüm proxy'ler SOCKS4 protokolü kullanıyor
- Proxy rotation aktif ve otomatik olarak çalışan proxy'ler arasında geçiş yapıyor

