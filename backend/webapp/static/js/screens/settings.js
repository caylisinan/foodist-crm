import API from "../api.js";
import { toast } from "../helpers.js";

export default {
  key: "settings",
  label: "⚙ Ayarlar",
  adminOnly: true,

  async render(container, state) {
    container.innerHTML = `
      <div class="page-title">Ayarlar</div>
      <div class="page-hint">SMTP e-posta ayarları ve eşleştirme varsayılanları.</div>

      <div class="card">
        <h3>E-posta (SMTP) Ayarları</h3>
        <div class="form-grid">
          <div class="form-field"><label>SMTP Sunucu</label><input id="s-host" placeholder="ör. smtp.gmail.com"></div>
          <div class="form-field"><label>Port</label><input id="s-port" placeholder="587"></div>
          <div class="form-field"><label>Kullanıcı Adı</label><input id="s-user" placeholder="ör. matchmaking@foodistexpo.com"></div>
          <div class="form-field"><label>Şifre / Uygulama Şifresi</label><input id="s-pass" type="password"></div>
          <div class="form-field"><label>Gönderen Adı</label><input id="s-from-name" placeholder="Foodist İstanbul"></div>
          <div class="form-field"><label>Gönderen E-posta</label><input id="s-from-email"></div>
        </div>
        <div class="checkbox-row" style="margin-bottom:16px;">
          <input type="checkbox" id="s-secure">
          <label for="s-secure">465 portu için SSL/TLS kullan (Gmail için genelde 587 + kapalı bırakın)</label>
        </div>
        <div style="color:var(--ash); font-size:12px; margin-bottom:14px;">
          Gmail kullanıyorsanız normal şifre değil, Google hesabınızdan oluşturduğunuz "Uygulama Şifresi" gerekir.
        </div>
      </div>

      <div class="card">
        <h3>Eşleştirme Varsayılanları</h3>
        <div class="form-grid">
          <div class="form-field"><label>Ürün Ağırlığı (%)</label><input id="s-weight-product"></div>
          <div class="form-field"><label>Sektör Ağırlığı (%)</label><input id="s-weight-sector"></div>
          <div class="form-field"><label>Ülke Ağırlığı (%)</label><input id="s-weight-country"></div>
          <div class="form-field"><label>Eşik Skor</label><input id="s-threshold"></div>
          <div class="form-field"><label>Varsayılan Buyer Toplantı Limiti</label><input id="s-max-meetings"></div>
          <div class="form-field"><label>Varsayılan Buyer Dakika Limiti</label><input id="s-max-minutes"></div>
        </div>
      </div>

      <button class="btn primary" id="save-settings-btn">Ayarları Kaydet</button>
    `;

    container.querySelector("#save-settings-btn").addEventListener("click", () => this.save(container));
    await this.loadSettings(container);
  },

  async loadSettings(container) {
    let s;
    try {
      s = await API.getSettings();
    } catch (e) {
      toast("Ayarlar alınamadı: " + e.message, "error");
      return;
    }
    container.querySelector("#s-host").value = s.smtp_host || "";
    container.querySelector("#s-port").value = s.smtp_port || "587";
    container.querySelector("#s-user").value = s.smtp_user || "";
    container.querySelector("#s-pass").value = s.smtp_pass || "";
    container.querySelector("#s-from-name").value = s.smtp_from_name || "";
    container.querySelector("#s-from-email").value = s.smtp_from_email || "";
    container.querySelector("#s-secure").checked = (s.smtp_secure === "true");
    container.querySelector("#s-weight-product").value = s.weight_product || "50";
    container.querySelector("#s-weight-sector").value = s.weight_sector || "30";
    container.querySelector("#s-weight-country").value = s.weight_country || "20";
    container.querySelector("#s-threshold").value = s.match_threshold || "40";
    container.querySelector("#s-max-meetings").value = s.default_max_meetings || "4";
    container.querySelector("#s-max-minutes").value = s.default_max_minutes || "60";
  },

  async save(container) {
    const payload = {
      smtp_host: container.querySelector("#s-host").value.trim(),
      smtp_port: container.querySelector("#s-port").value.trim(),
      smtp_user: container.querySelector("#s-user").value.trim(),
      smtp_pass: container.querySelector("#s-pass").value,
      smtp_from_name: container.querySelector("#s-from-name").value.trim(),
      smtp_from_email: container.querySelector("#s-from-email").value.trim(),
      smtp_secure: container.querySelector("#s-secure").checked ? "true" : "false",
      weight_product: container.querySelector("#s-weight-product").value,
      weight_sector: container.querySelector("#s-weight-sector").value,
      weight_country: container.querySelector("#s-weight-country").value,
      match_threshold: container.querySelector("#s-threshold").value,
      default_max_meetings: container.querySelector("#s-max-meetings").value,
      default_max_minutes: container.querySelector("#s-max-minutes").value,
    };
    try {
      await API.updateSettings(payload);
      toast("Ayarlar kaydedildi.", "success");
    } catch (e) {
      toast("Kaydedilemedi: " + e.message, "error");
    }
  },
};
