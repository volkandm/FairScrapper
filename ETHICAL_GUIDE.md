# FairScrapper Ethical Usage Guide

## 🎯 Etik Web Scraping Pratikleri

FairScrapper, etik ve yasal web scraping için tasarlanmıştır. Bu rehber, sorumlu kullanım için önemli kuralları içerir.

## ⚖️ Yasal Durum

### ✅ Genellikle Yasal Olan Kullanımlar:

1. **Halka Açık Veriler:**
   - RSS feed'leri
   - API'ler (rate limit'lere uygun)
   - Creative Commons lisanslı içerik
   - Açık veri setleri

2. **Kendi Siteniz:**
   - Kendi web sitenizi test etme
   - Performans izleme
   - SEO analizi

3. **Eğitim ve Araştırma:**
   - Akademik araştırmalar
   - Öğrenme amaçlı kullanım
   - Teknik deneyler

### ❌ Yasal Olmayan Kullanımlar:

1. **Telif Hakkı İhlali:**
   - Özel içeriği izinsiz kopyalama
   - Ticari amaçla içerik çalma
   - Lisanssız kullanım

2. **Kişisel Veri:**
   - GDPR/CCPA ihlali
   - Rıza olmadan kişisel bilgi toplama
   - Hassas veri işleme

3. **Kullanım Şartları İhlali:**
   - Site ToS'unu ihlal etme
   - Hesap oluşturma yasağı
   - Otomatik erişim yasağı

## 🛡️ Etik Kullanım Kuralları

### 1. **robots.txt Dosyasına Uyun**
```bash
# Örnek robots.txt kontrolü
User-agent: *
Disallow: /private/
Allow: /public/
```

### 2. **Rate Limiting Uygulayın**
- Makul bekleme süreleri (1-5 saniye)
- Sunucuya yük bindirmeyin
- Peak saatlerde dikkatli olun

### 3. **Şeffaf User-Agent Kullanın**
```python
# Örnek şeffaf user agent
USER_AGENT = "FairScrapper/1.0 (+https://github.com/your-repo)"
```

### 4. **Veri Kullanımı**
- Sadece gerekli verileri toplayın
- Kişisel bilgileri filtreleyin
- Veri saklama sürelerini belirleyin

## 📋 Best Practices

### ✅ Yapılması Gerekenler:

1. **Önceden İzin Alın:**
   - Site sahiplerine danışın
   - API dokümantasyonunu okuyun
   - Kullanım şartlarını kontrol edin

2. **Düzenli Kontroller:**
   - robots.txt güncellemelerini takip edin
   - Site değişikliklerini izleyin
   - Rate limit'leri kontrol edin

3. **Veri Kalitesi:**
   - Doğru veri toplayın
   - Hataları düzeltin
   - Kaynakları belirtin

### ❌ Yapılmaması Gerekenler:

1. **Aşırı Yük Bindirme:**
   - Çok hızlı istekler
   - Paralel bağlantılar
   - Sunucu kaynaklarını tüketme

2. **Gizli Scraping:**
   - Sahte user agent
   - IP gizleme (yasal olmayan durumlarda)
   - Bot tespitinden kaçınma

3. **Veri Kötüye Kullanımı:**
   - Spam gönderme
   - Rekabet analizi
   - Ticari avantaj sağlama

## 🔧 FairScrapper Güvenlik Özellikleri

### 1. **Otomatik Rate Limiting**
```python
# Varsayılan bekleme süreleri
DEFAULT_WAIT_TIME = 5000  # 5 saniye
MAX_RETRIES = 3
```

### 2. **Proxy Rotasyonu**
- Yük dağıtımı
- Sunucu dostu yaklaşım
- Otomatik hata yönetimi

### 3. **Şeffaf Logging**
- Tüm aktiviteleri kaydetme
- Hata raporlama
- Performans izleme

## 📞 Yasal Destek

### Kaynaklar:
- [Web Scraping Legal Guide](https://www.scrapingbee.com/blog/web-scraping-legal/)
- [GDPR Compliance](https://gdpr.eu/)
- [robots.txt Standard](https://www.robotstxt.org/)

### Öneriler:
1. Yasal danışmanlık alın
2. Site sahipleriyle iletişime geçin
3. Kullanım şartlarını dikkatle okuyun
4. Veri koruma yasalarını öğrenin

## 🎯 Sonuç

FairScrapper, etik ve yasal web scraping için tasarlanmıştır. Bu rehberi takip ederek sorumlu kullanım sağlayabilirsiniz.

**Unutmayın:** Bu araç sadece eğitim ve araştırma amaçlıdır. Kullanıcılar kendi yasal sorumluluklarını üstlenir.

---

*Bu rehber genel bilgi amaçlıdır ve yasal tavsiye niteliği taşımaz. Spesifik durumlar için yasal danışmanlık almanız önerilir.*
