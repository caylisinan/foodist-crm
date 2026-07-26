# Foodist İstanbul — Hosted Buyer B2B CRM (Masaüstü Uygulaması)

## Çalıştırma — Tek Adım

1. Bu klasörü (`foodist-crm`) bilgisayarınıza çıkarın.
2. **Python kurulu olmalı** (yoksa python.org'dan indirip kurun, kurulum
   ekranında "Add python.exe to PATH" kutusunu işaretleyin).
3. Klasörün içindeki **`baslat.bat`** dosyasına **çift tıklayın**.

Bu kadar. `baslat.bat`:
- Gerekli kütüphaneleri otomatik indirir (ilk çalıştırmada 2-5 dakika sürebilir).
- Backend'i arka planda başlatır.
- Programın penceresini açar.

İlk giriş: **admin / admin123**

## "Bu klasörü diğer bilgisayarlara da kurabilir miyim?"

Evet. Her bilgisayarda aynı adımı (Python kur + `baslat.bat`'a çift tıkla)
tekrarlarsınız. Ama **önemli bir nokta**: her bilgisayar kendi ayrı
veritabanını oluşturur — yani birbirlerinin verisini görmezler. Bu, tek
kişinin/tek bilgisayarın yönettiği kullanım için uygundur.

Eğer birden fazla kişinin **aynı** buyer/eşleşme/toplantı verisini görmesi
gerekiyorsa, bu ayrı bir kurulum gerektirir (backend'in tek bir bilgisayarda
çalışıp diğerlerinin ona bağlanması) — ihtiyacınız olursa bunu ayrıca
kurabiliriz.

## Sık Karşılaşılan Sorunlar

**"'python' is not recognized" hatası alıyorum:**
Python kurulurken "Add to PATH" işaretlenmemiş. Python'u kaldırıp
yeniden kurun, bu kutucuğu işaretleyin.

**Kütüphane kurulumu sırasında hata veriyor (WinError 183 gibi):**
Bu genelde şirket bilgisayarlarındaki antivirüs yazılımının geçici
dosyaları anlık kilitlemesinden kaynaklanır. `baslat.bat`'ı **tekrar
çift tıklamayı** deneyin — genelde ikinci denemede sorun çözülür. Israrla
tekrar ederse, IT departmanınızdan bu klasör için antivirüs istisnası
istemeniz gerekebilir, veya şahsi bilgisayarınızda deneyin.

**Program açılıyor ama "Bağlantı Hatası" veriyor:**
Backend'in başlaması biraz zaman alabilir. Programı kapatıp `baslat.bat`'ı
tekrar çalıştırın.

## Belgeler

- `docs/01_sistem_analizi.md` — amaç, roller, uçtan uca akış, eşleştirme mantığı
- `docs/02_veritabani_semasi.md` — tüm tablolar ve ilişkiler
- `docs/03_teknik_mimari.md` — mimari kararlar
- `docs/04_ekran_tasarimlari.md` — ekran wireframe'leri

## Rol Bazlı Erişim

- **admin**: Tüm ekranlar (Buyer/Katılımcı yönetimi, Excel içe aktarma,
  Eşleştirme motoru, Ayarlar dahil).
- **operation**: Sadece Dashboard, Takvim/Toplantı Planlama, Raporlar.

Yeni kullanıcı eklemek isterseniz haber verin, arayüze bir ekran ekleyebiliriz
(şu an sadece admin panelinden API üzerinden ekleniyor).
