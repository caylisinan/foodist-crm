import API from "../api.js";
import { toast, escapeHtml, confirmDialog } from "../helpers.js";

let editingId = null;

export default {
  key: "buyers",
  label: "👤 Hosted Buyer",
  adminOnly: true,

  async render(container, state) {
    container.innerHTML = `
      <div class="page-title">Hosted Buyer Yönetimi</div>
      <div class="page-hint">Alım heyeti üyelerini ve yetkili kişilerini buradan yönetin.</div>

      <div class="card">
        <h3 id="form-title">Buyer Ekle</h3>
        <div class="form-grid">
          <div class="form-field"><label>Firma Adı *</label><input id="f-company"></div>
          <div class="form-field"><label>Yetkili Ad Soyad</label><input id="f-contact"></div>
          <div class="form-field"><label>Ülke</label><input id="f-country"></div>
          <div class="form-field"><label>E-posta</label><input id="f-email"></div>
          <div class="form-field"><label>Telefon</label><input id="f-phone"></div>
          <div class="form-field"><label>Sektör</label><input id="f-sector"></div>
          <div class="form-field full"><label>İlgilenilen Ürünler (virgülle ayırın)</label><input id="f-products"></div>
          <div class="form-field"><label>Maks. Toplantı</label><input id="f-max-meetings" type="number" value="4"></div>
          <div class="form-field"><label>Maks. Dakika</label><input id="f-max-minutes" type="number" value="60"></div>
        </div>
        <button class="btn primary" id="save-btn">Kaydet</button>
        <button class="btn ghost" id="clear-btn">Temizle / Yeni</button>
      </div>

      <div class="table-wrap"><table>
        <thead><tr>
          <th>Firma</th><th>Yetkili</th><th>Ülke</th><th>Sektör</th><th>E-posta</th><th>Limit</th><th></th>
        </tr></thead>
        <tbody id="buyers-tbody"></tbody>
      </table></div>
    `;

    editingId = null;
    container.querySelector("#save-btn").addEventListener("click", () => this.save(container, state));
    container.querySelector("#clear-btn").addEventListener("click", () => this.clearForm(container));

    await this.refresh(container, state);
  },

  clearForm(container) {
    editingId = null;
    container.querySelector("#form-title").textContent = "Buyer Ekle";
    ["f-company", "f-contact", "f-country", "f-email", "f-phone", "f-sector", "f-products"]
      .forEach(id => { container.querySelector("#" + id).value = ""; });
    container.querySelector("#f-max-meetings").value = 4;
    container.querySelector("#f-max-minutes").value = 60;
  },

  fillForm(container, buyer) {
    editingId = buyer.id;
    container.querySelector("#form-title").textContent = `Düzenleniyor: ${buyer.company_name}`;
    container.querySelector("#f-company").value = buyer.company_name || "";
    container.querySelector("#f-contact").value = buyer.contact_name || "";
    container.querySelector("#f-country").value = buyer.country || "";
    container.querySelector("#f-email").value = buyer.contact_email || "";
    container.querySelector("#f-phone").value = buyer.contact_phone || "";
    container.querySelector("#f-sector").value = buyer.sector || "";
    container.querySelector("#f-products").value = buyer.interested_products || "";
    container.querySelector("#f-max-meetings").value = buyer.max_meetings || 4;
    container.querySelector("#f-max-minutes").value = buyer.max_minutes || 60;
    window.scrollTo({ top: 0, behavior: "smooth" });
  },

  async save(container, state) {
    if (!state.eventId) { toast("Önce bir etkinlik seçin.", "error"); return; }
    const company = container.querySelector("#f-company").value.trim();
    if (!company) { toast("Firma adı zorunludur.", "error"); return; }

    const payload = {
      event_id: state.eventId,
      company_name: company,
      contact_name: container.querySelector("#f-contact").value.trim() || null,
      country: container.querySelector("#f-country").value.trim() || null,
      contact_email: container.querySelector("#f-email").value.trim() || null,
      contact_phone: container.querySelector("#f-phone").value.trim() || null,
      sector: container.querySelector("#f-sector").value.trim() || null,
      interested_products: container.querySelector("#f-products").value.trim() || null,
      max_meetings: parseInt(container.querySelector("#f-max-meetings").value) || 4,
      max_minutes: parseInt(container.querySelector("#f-max-minutes").value) || 60,
    };

    try {
      if (editingId) {
        await API.updateBuyer(editingId, payload);
        toast("Buyer güncellendi.", "success");
      } else {
        await API.createBuyer(payload);
        toast("Buyer eklendi.", "success");
      }
    } catch (e) {
      toast("Kaydedilemedi: " + e.message, "error");
      return;
    }
    this.clearForm(container);
    await this.refresh(container, state);
  },

  async remove(container, state, id) {
    if (!confirmDialog("Bu buyer silinsin mi?")) return;
    try {
      await API.deleteBuyer(id);
      toast("Buyer silindi.", "success");
    } catch (e) {
      toast("Silinemedi: " + e.message, "error");
    }
    await this.refresh(container, state);
  },

  async showHistory(id) {
    try {
      const data = await API.buyerHistory(id);
      const companies = data.met_companies.length ? data.met_companies.join(", ") : "—";
      alert(
        `Firma: ${data.company_name}\n\n` +
        `Katıldığı etkinlik sayısı: ${data.events_participated}\n` +
        `Toplam toplantı: ${data.total_meetings}\n` +
        `Tamamlanan: ${data.completed_meetings}\n` +
        `No-Show: ${data.no_show_count}\n\n` +
        `Görüştüğü Firmalar:\n${companies}`
      );
    } catch (e) {
      toast("Geçmiş alınamadı: " + e.message, "error");
    }
  },

  async refresh(container, state) {
    const tbody = container.querySelector("#buyers-tbody");
    if (!tbody) return;
    if (!state.eventId) {
      tbody.innerHTML = `<tr><td colspan="7">Önce bir etkinlik seçin.</td></tr>`;
      return;
    }
    let buyers;
    try {
      buyers = await API.listBuyers(state.eventId);
    } catch (e) {
      tbody.innerHTML = `<tr><td colspan="7">Hata: ${escapeHtml(e.message)}</td></tr>`;
      return;
    }
    if (!buyers.length) {
      tbody.innerHTML = `<tr><td colspan="7">Henüz buyer eklenmedi.</td></tr>`;
      return;
    }

    tbody.innerHTML = buyers.map(b => `
      <tr data-id="${b.id}">
        <td>${escapeHtml(b.company_name)}</td>
        <td>${escapeHtml(b.contact_name) || "-"}</td>
        <td>${escapeHtml(b.country) || "-"}</td>
        <td>${escapeHtml(b.sector) || "-"}</td>
        <td>${escapeHtml(b.contact_email) || "-"}</td>
        <td>${b.max_meetings} top. / ${b.max_minutes} dk</td>
        <td>
          <button class="btn small ghost" data-action="edit">Düzenle</button>
          <button class="btn small ghost" data-action="history">Geçmiş</button>
          <button class="btn danger" data-action="delete">Sil</button>
        </td>
      </tr>
    `).join("");

    tbody.querySelectorAll("tr").forEach(row => {
      const id = parseInt(row.dataset.id);
      const buyer = buyers.find(b => b.id === id);
      row.querySelector('[data-action="edit"]').addEventListener("click", () => this.fillForm(container, buyer));
      row.querySelector('[data-action="history"]').addEventListener("click", () => this.showHistory(id));
      row.querySelector('[data-action="delete"]').addEventListener("click", () => this.remove(container, state, id));
    });
  },
};
