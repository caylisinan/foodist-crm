import API from "./api.js";
import { toast } from "./helpers.js";

import dashboardScreen from "./screens/dashboard.js";
import buyersScreen from "./screens/buyers.js";
import participantsScreen from "./screens/participants.js";
import importScreen from "./screens/import.js";
import matchingScreen from "./screens/matching.js";
import calendarScreen from "./screens/calendar.js";
import reportsScreen from "./screens/reports.js";
import settingsScreen from "./screens/settings.js";

const SCREENS = [
  dashboardScreen, buyersScreen, participantsScreen, importScreen,
  matchingScreen, calendarScreen, reportsScreen, settingsScreen,
];

const state = {
  user: null,       // { username, full_name, role }
  eventId: null,
  activeScreen: null,
};

const screenContainers = {}; // key -> DOM element

function visibleScreens() {
  if (!state.user) return [];
  return SCREENS.filter(s => !s.adminOnly || state.user.role === "admin");
}

// ---------------- Giriş ----------------

function initLogin() {
  const form = document.getElementById("login-form");
  const errorBox = document.getElementById("login-error");

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    errorBox.style.display = "none";
    const username = document.getElementById("login-username").value.trim();
    const password = document.getElementById("login-password").value;
    if (!username || !password) return;

    try {
      const user = await API.login(username, password);
      state.user = user;
      API.setRole(user.role);
      localStorage.setItem("foodist_user", JSON.stringify(user));
      enterApp();
    } catch (err) {
      errorBox.textContent = err.message || "Giriş başarısız.";
      errorBox.style.display = "block";
    }
  });

  // Daha önce giriş yapılmışsa (tarayıcı hatırlıyorsa) otomatik gir
  const saved = localStorage.getItem("foodist_user");
  if (saved) {
    try {
      state.user = JSON.parse(saved);
      API.setRole(state.user.role);
      enterApp();
    } catch (e) {
      localStorage.removeItem("foodist_user");
    }
  }
}

function logout() {
  localStorage.removeItem("foodist_user");
  API.setRole(null);
  state.user = null;
  state.eventId = null;
  document.getElementById("app-shell").classList.remove("active");
  document.getElementById("login-screen").style.display = "flex";
  document.getElementById("login-username").value = "";
  document.getElementById("login-password").value = "";
}

// ---------------- Uygulama Kabuğu ----------------

async function enterApp() {
  document.getElementById("login-screen").style.display = "none";
  const shell = document.getElementById("app-shell");
  shell.classList.add("active");

  document.getElementById("sidebar-role").textContent = "Rol: " + state.user.role.toUpperCase();
  document.getElementById("sidebar-username").textContent = "Kullanıcı: " + state.user.username;

  buildNav();
  await loadEvents();
  buildScreenContainers();
}

function buildNav() {
  const navList = document.getElementById("nav-list");
  navList.innerHTML = "";
  visibleScreens().forEach((screen, idx) => {
    const li = document.createElement("li");
    li.textContent = screen.label;
    li.dataset.key = screen.key;
    li.addEventListener("click", () => selectScreen(screen.key));
    navList.appendChild(li);
  });
}

function buildScreenContainers() {
  const content = document.getElementById("content");
  content.innerHTML = "";
  for (const key in screenContainers) delete screenContainers[key];

  visibleScreens().forEach(screen => {
    const div = document.createElement("div");
    div.className = "screen";
    div.id = "screen-" + screen.key;
    content.appendChild(div);
    screenContainers[screen.key] = div;
  });

  const first = visibleScreens()[0];
  if (first) selectScreen(first.key);
}

async function selectScreen(key) {
  state.activeScreen = key;
  document.querySelectorAll("#nav-list li").forEach(li => {
    li.classList.toggle("active", li.dataset.key === key);
  });
  document.querySelectorAll(".screen").forEach(div => div.classList.remove("active"));
  const container = screenContainers[key];
  if (!container) return;
  container.classList.add("active");

  const screen = SCREENS.find(s => s.key === key);
  if (!screen) return;

  if (!container.dataset.rendered) {
    await screen.render(container, state);
    container.dataset.rendered = "1";
  } else if (screen.refresh) {
    await screen.refresh(container, state);
  }
}

async function refreshActiveScreen() {
  const key = state.activeScreen;
  if (!key) return;
  const container = screenContainers[key];
  const screen = SCREENS.find(s => s.key === key);
  if (container && screen && screen.refresh) {
    await screen.refresh(container, state);
  }
}

// ---------------- Etkinlik Seçici ----------------

async function loadEvents() {
  let events;
  try {
    events = await API.listEvents();
  } catch (e) {
    toast("Etkinlikler alınamadı: " + e.message, "error");
    return;
  }

  const select = document.getElementById("event-select");
  select.innerHTML = events.map(ev => `<option value="${ev.id}">${ev.name}</option>`).join("");

  if (events.length) {
    state.eventId = events[0].id;
  } else {
    state.eventId = null;
    // İlk kurulum: hiç etkinlik yoksa kullanıcıyı nazikçe bilgilendir ve modal aç
    openNewEventModal(true);
  }
}

function initEventPicker() {
  document.getElementById("event-select").addEventListener("change", async (e) => {
    state.eventId = parseInt(e.target.value);
    await refreshActiveScreen();
  });
  document.getElementById("new-event-btn").addEventListener("click", () => openNewEventModal(false));
}

function openNewEventModal(isFirst) {
  const overlay = document.getElementById("event-modal");
  overlay.classList.add("active");
  document.getElementById("event-modal-hint").style.display = isFirst ? "block" : "none";
  document.getElementById("new-event-name").value = "";
  document.getElementById("new-event-venue").value = "";
}

function initEventModal() {
  document.getElementById("event-modal-cancel").addEventListener("click", () => {
    document.getElementById("event-modal").classList.remove("active");
  });
  document.getElementById("event-modal-save").addEventListener("click", async () => {
    const name = document.getElementById("new-event-name").value.trim();
    const venue = document.getElementById("new-event-venue").value.trim();
    if (!name) { toast("Etkinlik adı zorunludur.", "error"); return; }
    try {
      await API.createEvent({ name, venue: venue || null });
    } catch (e) {
      toast("Oluşturulamadı: " + e.message, "error");
      return;
    }
    document.getElementById("event-modal").classList.remove("active");
    await loadEvents();
    buildScreenContainers();
  });
}

// ---------------- Başlat ----------------

document.getElementById("logout-btn").addEventListener("click", logout);
initLogin();
initEventPicker();
initEventModal();
