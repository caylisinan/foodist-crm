# Ücretsiz Bulut Kurulumu — Adım Adım Rehber

Bu rehber, hiçbir ücret ödemeden, hiçbir bilgisayara Python kurmadan,
sistemi **internetten herkesin erişebileceği** bir adrese taşımanızı sağlar.

İki ücretsiz servis kullanacağız:
- **Neon.tech** → verilerin saklandığı yer (veritabanı)
- **Render.com** → programın çalıştığı yer (backend + web arayüzü)

Toplam süre: ~15-20 dakika. Hepsi tarayıcıdan, tıklayarak yapılır.

---

## Bölüm 1 — Neon.tech'te ücretsiz veritabanı oluşturma

1. https://neon.tech adresine gidin.
2. **"Sign up"** butonuna tıklayın. E-posta ile veya Google/GitHub hesabınızla
   kayıt olabilirsiniz.
3. Kayıt sonrası "Create a project" ekranı çıkar. Proje adına
   `foodist-crm` yazın, **"Create Project"**'e tıklayın.
4. Proje oluşunca ekranda **"Connection string"** (bağlantı adresi)
   göreceksiniz — `postgresql://...` ile başlayan uzun bir metin.
5. Bu metnin yanındaki **kopyala** simgesine tıklayıp, bir yere
   (ör. Not Defteri) geçici olarak yapıştırın. Buna birazdan ihtiyacımız
   olacak.

---

## Bölüm 2 — GitHub'a kodu yükleme

1. https://github.com adresine gidin, hesabınız yoksa **"Sign up"** ile
   ücretsiz bir hesap oluşturun.
2. Sağ üstteki **"+"** işaretine, ardından **"New repository"**'e tıklayın.
3. "Repository name" alanına `foodist-crm` yazın.
4. **"Public"** seçili kalsın (Private de olur, fark etmez).
5. **"Create repository"**'e tıklayın.
6. Açılan sayfada **"uploading an existing file"** yazan linke tıklayın.
7. Bilgisayarınızda daha önce çıkardığınız `foodist-crm` klasörünün
   **içindeki tüm dosya ve klasörleri** (klasörün kendisini değil, içini)
   seçip bu sayfaya sürükleyip bırakın.
8. Sayfanın altındaki **"Commit changes"** butonuna basın.
9. Birkaç saniye içinde tüm dosyalar GitHub'a yüklenmiş olacak.

---

## Bölüm 3 — Render.com'da ücretsiz olarak yayınlama

1. https://render.com adresine gidin, **"Get Started"** ile kayıt olun
   (GitHub hesabınızla giriş yapmanız işleri kolaylaştırır — "Sign up
   with GitHub" seçeneğini kullanın).
2. Giriş yaptıktan sonra sağ üstte **"New +"** → **"Blueprint"** seçin.
3. GitHub hesabınızı bağlamanızı isteyecek — izin verin.
4. Az önce oluşturduğunuz `foodist-crm` deposunu (repository) listeden
   seçin.
5. Render, içindeki `render.yaml` dosyasını otomatik bulacak ve size
   bir form gösterecek. Formda **`DATABASE_URL`** adında boş bir kutu
   göreceksiniz — Bölüm 1'de kopyaladığınız Neon bağlantı adresini
   buraya yapıştırın.
6. **"Apply"** / **"Create"** butonuna basın.
7. Render otomatik olarak kurulumu yapıp programı başlatacak — bu
   2-5 dakika sürebilir. Ekranda akan yazıları izleyebilirsiniz.
8. İşlem bitince sayfanın üstünde `https://foodist-hosted-buyer-crm-....onrender.com`
   şeklinde bir adres göreceksiniz. **İşte bu, sisteminizin herkese açık
   adresi.**

---

## Kullanım

- Bu adresi (`https://....onrender.com`) tüm ekibinizle paylaşın.
  Herkes, hangi Wi-Fi'da / hangi şehirde olursa olsun, bu adrese
  tarayıcıdan girip kullanabilir.
- İlk giriş: **admin / admin123**
- **Önemli:** Ücretsiz plan, 15 dakika kullanılmazsa "uyur". Biri tekrar
  siteye girdiğinde 30-60 saniye "uyanma" süresi olabilir — bu normaldir,
  bir hata değildir, sadece sabırla bekleyin.

## Bir şey değiştirmem gerekirse?

Kodda bir değişiklik/güncelleme gerekirse, GitHub'daki dosyaları
güncelleyip (yine "Upload files" ile üzerine yazarak) Render otomatik
olarak yeniden yayınlar — tekrar tüm bu adımları yapmanıza gerek kalmaz.
