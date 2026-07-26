import API from "../api.js";

export default {
  key: "dashboard",
  label: "📊 Dashboard",
  adminOnly: false,

  async render(container, state) {
    container.innerHTML = `
      <div class="page-title">Dashboard</div>
      <div class="page-hint">Etkinliğin genel durumu.</div>
      <div class="dashboard-grid" id="dash-grid"></div>
    `;
    await this.refresh(container, state);
  },

  async refresh(container, state) {
    const grid = container.querySelector("#dash-grid");
    if (!grid) return;
    if (!state.eventId) {
      grid.innerHTML = `<div class="empty-state">Önce bir etkinlik seçin.</div>`;
      return;
    }
    let data;
    try {
      data = await API.getDashboard(state.eventId);
    } catch (e) {
      grid.innerHTML = `<div class="empty-state">Veri alınamadı: ${e.message}</div>`;
      return;
    }

    const metrics = [
      ["Toplam Buyer", data.total_buyers],
      ["Toplam Katılımcı", data.total_participants],
      ["Toplam Eşleşme", data.total_matches],
      ["Onay Bekleyen", data.pending_approval],
      ["Onaylanan", data.approved],
      ["Planlanan Toplantı", data.scheduled_meetings],
      ["Tamamlanan Toplantı", data.completed_meetings],
      ["No-Show Oranı", data.no_show_rate + "%"],
    ];

    grid.innerHTML = metrics.map(([label, value]) => `
      <div class="metric-card">
        <div class="value">${value}</div>
        <div class="label">${label}</div>
      </div>
    `).join("");
  },
};
