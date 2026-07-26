# Ekran Tasarımları (Wireframe)

## 1. Giriş Ekranı
```
┌───────────────────────────────┐
│   Foodist Hosted Buyer CRM     │
│                                 │
│   Kullanıcı Adı  [__________]  │
│   Şifre          [__________]  │
│                                 │
│           [ Giriş Yap ]        │
└───────────────────────────────┘
```

## 2. Ana Pencere (Sol Menü + İçerik)
```
┌──────────────┬──────────────────────────────────────────┐
│ 📅 Etkinlik   │                                          │
│ 👤 Buyer      │              [ Seçili ekran içeriği ]    │
│ 🏢 Katılımcı  │                                          │
│ 🔗 Eşleştirme │                                          │
│ ✅ Onaylar    │                                          │
│ 🗓 Takvim     │                                          │
│ 📊 Dashboard  │                                          │
│ 📄 Raporlar   │                                          │
│ ⚙ Ayarlar     │                                          │
├──────────────┤                                          │
│ Rol: Admin    │                                          │
│ [Çıkış Yap]   │                                          │
└──────────────┴──────────────────────────────────────────┘
```
`operation` rolünde: Buyer, Katılımcı, Eşleştirme, Ayarlar menüleri gizli.

## 3. Excel İçe Aktarma + Alan Eşleştirme
```
┌──────────────────────────────────────────────┐
│ 1) Dosya Seç: [ buyers.xlsx ]  [Gözat]        │
│ 2) Alan Eşleştirme                            │
│    Sistem Alanı        Excel Kolonu           │
│    Firma Adı        →  [Buyer Name    ▾]      │
│    Ülke              →  [Country       ▾]     │
│    İlgilenilen Ürün  →  [Interested Products▾]│
│    E-posta           →  [Email         ▾]     │
│    ...                                        │
│ 3) Önizleme (ilk 5 satır)                     │
│  ┌────────┬────────┬──────────────┐           │
│  │ Firma  │ Ülke   │ Ürün         │           │
│  ├────────┼────────┼──────────────┤           │
│  │ ...    │ ...    │ ...          │           │
│  └────────┴────────┴──────────────┘           │
│         [ Eşleştirmeyi Kaydet ] [ İçe Aktar ] │
└──────────────────────────────────────────────┘
```

## 4. Eşleştirme Motoru Ekranı
```
┌──────────────────────────────────────────────┐
│ Ağırlıklar   Ürün [50]%  Sektör [30]%  Ülke[20]%│
│ Ülke Filtresi: (•) Filtre yok                 │
│                ( ) Aynı ülkeleri eşleştir      │
│                ( ) Aynı ülkeleri hariç tut     │
│ Eşik Skor: [40]                                │
│                                                │
│              [ Eşleştirmeleri Oluştur ]        │
│                                                │
│ Sonuç: 214 eşleşme oluşturuldu (skor≥40)       │
└──────────────────────────────────────────────┘
```

## 5. Eşleşme / Onay Listesi
```
┌──────────────────────────────────────────────────────────────────┐
│ Durum Filtresi: [Tümü ▾]                                          │
├────────────┬──────────────┬───────┬────────────┬─────────────────┤
│ Buyer      │ Katılımcı     │ Skor  │ Durum       │ İşlem            │
├────────────┼──────────────┼───────┼────────────┼─────────────────┤
│ Al Marwan  │ ABC Gıda      │ 87.5  │ Önerildi    │ [Onayla][Reddet] │
│ Sakura Com │ XYZ Süt        │ 74.0  │ Onay Bekliyor│ (mail gönderildi)│
│ Nordic Ret │ Deniz Ürün.   │ 91.2  │ Karş. Onaylandı│ [Toplantı Kur] │
└────────────┴──────────────┴───────┴────────────┴─────────────────┘
```

## 6. Takvim / Toplantı Planlama (Saat × Buyer × Katılımcı)
```
┌───────┬────────────────┬────────────────┬────────────────┐
│ Saat  │ Al Marwan Trd. │ Sakura Commerce│ Nordic Retail  │
├───────┼────────────────┼────────────────┼────────────────┤
│ 09:00 │ [ABC Gıda]     │  boş           │  boş            │
│ 09:15 │ [XYZ Süt]      │ [Deniz Ürün.]  │  boş            │
│ 09:30 │  boş           │  boş           │ [Kuru Meyve Ltd]│
│ 09:45 │  boş           │  boş           │  boş            │
└───────┴────────────────┴────────────────┴────────────────┘
Sürükle-bırak: sağ panelden "Karşılıklı Onaylandı" durumundaki eşleşmeler
bu ızgaraya sürüklenir → sistem çakışma/limit kontrolü yapar → mail+ICS gider.
(MVP'de sürükle-bırağın ilk sürümü buton tabanlı "Bu Hücreye Ata" olarak
gelir; tam drag&drop bir sonraki iterasyonda eklenir — bkz. README.)
```

## 7. Dashboard
```
┌───────────────┬───────────────┬───────────────┬───────────────┐
│ Toplam Buyer  │ Toplam Katılımcı│ Toplam Eşleşme│ Onay Bekleyen │
│     48        │      212       │     634        │     52        │
├───────────────┼───────────────┼───────────────┼───────────────┤
│ Onaylanan     │ Planlanan Top. │ Tamamlanan     │ No-Show %     │
│    180        │      96        │     71         │    8.3%       │
└───────────────┴───────────────┴───────────────┴───────────────┘
```

## 8. Raporlar
```
┌──────────────────────────────────────────────┐
│ [ Buyer Takvimi (Excel) ]                     │
│ [ Firma Takvimi (Excel) ]                     │
│ [ Günlük Toplantı Programı (PDF) ]            │
│ [ No Show Raporu (Excel) ]                    │
│ [ En Çok Görüşme Alan Firmalar (Excel) ]      │
│ [ Ülke Bazlı Analiz (Excel) ]                 │
│ [ Sektör Bazlı Analiz (Excel) ]               │
└──────────────────────────────────────────────┘
```

## 9. Ayarlar
```
┌──────────────────────────────────────────────┐
│ SMTP: Sunucu / Port / Kullanıcı / Şifre        │
│ Ağırlıklar: Ürün % / Sektör % / Ülke %         │
│ Eşleşme Eşiği: [40]                            │
│ Varsayılan Buyer Limiti: [4] toplantı /[60] dk │
└──────────────────────────────────────────────┘
```
