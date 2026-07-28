import API from "../api.js";
import { toast, escapeHtml } from "../helpers.js";

function todayStr() {
  return new Date().toISOString().slice(0, 10);
}

export default {
  key: "calendar",
  label: "🗓 Takvim / Toplantı",
  adminOnly: false,

  async render(container, state) {
    const today = todayStr();
    container.innerHTML = `
      <div class="page-title">Takvim / Toplantı Planlama</div>
      <div class="page-hint">Karşılıklı onaylanan eşleşmeleri seçip tarih/saat vererek 15 dakikalık toplantı planlayın.</div>

      <div class="card">
        <h3>Toplantı Planla</h3>
        <div class="form-grid">
          <div class="form-field full">
            <label>Karşılıklı Onaylanan Eşleşme</label>
            <select id="eligible-select"></select>
          </div>
          <div class="form-field"><label>Tarih</label><input id="meeting-date" type="date" value="${today}"></div>
          <div class="form-field"><label>Başlangıç Saati (15 dk'lık slot)</label><input id="meeting-time" placeholder="ör. 10:00"></div>
          <div class="form-field"><label>Stand No (opsiyonel override)</label><input id="meeting-stand"></div>
        </div>
        <button class="btn primary" id="schedule-btn">Toplantıyı Planla ve Mail Gönder</button>
        <button class="btn ghost" id="schedule-no-mail-btn">Toplantıyı Planla (Mailsiz)</button>
      </div>

      <div class="filter-row">
        <label>Görüntülenen Gün:</label>
        <input id="view-date" type="date" value="${today}">
        <button class="btn ghost" id="refresh-btn">Yenile</button>
      </div>

      <div class="table-wrap"><table>
        <thead><tr>
          <th>Saat</th><th>Buyer</th><th>Katılımcı</th><th>Stand No</th><th>Durum</th><th>Katılım</th><th>ICS</th>
        </tr></thead>
        <tbody id="meetings-tbody"></tbody>
      </table></div>
    `;

    container.querySelector("#schedule-btn").addEventListener("click", () => this.schedule(container, state, true));
    container.querySelector("#schedule-no-mail-btn").addEventListener("click", () => this.schedule(container, state, false));
    container.querySelector("#view-date").addEventListener("change", () => this.refreshMeetings(container, state));
    container.querySelector("#refresh-btn").addEventListener("click", () => this.refresh(container, state));

    await this.refresh(container, state);
  },

  async refresh(container, state) {
    await this.refreshEligible(container, state);
    await this.refreshMeetings(container, state);
  },

  async refreshEligible(container, state) {
    const select = container.querySelector("#eligible-select");
    if (!state.eventId) { select.innerHTML = ""; return; }

    let approved, scheduled;
    try {
      approved = await API.listMatches(state.eventId, "Karşılıklı Onaylandı");
      scheduled = await API.listMatches(state.eventId, "Toplantı Planlandı");
    } catch (e) {
      toast("Hata: " + e.message, "error");
      return;
    }
    const combined = approved.concat(scheduled);
    if (!combined.length) {
      select.innerHTML = `<option value="">(Uygun eşleşme yok)</option>`;
      return;
    }
    select.innerHTML = combined.map(m =>
      `<option value="${m.id}">${escapeHtml(m.buyer_name)} ↔ ${escapeHtml(m.participant_name)} (skor ${m.total_score}, ${m.status})</option>`
    ).join("");
  },

  async refreshMeetings(container, state) {
    const tbody = container.querySelector("#meetings-tbody");
    if (!state.eventId) { tbody.innerHTML = `<tr><td colspan="7">Önce bir etkinlik seçin.</td></tr>`; return; }

    const meetingDate = container.querySelector("#view-date").value;
    let meetings;
    try {
      meetings = await API.listMeetings(state.eventId, meetingDate);
    } catch (e) {
      tbody.innerHTML = `<tr><td colspan="7">Hata: ${escapeHtml(e.message)}</td></tr>`;
      return;
    }

    if (!meetings.length) {
      tbody.innerHTML = `<tr><td colspan="7">Bu tarihte planlanmış toplantı yok.</td></tr>`;
      return;
    }

    tbody.innerHTML = meetings.map(m => `
      <tr data-id="${m.id}">
        <td>${m.start_time}-${m.end_time}</td>
        <td>${escapeHtml(m.buyer_name) || "-"}</td>
        <td>${escapeHtml(m.participant_name) || "-"}</td>
        <td>${escapeHtml(m.stand_no) || "-"}</td>
        <td>${escapeHtml(m.status)}</td>
        <td>
          <select data-action="attendance">
            <option ${m.status === "Planlandı" ? "selected" : ""}>Planlandı</option>
            <option ${m.status === "Tamamlandı" ? "selected" : ""}>Tamamlandı</option>
            <option ${m.status === "Katılmadı" ? "selected" : ""}>Katılmadı</option>
          </select>
        </td>
        <td><a class="btn small ghost" href="${API.icsDownloadUrl(m.id)}" download>İndir (.ics)</a></td>
      </tr>
    `).join("");

    tbody.querySelectorAll("tr").forEach(row => {
      const id = parseInt(row.dataset.id);
      row.querySelector('[data-action="attendance"]').addEventListener("change", async (e) => {
        try {
          await API.updateAttendance(id, e.target.value);
          toast("Katılım durumu güncellendi.", "success");
        } catch (err) {
          toast("Hata: " + err.message, "error");
        }
      });
    });
  },

  async schedule(container, state, sendEmail = true) {
    const select = container.querySelector("#eligible-select");
    if (!select.value) { toast("Önce 'Eşleştirme' ekranından eşleşmeleri karşılıklı onaylatmanız gerekir.", "error"); return; }

    const time = container.querySelector("#meeting-time").value.trim();
    if (!time.includes(":")) { toast("Saat alanını 'SS:DD' formatında girin (ör. 10:00).", "error"); return; }

    const payload = {
      match_id: parseInt(select.value),
      meeting_date: container.querySelector("#meeting-date").value,
      start_time: time,
      stand_no: container.querySelector("#meeting-stand").value.trim() || null,
      send_email: sendEmail,
    };

    try {
      await API.scheduleMeeting(payload);
    } catch (e) {
      toast("Planlanamadı: " + e.message, "error");
      return;
    }

    toast(sendEmail
      ? "Toplantı planlandı ve taraflara bilgilendirme e-postası gönderildi."
      : "Toplantı planlandı (mail gönderilmedi).", "success");
    container.querySelector("#view-date").value = payload.meeting_date;
    await this.refresh(container, state);
  },
};
