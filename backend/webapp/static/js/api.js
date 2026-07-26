// Backend ile iletişim katmanı. Sayfa hangi adresten açıldıysa (ör.
// http://192.168.1.25:8000), fetch çağrıları otomatik olarak AYNI adrese
// gider — bu yüzden hiçbir yapılandırma gerekmez.
//
// X-User-Role header'ı, admin-only uç noktaların sadece arayüzde değil
// backend'de de korunmasını sağlar (bkz. backend/app/deps.py).

let currentRole = null;

function authHeaders(extra = {}) {
  const headers = { ...extra };
  if (currentRole) headers["X-User-Role"] = currentRole;
  return headers;
}

const API = {
  setRole(role) {
    currentRole = role;
  },

  async _handle(res) {
    if (!res.ok) {
      let detail = res.statusText;
      try {
        const data = await res.json();
        detail = data.detail || JSON.stringify(data);
      } catch (e) { /* body json değilse statusText kalsın */ }
      throw new Error(detail);
    }
    const contentType = res.headers.get("content-type") || "";
    if (contentType.includes("application/json")) {
      return res.json();
    }
    return res;
  },

  async login(username, password) {
    const res = await fetch("/auth/login", {
      method: "POST", headers: authHeaders({ "Content-Type": "application/json" }),
      body: JSON.stringify({ username, password }),
    });
    return this._handle(res);
  },

  async createUser(payload) {
    const res = await fetch("/auth/users", {
      method: "POST", headers: authHeaders({ "Content-Type": "application/json" }),
      body: JSON.stringify(payload),
    });
    return this._handle(res);
  },

  // ---- Events ----
  async listEvents() {
    return this._handle(await fetch("/events"));
  },
  async createEvent(payload) {
    const res = await fetch("/events", {
      method: "POST", headers: authHeaders({ "Content-Type": "application/json" }),
      body: JSON.stringify(payload),
    });
    return this._handle(res);
  },

  // ---- Buyers ----
  async listBuyers(eventId) {
    return this._handle(await fetch(`/buyers?event_id=${eventId}`, { headers: authHeaders() }));
  },
  async createBuyer(payload) {
    const res = await fetch("/buyers", {
      method: "POST", headers: authHeaders({ "Content-Type": "application/json" }),
      body: JSON.stringify(payload),
    });
    return this._handle(res);
  },
  async updateBuyer(id, payload) {
    const res = await fetch(`/buyers/${id}`, {
      method: "PUT", headers: authHeaders({ "Content-Type": "application/json" }),
      body: JSON.stringify(payload),
    });
    return this._handle(res);
  },
  async deleteBuyer(id) {
    return this._handle(await fetch(`/buyers/${id}`, { method: "DELETE", headers: authHeaders() }));
  },
  async buyerHistory(id) {
    return this._handle(await fetch(`/buyers/${id}/history`, { headers: authHeaders() }));
  },

  // ---- Participants ----
  async listParticipants(eventId) {
    return this._handle(await fetch(`/participants?event_id=${eventId}`, { headers: authHeaders() }));
  },
  async createParticipant(payload) {
    const res = await fetch("/participants", {
      method: "POST", headers: authHeaders({ "Content-Type": "application/json" }),
      body: JSON.stringify(payload),
    });
    return this._handle(res);
  },
  async updateParticipant(id, payload) {
    const res = await fetch(`/participants/${id}`, {
      method: "PUT", headers: authHeaders({ "Content-Type": "application/json" }),
      body: JSON.stringify(payload),
    });
    return this._handle(res);
  },
  async deleteParticipant(id) {
    return this._handle(await fetch(`/participants/${id}`, { method: "DELETE", headers: authHeaders() }));
  },

  // ---- Import ----
  async importFields(entityType) {
    return this._handle(await fetch(`/import/fields/${entityType}`, { headers: authHeaders() }));
  },
  async uploadFile(file) {
    const formData = new FormData();
    formData.append("file", file);
    const res = await fetch("/import/upload", { method: "POST", headers: authHeaders(), body: formData });
    return this._handle(res);
  },
  async commitImport(payload) {
    const res = await fetch("/import/commit", {
      method: "POST", headers: authHeaders({ "Content-Type": "application/json" }),
      body: JSON.stringify(payload),
    });
    return this._handle(res);
  },

  // ---- Matching ----
  async generateMatches(payload) {
    const res = await fetch("/matches/generate", {
      method: "POST", headers: authHeaders({ "Content-Type": "application/json" }),
      body: JSON.stringify(payload),
    });
    return this._handle(res);
  },
  async listMatches(eventId, status) {
    let url = `/matches?event_id=${eventId}`;
    if (status && status !== "Tümü") url += `&status=${encodeURIComponent(status)}`;
    return this._handle(await fetch(url, { headers: authHeaders() }));
  },
  async approveMatches(matchIds) {
    const res = await fetch("/matches/approve", {
      method: "POST", headers: authHeaders({ "Content-Type": "application/json" }),
      body: JSON.stringify({ match_ids: matchIds }),
    });
    return this._handle(res);
  },
  async updateMatchStatus(id, status) {
    const res = await fetch(`/matches/${id}/status`, {
      method: "PUT", headers: authHeaders({ "Content-Type": "application/json" }),
      body: JSON.stringify({ status }),
    });
    return this._handle(res);
  },

  // ---- Meetings ----
  async listMeetings(eventId, meetingDate) {
    let url = `/meetings?event_id=${eventId}`;
    if (meetingDate) url += `&meeting_date=${meetingDate}`;
    return this._handle(await fetch(url, { headers: authHeaders() }));
  },
  async scheduleMeeting(payload) {
    const res = await fetch("/meetings/schedule", {
      method: "POST", headers: authHeaders({ "Content-Type": "application/json" }),
      body: JSON.stringify(payload),
    });
    return this._handle(res);
  },
  async updateAttendance(id, status) {
    const res = await fetch(`/meetings/${id}/attendance`, {
      method: "PUT", headers: authHeaders({ "Content-Type": "application/json" }),
      body: JSON.stringify({ status }),
    });
    return this._handle(res);
  },
  icsDownloadUrl(id) {
    return `/meetings/${id}/ics`;
  },

  // ---- Dashboard ----
  async getDashboard(eventId) {
    return this._handle(await fetch(`/dashboard/${eventId}`));
  },

  // ---- Settings ----
  async getSettings() {
    return this._handle(await fetch("/settings", { headers: authHeaders() }));
  },
  async updateSettings(payload) {
    const res = await fetch("/settings", {
      method: "PUT", headers: authHeaders({ "Content-Type": "application/json" }),
      body: JSON.stringify(payload),
    });
    return this._handle(res);
  },

  // ---- Reports ----
  reportUrl(endpoint, params) {
    const query = new URLSearchParams(params).toString();
    return `${endpoint}?${query}`;
  },
};

export default API;
