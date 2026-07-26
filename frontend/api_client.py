"""Backend (FastAPI) ile HTTP üzerinden iletişim kuran ince istemci katmanı."""
import os
import requests

# Varsayılan: aynı bilgisayarda çalışan backend. Backend başka bir bilgisayarda
# çalışıyorsa (ör. ofis ağı üzerinden), FOODIST_BACKEND_URL çevre değişkenini
# ayarlayın, örn: set FOODIST_BACKEND_URL=http://192.168.1.25:8000
BASE_URL = os.environ.get("FOODIST_BACKEND_URL", "http://127.0.0.1:8000")


class ApiError(Exception):
    def __init__(self, message):
        super().__init__(message)
        self.message = message


def _handle(resp):
    if resp.status_code >= 400:
        try:
            detail = resp.json().get("detail", resp.text)
        except Exception:
            detail = resp.text
        raise ApiError(str(detail))
    if resp.headers.get("content-type", "").startswith("application/json"):
        return resp.json()
    return resp


class ApiClient:
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.role = None  # giriş sonrası set edilir; admin-only uç noktalar için gerekli

    def _headers(self, extra=None):
        headers = dict(extra or {})
        if self.role:
            headers["X-User-Role"] = self.role
        return headers

    # ---- Auth ----
    def login(self, username, password):
        r = requests.post(f"{self.base_url}/auth/login", json={"username": username, "password": password}, timeout=10)
        user = _handle(r)
        self.role = user.get("role")
        return user

    # ---- Events ----
    def list_events(self):
        return _handle(requests.get(f"{self.base_url}/events", headers=self._headers(), timeout=10))

    def create_event(self, name, start_date=None, end_date=None, venue=None):
        payload = {"name": name, "start_date": start_date, "end_date": end_date, "venue": venue}
        return _handle(requests.post(f"{self.base_url}/events", json=payload, headers=self._headers(), timeout=10))

    # ---- Buyers ----
    def list_buyers(self, event_id):
        return _handle(requests.get(f"{self.base_url}/buyers", params={"event_id": event_id}, headers=self._headers(), timeout=10))

    def create_buyer(self, payload):
        return _handle(requests.post(f"{self.base_url}/buyers", json=payload, headers=self._headers(), timeout=10))

    def update_buyer(self, buyer_id, payload):
        return _handle(requests.put(f"{self.base_url}/buyers/{buyer_id}", json=payload, headers=self._headers(), timeout=10))

    def delete_buyer(self, buyer_id):
        return _handle(requests.delete(f"{self.base_url}/buyers/{buyer_id}", headers=self._headers(), timeout=10))

    def buyer_history(self, buyer_id):
        return _handle(requests.get(f"{self.base_url}/buyers/{buyer_id}/history", headers=self._headers(), timeout=10))

    # ---- Participants ----
    def list_participants(self, event_id):
        return _handle(requests.get(f"{self.base_url}/participants", params={"event_id": event_id}, headers=self._headers(), timeout=10))

    def create_participant(self, payload):
        return _handle(requests.post(f"{self.base_url}/participants", json=payload, headers=self._headers(), timeout=10))

    def update_participant(self, participant_id, payload):
        return _handle(requests.put(f"{self.base_url}/participants/{participant_id}", json=payload, headers=self._headers(), timeout=10))

    def delete_participant(self, participant_id):
        return _handle(requests.delete(f"{self.base_url}/participants/{participant_id}", headers=self._headers(), timeout=10))

    # ---- Import ----
    def import_fields(self, entity_type):
        return _handle(requests.get(f"{self.base_url}/import/fields/{entity_type}", headers=self._headers(), timeout=10))

    def upload_file(self, file_path):
        with open(file_path, "rb") as f:
            files = {"file": (file_path.split("/")[-1].split("\\")[-1], f)}
            return _handle(requests.post(f"{self.base_url}/import/upload", files=files, headers=self._headers(), timeout=30))

    def commit_import(self, event_id, entity_type, file_token, mapping):
        payload = {"event_id": event_id, "entity_type": entity_type, "file_token": file_token, "mapping": mapping}
        return _handle(requests.post(f"{self.base_url}/import/commit", json=payload, headers=self._headers(), timeout=30))

    # ---- Matching ----
    def generate_matches(self, payload):
        return _handle(requests.post(f"{self.base_url}/matches/generate", json=payload, headers=self._headers(), timeout=60))

    def list_matches(self, event_id, status=None):
        params = {"event_id": event_id}
        if status:
            params["status"] = status
        return _handle(requests.get(f"{self.base_url}/matches", params=params, headers=self._headers(), timeout=15))

    def approve_matches(self, match_ids):
        return _handle(requests.post(f"{self.base_url}/matches/approve", json={"match_ids": match_ids}, headers=self._headers(), timeout=30))

    def update_match_status(self, match_id, status):
        return _handle(requests.put(f"{self.base_url}/matches/{match_id}/status", json={"status": status}, headers=self._headers(), timeout=10))

    # ---- Meetings ----
    def list_meetings(self, event_id, meeting_date=None):
        params = {"event_id": event_id}
        if meeting_date:
            params["meeting_date"] = meeting_date
        return _handle(requests.get(f"{self.base_url}/meetings", params=params, headers=self._headers(), timeout=15))

    def schedule_meeting(self, match_id, meeting_date, start_time, stand_no=None):
        payload = {"match_id": match_id, "meeting_date": meeting_date, "start_time": start_time, "stand_no": stand_no}
        return _handle(requests.post(f"{self.base_url}/meetings/schedule", json=payload, headers=self._headers(), timeout=15))

    def update_attendance(self, meeting_id, status):
        return _handle(requests.put(f"{self.base_url}/meetings/{meeting_id}/attendance", json={"status": status}, headers=self._headers(), timeout=10))

    def download_ics(self, meeting_id, save_path):
        r = requests.get(f"{self.base_url}/meetings/{meeting_id}/ics", headers=self._headers(), timeout=15)
        with open(save_path, "wb") as f:
            f.write(r.content)
        return save_path

    # ---- Dashboard ----
    def get_dashboard(self, event_id):
        return _handle(requests.get(f"{self.base_url}/dashboard/{event_id}", headers=self._headers(), timeout=15))

    # ---- Settings ----
    def get_settings(self):
        return _handle(requests.get(f"{self.base_url}/settings", headers=self._headers(), timeout=10))

    def update_settings(self, payload):
        return _handle(requests.put(f"{self.base_url}/settings", json=payload, headers=self._headers(), timeout=10))

    # ---- Reports ----
    def download_report(self, endpoint, params, save_path):
        r = requests.get(f"{self.base_url}{endpoint}", params=params, headers=self._headers(), timeout=30)
        if r.status_code >= 400:
            raise ApiError(r.text)
        with open(save_path, "wb") as f:
            f.write(r.content)
        return save_path
