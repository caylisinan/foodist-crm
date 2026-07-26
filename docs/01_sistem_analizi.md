# B2B Hosted Buyer Matchmaking ve Toplantı Yönetim Sistemi — Sistem Analizi

## 1. Amaç

Fuar organizasyonlarında Hosted Buyer ve katılımcı firmalar arasındaki B2B
görüşme sürecini uçtan uca yönetmek: veri içe aktarma → akıllı eşleştirme →
çift taraflı onay → toplantı planlama → hatırlatma → katılım takibi → raporlama.

## 2. Kullanıcı Rolleri ve Yetki Matrisi

| Yetki                          | Admin | Operasyon |
|---------------------------------|:-----:|:---------:|
| Buyer / Katılımcı yükleme        | ✅    | ❌        |
| Eşleşme oluşturma (motor çalıştırma) | ✅ | ❌        |
| Eşleşme onaylama (Admin onayı)   | ✅    | ❌        |
| Toplantı planlama                | ✅    | ✅        |
| Mail gönderme                    | ✅    | ✅        |
| Katılım takibi (Katıldı/Katılmadı)| ✅   | ✅        |
| Rapor alma                       | ✅    | ✅        |
| Ayarlar (SMTP, ağırlıklar)       | ✅    | ❌        |

Not: "Admin onayı", eşleşme motorunun önerdiği bir eşleşmeyi sisteme resmi
olarak sokan adımdır. Bundan sonra devreye giren **Buyer Onayı** ve
**Katılımcı Onayı** ise dış taraflardan e-posta linki üzerinden gelir.

## 3. Uçtan Uca Akış

```
[Excel İçe Aktar] → [Alan Eşleştirme] → [Buyer / Katılımcı Kayıtları]
        ↓
[Eşleştirme Motoru Çalıştır] → Skorlu Eşleşme Listesi (durum: Önerildi)
        ↓
[Admin İnceler ve Onaylar] → durum: Onay Bekliyor + Buyer'a ve Katılımcıya mail
        ↓                                         ↓
  Buyer linke tıklar                    Katılımcı linke tıklar
  (Onayla/Reddet)                        (Onayla/Reddet)
        ↓                                         ↓
   durum: Buyer Onayladı   /   Katılımcı Onayladı
        ↓ (her ikisi de onaylarsa)
   durum: Karşılıklı Onaylandı
        ↓
[Toplantı Planlama — 15 dk slot, takvim ekranı]
        ↓
   durum: Toplantı Planlandı → Buyer'a + Katılımcıya mail (tarih/saat/stand no) + ICS
        ↓
[Hatırlatma: 24 sa önce, 1 sa önce — otomatik mail]
        ↓
[Fuar Günü: Katıldı / Katılmadı işaretleme]
        ↓
   durum: Tamamlandı veya No Show
        ↓
[Dashboard + Raporlar (Excel/PDF) + CRM Geçmişi]
```

## 4. Eşleştirme Motoru — Skorlama Mantığı

Her buyer × katılımcı çifti için üç bileşen hesaplanır (0–100):

- **Ürün Uyumu**: Buyer'ın ilgilendiği ürün listesi ile katılımcının sunduğu
  ürün listesi kelime bazlı karşılaştırılır (kesişim/birleşim oranı +
  metin benzerliği). Örn. "Süt ve süt ürünleri" ↔ "Süt Ürünleri Üreticisi"
  yüksek puan alır.
- **Sektör Uyumu**: Aynı mantıkla sektör alanları karşılaştırılır
  (örn. "Industrial Machinery" ↔ "Industrial Automation" kısmi eşleşme alır).
- **Ülke Uyumu**: Admin'in seçtiği filtre moduna göre hesaplanır:
  - *Filtre yok*: farklı ülke ise 100, aynı ülke ise 40 (uluslararası
    çeşitliliği ödüllendiren varsayılan iş kararı — Ayarlar'dan değiştirilebilir).
  - *Aynı ülkeleri eşleştir*: sadece aynı ülkeden çiftler skorlanır, diğerleri elenir.
  - *Aynı ülkeleri hariç tut*: aynı ülkeden çiftler tamamen elenir.

**Toplam Skor** = Ürün×w₁ + Sektör×w₂ + Ülke×w₃ (varsayılan 50/30/20,
Ayarlar ekranından değiştirilebilir, w₁+w₂+w₃=1 olacak şekilde otomatik
normalize edilir).

Skoru bir eşiğin (varsayılan 40) altında kalan çiftler öneri listesine
hiç girmez — bu, binlerce buyer×katılımcı kombinasyonunda admin'in
anlamsız eşleşmelerle boğulmasını önler.

## 5. Toplantı Planlama Kuralları

- Her görüşme: **15 dakika**.
- Varsayılan: her buyer en fazla **4 toplantı / 60 dakika** (event bazında
  buyer kaydında override edilebilir — bazı VIP buyer'lar için 90 dk/6
  toplantı gibi).
- Planlama sırasında sistem şu çakışmaları engeller:
  - Aynı buyer için aynı saat aralığında ikinci bir toplantı.
  - Aynı katılımcı için aynı saat aralığında ikinci bir toplantı.
  - Buyer'ın günlük toplam dakika/toplantı limitinin aşılması.

## 6. E-posta ve Onay Linkleri

Sistem SMTP üzerinden (Gmail, Microsoft 365 veya kurumsal sunucu) mail
gönderir. Her eşleşme için buyer ve katılımcıya **benzersiz token'lı**
onay/red linkleri üretilir (`/approve/{token}`, `/reject/{token}`).
Link tıklanınca tarayıcıda basit bir onay sayfası açılır, ekstra giriş
gerekmez — bu, dış taraflara hesap açtırma yükünü ortadan kaldırır.

## 7. CRM Geçmişi

Sistem çoklu **etkinlik (fuar edisyonu)** kaydı tutar. Bir buyer kartı
açıldığında, o buyer'ın geçmiş etkinliklerdeki katılımları, görüştüğü
firmalar, no-show geçmişi ve toplam toplantı sayısı görülür — bu, aynı
buyer'ı yıllar içinde takip etmeyi sağlar.

## 8. Kapsam Dışı (Bu MVP'de Değil, Mimari Buna Hazır)

- Outlook / Google Calendar gerçek zamanlı iki yönlü senkronizasyon
  (OAuth uygulama kaydı gerektirir — kurumun Azure/Google Cloud hesabı
  belirlenince eklenir). Şimdilik **ICS dosyası indirme** ile karşılanıyor;
  kullanıcı bunu tek tıkla Outlook/Google'a "içe aktar" edebilir.
- Yapay zekâ destekli otomatik öneri motoru ("Almanya'dan gelen alıcılar
  için en uygun 20 katılımcıyı öner" gibi doğal dil komutları). Veritabanı
  ve API şeması bunu destekleyecek şekilde tasarlandı (bkz. mimari
  dokümanı, "AI Modülü Hazırlığı" bölümü); ileride Claude/OpenAI API'sini
  mevcut `/matches/generate` uç noktasının üzerine ince bir katman olarak
  eklemek yeterli olacak.
