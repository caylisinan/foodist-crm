import API from "../api.js";
import { toast, escapeHtml, confirmDialog } from "../helpers.js";

let editingId = null;

export default {
  key: "participants",
  label: "🏢 Katılımcı Firma",
  adminOnly: true,

  async render(container, state) {
    container.innerHTML = `
      <div class="page-title">Katılımcı Firma Yönetimi</div>
      <div class="page-hint">Fuara katılan firmaları buradan yönetin.</div>

      <div class="card">
        <h3 id="form-title">Katılımcı Ekle</h3>
        <div class="form-grid">
          <div class="form-field"><label>Firma Adı *</label><input id="f-company"></div>
          <div class="form-field"><label>Yetkili Ad Soyad</label><input id="f-contact"></div>
          <div class="form-field"><label>Ülke</label><input id="f-country"></div>
          <div class="form-field"><label>E-posta</label><input id="f-email"></div>
          <div class="form-field"><label>Telefon</label><input id="f-phone"></div>
          <div class="form-field"><label>Sektör</label><input id="f-sector"></div>
          <div class="form-field full"><label>Sunulan Ürünler (virgülle ayırın)</label><input id="f-products"></div>
          <div class="form-field"><label>Stand No</label><input id="f-stand"></div>
        </div>
        <button class="btn primary" id="save-btn">Kaydet</button>
        <button class="btn ghost" id="clear-btn">Temizle / Yeni</button>
      </div>

      <div class="table-wrap"><table>
        <thead><tr>
          <th>Firma</th><th>Yetkili</th><th>Ülke</th><th>Sektör</th><th>Stand No</th><th>E-posta</th><th></th>
        </tr></thead>
        <tbody id="participants-tbody"></tbody>
      </table></div>
    `;

    editingId = null;
    container.querySelector("#save-btn").addEventListener("click", () => this.save(container, state));
    container.querySelector("#clear-btn").addEventListener("click", () => this.clearForm(container));

    await this.refresh(container, state);
  },

  clearForm(container) {
    editingId = null;
    container.querySelector("#form-title").textContent = "Katılımcı Ekle";
    ["f-company", "f-contact", "f-country", "f-email", "f-phone", "f-sector", "f-products", "f-stand"]
      .forEach(id => { container.querySelector("#" + id).value = ""; });
  },

  fillForm(container, p) {
    editingId = p.id;
    container.querySelector("#form-title").textContent = `Düzenleniyor: ${p.company_name}`;
    container.querySelector("#f-company").value = p.company_name || "";
    container.querySelector("#f-contact").value = p.contact_name || "";
    container.querySelector("#f-country").value = p.country || "";
    container.querySelector("#f-email").value = p.contact_email || "";
    container.querySelector("#f-phone").value = p.contact_phone || "";
    container.querySelector("#f-sector").value = p.sector || "";
    container.querySelector("#f-products").value = p.offered_products || "";
    container.querySelector("#f-stand").value = p.stand_no || "";
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
      offered_products: container.querySelector("#f-products").value.trim() || null,
      stand_no: container.querySelector("#f-stand").value.trim() || null,
    };

    try {
      if (editingId) {
        await API.updateParticipant(editingId, payload);
        toast("Katılımcı güncellendi.", "success");
      } else {
        await API.createParticipant(payload);
        toast("Katılımcı eklendi.", "success");
      }
    } catch (e) {
      toast("Kaydedilemedi: " + e.message, "error");
      return;
    }
    this.clearForm(container);
    await this.refresh(container, state);
  },

  async remove(container, state, id) {
    if (!confirmDialog("Bu katılımcı silinsin mi?")) return;
    try {
      await API.deleteParticipant(id);
      toast("Katılımcı silindi.", "success");
    } catch (e) {
      toast("Silinemedi: " + e.message, "error");
    }
    await this.refresh(container, state);
  },

  async refresh(container, state) {
    const tbody = container.querySelector("#participants-tbody");
    if (!tbody) return;
    if (!state.eventId) {
      tbody.innerHTML = `<tr><td colspan="7">Önce bir etkinlik seçin.</td></tr>`;
      return;
    }
    let list;
    try {
      list = await API.listParticipants(state.eventId);
    } catch (e) {
      tbody.innerHTML = `<tr><td colspan="7">Hata: ${escapeHtml(e.message)}</td></tr>`;
      return;
    }
    if (!list.length) {
      tbody.innerHTML = `<tr><td colspan="7">Henüz katılımcı eklenmedi.</td></tr>`;
      return;
    }

    tbody.innerHTML = list.map(p => `
      <tr data-id="${p.id}">
        <td>${escapeHtml(p.company_name)}</td>
        <td>${escapeHtml(p.contact_name) || "-"}</td>
        <td>${escapeHtml(p.country) || "-"}</td>
        <td>${escapeHtml(p.sector) || "-"}</td>
        <td>${escapeHtml(p.stand_no) || "-"}</td>
        <td>${escapeHtml(p.contact_email) || "-"}</td>
        <td>
          <button class="btn small ghost" data-action="edit">Düzenle</button>
          <button class="btn danger" data-action="delete">Sil</button>
        </td>
      </tr>
    `).join("");

    tbody.querySelectorAll("tr").forEach(row => {
      const id = parseInt(row.dataset.id);
      const p = list.find(x => x.id === id);
      row.querySelector('[data-action="edit"]').addEventListener("click", () => this.fillForm(container, p));
      row.querySelector('[data-action="delete"]').addEventListener("click", () => this.remove(container, state, id));
    });
  },
};
