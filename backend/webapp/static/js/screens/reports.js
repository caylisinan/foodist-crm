import API from "../api.js";

function todayStr() {
  return new Date().toISOString().slice(0, 10);
}

export default {
  key: "reports",
  label: "📄 Raporlar",
  adminOnly: false,

  async render(container, state) {
    container.innerHTML = `
      <div class="page-title">Raporlar</div>
      <div class="page-hint">Excel/PDF çıktılarını indirin.</div>

      <div class="card report-list">
        <a class="btn ghost" id="rep-buyer-cal">📅 Buyer Takvimi (Excel)</a>
        <a class="btn ghost" id="rep-part-cal">📅 Firma Takvimi (Excel)</a>
        <div class="form-field" style="max-width:240px;">
          <label>Günlük Program Tarihi</label>
          <input type="date" id="rep-daily-date" value="${todayStr()}">
        </div>
        <a class="btn ghost" id="rep-daily">🗓 Günlük Toplantı Programı (PDF)</a>
        <a class="btn ghost" id="rep-noshow">🚫 No Show Raporu (Excel)</a>
        <a class="btn ghost" id="rep-top">🏆 En Çok Görüşme Alan Firmalar (Excel)</a>
        <a class="btn ghost" id="rep-country">🌍 Ülke Bazlı Analiz (Excel)</a>
        <a class="btn ghost" id="rep-sector">🏷 Sektör Bazlı Analiz (Excel)</a>
      </div>
    `;

    this.wireLinks(container, state);
  },

  wireLinks(container, state) {
    if (!state.eventId) {
      container.querySelectorAll(".report-list a").forEach(a => a.removeAttribute("href"));
      return;
    }
    const eventId = state.eventId;
    container.querySelector("#rep-buyer-cal").href = API.reportUrl("/reports/buyer-calendar", { event_id: eventId });
    container.querySelector("#rep-part-cal").href = API.reportUrl("/reports/participant-calendar", { event_id: eventId });
    container.querySelector("#rep-noshow").href = API.reportUrl("/reports/no-show", { event_id: eventId });
    container.querySelector("#rep-top").href = API.reportUrl("/reports/top-companies", { event_id: eventId });
    container.querySelector("#rep-country").href = API.reportUrl("/reports/country-analysis", { event_id: eventId });
    container.querySelector("#rep-sector").href = API.reportUrl("/reports/sector-analysis", { event_id: eventId });

    const updateDailyLink = () => {
      const date = container.querySelector("#rep-daily-date").value;
      container.querySelector("#rep-daily").href =
        API.reportUrl("/reports/daily-schedule-pdf", { event_id: eventId, meeting_date: date });
    };
    updateDailyLink();
    container.querySelector("#rep-daily-date").addEventListener("change", updateDailyLink);
  },

  async refresh(container, state) {
    this.wireLinks(container, state);
  },
};
