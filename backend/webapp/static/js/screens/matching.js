import API from "../api.js";
import { toast, escapeHtml, statusBadgeClass } from "../helpers.js";

const STATUS_OPTIONS = [
  "Tümü", "Önerildi", "Onay Bekliyor", "Buyer Onayladı", "Katılımcı Onayladı",
  "Karşılıklı Onaylandı", "Toplantı Planlandı", "Tamamlandı", "No Show", "Reddedildi",
];

let matchesCache = [];

export default {
  key: "matching",
  label: "🔗 Eşleştirme / Onaylar",
  adminOnly: true,

  async render(container, state) {
    container.innerHTML = `
      <div class="page-title">Akıllı Eşleştirme Motoru</div>
      <div class="page-hint">Ağırlıkları ayarlayıp eşleştirmeleri oluşturun, ardından listeden onaylayın.</div>

      <div class="card">
        <h3>Eşleştirme Ayarları</h3>
        <div class="form-grid">
          <div class="form-field"><label>Ürün Uyumu Ağırlığı (%)</label><input id="w-product" type="number" value="50"></div>
          <div class="form-field"><label>Sektör Uyumu Ağırlığı (%)</label><input id="w-sector" type="number" value="30"></div>
          <div class="form-field"><label>Ülke Uyumu Ağırlığı (%)</label><input id="w-country" type="number" value="20"></div>
          <div class="form-field"><label>Eşik Skor</label><input id="w-threshold" type="number" value="40"></div>
          <div class="form-field full">
            <label>Ülke Filtresi</label>
            <select id="w-country-mode">
              <option value="none">Filtre yok (uluslararası çeşitlilik ödüllenir)</option>
              <option value="same_only">Aynı ülkeleri eşleştir</option>
              <option value="exclude_same">Aynı ülkeleri hariç tut</option>
            </select>
          </div>
        </div>
        <button class="btn primary" id="generate-btn">Eşleştirmeleri Oluştur</button>
      </div>

      <div class="card">
        <h3>Manuel Eşleştirme</h3>
        <div class="page-hint" style="margin-bottom:14px;">
          Otomatik motoru beklemeden, belirli bir buyer ile belirli bir firmayı doğrudan eşleştirin.
        </div>
        <div class="form-grid">
          <div class="form-field">
            <label>Hosted Buyer</label>
            <select id="manual-buyer-select"></select>
          </div>
          <div class="form-field">
            <label>Katılımcı Firma</label>
            <select id="manual-participant-select"></select>
          </div>
        </div>
        <button class="btn primary" id="manual-match-btn">Eşleştir</button>
      </div>

      <div class="filter-row">
        <label>Durum Filtresi:</label>
        <select id="status-filter">${STATUS_OPTIONS.map(s => `<option>${s}</option>`).join("")}</select>
        <button class="btn ghost" id="refresh-btn">Yenile</button>
      </div>

      <div class="filter-row">
        <button class="btn primary" id="approve-both-btn">Seçilenleri Onayla (Mail Gönder)</button>
        <button class="btn ghost" id="direct-approve-btn">Seçilenleri Direkt Onayla (Mailsiz)</button>
        <button class="btn ghost" id="approve-buyer-only-btn">Onay için sadece Hosted Buyer'a mail gönder</button>
        <button class="btn ghost" id="approve-participant-only-btn">Onay için sadece Katılımcıya mail gönder</button>
      </div>

      <div class="table-wrap"><table>
        <thead><tr>
          <th style="width:26px;"><input type="checkbox" id="select-all"></th>
          <th>Buyer</th><th>Katılımcı</th><th>Ürün</th><th>Sektör</th><th>Toplam</th><th>Durum</th>
        </tr></thead>
        <tbody id="matches-tbody"></tbody>
      </table></div>
    `;

    container.querySelector("#generate-btn").addEventListener("click", () => this.generate(container, state));
    container.querySelector("#manual-match-btn").addEventListener("click", () => this.createManualMatch(container, state));
    container.querySelector("#status-filter").addEventListener("change", () => this.refresh(container, state));
    container.querySelector("#refresh-btn").addEventListener("click", () => this.refresh(container, state));
    container.querySelector("#approve-both-btn").addEventListener("click", () => this.approveSelected(container, state, "both"));
    container.querySelector("#direct-approve-btn").addEventListener("click", () => this.directApproveSelected(container, state));
    container.querySelector("#approve-buyer-only-btn").addEventListener("click", () => this.approveSelected(container, state, "buyer"));
    container.querySelector("#approve-participant-only-btn").addEventListener("click", () => this.approveSelected(container, state, "participant"));
    container.querySelector("#select-all").addEventListener("change", (e) => {
      container.querySelectorAll(".match-checkbox").forEach(cb => { cb.checked = e.target.checked; });
    });

    await this.loadManualOptions(container, state);
    await this.refresh(container, state);
  },

  async loadManualOptions(container, state) {
    const buyerSelect = container.querySelector("#manual-buyer-select");
    const participantSelect = container.querySelector("#manual-participant-select");
    if (!state.eventId) {
      buyerSelect.innerHTML = `<option value="">(Önce etkinlik seçin)</option>`;
      participantSelect.innerHTML = `<option value="">(Önce etkinlik seçin)</option>`;
      return;
    }
    try {
      const [buyers, participants] = await Promise.all([
        API.listBuyers(state.eventId),
        API.listParticipants(state.eventId),
      ]);
      buyerSelect.innerHTML = buyers.length
        ? buyers.map(b => `<option value="${b.id}">${escapeHtml(b.company_name)} (${escapeHtml(b.country) || "-"})</option>`).join("")
        : `<option value="">(Buyer yok)</option>`;
      participantSelect.innerHTML = participants.length
        ? participants.map(p => `<option value="${p.id}">${escapeHtml(p.company_name)} (${escapeHtml(p.country) || "-"})</option>`).join("")
        : `<option value="">(Katılımcı yok)</option>`;
    } catch (e) {
      toast("Buyer/katılımcı listesi alınamadı: " + e.message, "error");
    }
  },

  async createManualMatch(container, state) {
    const buyerSelect = container.querySelector("#manual-buyer-select");
    const participantSelect = container.querySelector("#manual-participant-select");
    if (!buyerSelect.value || !participantSelect.value) {
      toast("Lütfen bir buyer ve bir katılımcı seçin.", "error");
      return;
    }
    try {
      await API.createManualMatch(parseInt(buyerSelect.value), parseInt(participantSelect.value));
      toast("Eşleşme oluşturuldu.", "success");
    } catch (e) {
      toast("Eşleştirilemedi: " + e.message, "error");
      return;
    }
    await this.refresh(container, state);
  },

  async generate(container, state) {
    if (!state.eventId) { toast("Önce bir etkinlik seçin.", "error"); return; }

    const payload = {
      event_id: state.eventId,
      weight_product: parseFloat(container.querySelector("#w-product").value) || 0,
      weight_sector: parseFloat(container.querySelector("#w-sector").value) || 0,
      weight_country: parseFloat(container.querySelector("#w-country").value) || 0,
      country_mode: container.querySelector("#w-country-mode").value,
      threshold: parseFloat(container.querySelector("#w-threshold").value) || 0,
    };

    let result;
    try {
      result = await API.generateMatches(payload);
    } catch (e) {
      toast("Hata: " + e.message, "error");
      return;
    }

    alert(
      `${result.created} yeni eşleşme oluşturuldu.\n` +
      `Zaten var olan: ${result.skipped_existing_pairs}\n` +
      `Eşik altında kalan: ${result.below_threshold}\n` +
      `Ülke filtresiyle elenen: ${result.filtered_by_country_rule}`
    );
    await this.refresh(container, state);
  },

  async refresh(container, state) {
    await this.loadManualOptions(container, state);
    const tbody = container.querySelector("#matches-tbody");
    if (!tbody || !state.eventId) {
      if (tbody) tbody.innerHTML = `<tr><td colspan="7">Önce bir etkinlik seçin.</td></tr>`;
      return;
    }
    const status = container.querySelector("#status-filter").value;
    try {
      matchesCache = await API.listMatches(state.eventId, status);
    } catch (e) {
      tbody.innerHTML = `<tr><td colspan="7">Hata: ${escapeHtml(e.message)}</td></tr>`;
      return;
    }

    if (!matchesCache.length) {
      tbody.innerHTML = `<tr><td colspan="7">Bu filtreyle eşleşme bulunamadı.</td></tr>`;
      return;
    }

    tbody.innerHTML = matchesCache.map(m => `
      <tr>
        <td><input type="checkbox" class="match-checkbox" data-id="${m.id}"></td>
        <td>${escapeHtml(m.buyer_name)}</td>
        <td>${escapeHtml(m.participant_name)}</td>
        <td>${m.product_score}</td>
        <td>${m.sector_score}</td>
        <td><strong>${m.total_score}</strong></td>
        <td><span class="${statusBadgeClass(m.status)}">${escapeHtml(m.status)}</span></td>
      </tr>
    `).join("");
  },

  async directApproveSelected(container, state) {
    const ids = [...container.querySelectorAll(".match-checkbox:checked")].map(cb => parseInt(cb.dataset.id));
    if (!ids.length) { toast("Onaylamak için en az bir eşleşme seçin.", "error"); return; }

    if (!confirm(
      `${ids.length} eşleşme, mail onayı beklenmeden doğrudan "Karşılıklı Onaylandı" ` +
      `durumuna alınacak ve Takvim ekranında toplantı planlanabilir hale gelecek. Onaylıyor musunuz?`
    )) return;

    let okCount = 0;
    const errors = [];
    for (const id of ids) {
      try {
        await API.updateMatchStatus(id, "Karşılıklı Onaylandı");
        okCount++;
      } catch (e) {
        errors.push(`Eşleşme ${id}: ${e.message}`);
      }
    }

    toast(`${okCount} eşleşme direkt onaylandı.` + (errors.length ? ` ${errors.length} hata oluştu.` : ""),
          errors.length ? "error" : "success");
    if (errors.length) alert(errors.join("\n"));

    await this.refresh(container, state);
  },

  async approveSelected(container, state, notify = "both") {
    const ids = [...container.querySelectorAll(".match-checkbox:checked")].map(cb => parseInt(cb.dataset.id));
    if (!ids.length) { toast("Onaylamak için en az bir eşleşme seçin.", "error"); return; }

    let result;
    try {
      result = await API.approveMatches(ids, notify);
    } catch (e) {
      toast("Hata: " + e.message, "error");
      return;
    }

    const describe = (skipped, sent, err) => {
      if (skipped) return "gönderilmedi (bu seçenekte hedeflenmedi)";
      if (sent) return "gönderildi";
      return `BAŞARISIZ (${err})`;
    };

    const lines = result.results.map(r => {
      if (!r.ok) return `Eşleşme ${r.match_id}: ${r.error}`;
      const b = describe(r.buyer_mail_skipped, r.buyer_mail_sent, r.buyer_mail_error);
      const p = describe(r.participant_mail_skipped, r.participant_mail_sent, r.participant_mail_error);
      return `Eşleşme ${r.match_id} — Buyer maili: ${b} | Katılımcı maili: ${p}`;
    });
    alert(lines.join("\n"));
    await this.refresh(container, state);
  },
};
