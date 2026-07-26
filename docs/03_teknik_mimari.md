# Teknik Mimari

## Genel Yaklaşım

```
┌───────────────────────────────────────────────────────────┐
│  TEK bir bilgisayar/sunucu (server_launcher.py)             │
│                                                               │
│   FastAPI Backend (uvicorn) ── SQLAlchemy ORM ── SQLite      │
│         │                                                     │
│         └── backend/webapp/ (statik HTML/CSS/JS) sunar        │
└───────────────────────────┬───────────────────────────────┘
                             │  http://<sunucu-ip>:8000
          ┌──────────────────┼──────────────────┐
          ▼                  ▼                  ▼
      Tarayıcı           Tarayıcı           Tarayıcı
    (admin, PC 1)      (operasyon, PC 2)   (operasyon, PC 3)

Ayrıca aynı FastAPI süreci içinde:
- SMTP istemcisi (smtplib) → e-posta gönderimi
- Arka plan zamanlayıcı (APScheduler) → 24sa/1sa toplantı hatırlatmaları
- /approve/{token} ve /reject/{token} → dış tarafların (buyer/katılımcı)
  hiçbir kurulum yapmadan, sadece tarayıcıdan tek tıkla onay vermesi
```

**Neden web tabanlı (masaüstü uygulaması değil)?**
İlk tasarım PySide6 masaüstü arayüzüydü, ancak bu iki pratik sorun
doğuruyordu: (1) her kullanıcı bilgisayarına Python + bağımlılık kurulması
gerekiyordu, (2) her bilgisayar kendi bağımsız veritabanını oluşturuyordu
— yani ekip aynı veriyi göremiyordu. Web tabanlı yaklaşımda:
1. Backend'in çalıştığı **tek** bilgisayarda Python bir kez kurulur.
2. Diğer **tüm** kullanıcılar zaten sahip oldukları bir tarayıcıyı açar —
   sıfır kurulum.
3. Herkes aynı backend'e bağlandığı için **otomatik olarak aynı veriyi görür.**
4. Onay linkleri (`/approve/{token}`) zaten tarayıcıdan açılıyordu, bu
   tutarlılığı arayüzün geri kalanına da taşımak doğal bir adımdı.
5. Yapay zekâ modülü (Claude/OpenAI) ileride ayrı bir servis/uç nokta
   olarak aynı veritabanına bu API üzerinden bağlanabilir.


## Katman Sorumlulukları

| Katman | Sorumluluk |
|---|---|
| `backend/webapp/` (statik HTML/CSS/JS) | Ekranlar, kullanıcı girişi, backend'e fetch() istekleri (tarayıcıda çalışır) |
| `backend/app/routers/` | HTTP uç noktaları (CRUD, import, matching, scheduling, dashboard) |
| `backend/app/deps.py` | Rol bazlı erişim kontrolü (X-User-Role header, admin-only uç noktalar) |
| `backend/app/matching.py` | Skorlama motoru (saf Python, backend'den bağımsız test edilebilir) |
| `backend/app/email_service.py` | SMTP gönderimi + Türkçe e-posta şablonları |
| `backend/app/calendar_ics.py` | ICS dosyası üretimi |
| `backend/app/reports.py` | Excel/PDF rapor üretimi (openpyxl / reportlab) |
| `backend/app/scheduler.py` | APScheduler — periyodik hatırlatma taraması |
| `backend/app/models.py` | SQLAlchemy tablo tanımları (bkz. 02_veritabani_semasi.md) |
| `server_launcher.py` | Sunucuyu başlatır, yerel ağ IP'sini ekrana yazar |

## Rol Bazlı Erişim

Frontend, giriş yapan kullanıcının `role` bilgisine göre menüleri gösterir/gizler
(Buyer Yükleme, Eşleştirme Motoru, Onaylama gibi admin-only ekranlar
`operation` rolünde devre dışı kalır). Backend tarafında da her admin-only
uç nokta, gelen isteğin `X-User-Role` header'ını kontrol eder — yani
yetki kontrolü sadece arayüzde değil, API seviyesinde de var.

## AI Modülü Hazırlığı

`/matches/generate` uç noktası şu an kural tabanlı `matching.py` motorunu
çağırıyor. İleride bu uç noktaya `engine=ai` parametresi eklenip,
`matching.py` yerine bir `ai_matching.py` modülü (Claude API'ye buyer/katılımcı
listesini yapılandırılmış JSON olarak gönderip skor isteyen) devreye alınabilir.
Veritabanı şeması zaten skor bileşenlerini (`product_score`, `sector_score`,
`country_score`) ayrı sütunlarda tuttuğu için, motor değişse de raporlama ve
onay akışı hiç değişmeden çalışır.

## Dağıtım

Sunucu olacak bilgisayarda: `pip install -r backend/requirements.txt`,
ardından `python server_launcher.py`. Bu tek komut backend'i başlatır,
web arayüzünü aynı adresten sunar ve ekrana yerel ağ IP'sini yazdırır.
Diğer tüm bilgisayarlar hiçbir kurulum yapmadan, sadece bu adrese
tarayıcıdan giderek sisteme erişir (bkz. README.md).
