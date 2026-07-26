"""
Foodist Hosted Buyer CRM — Tek Program Başlatıcı.

Bu dosya, backend (FastAPI/uvicorn) sürecini arka planda bir thread
içinde başlatır, hazır olmasını bekler, ardından PySide6 arayüzünü açar.
Kullanıcı iki ayrı program açtığını hiç fark etmez — tek pencere görür.

Çalıştırma: python app_launcher.py
"""
import os
import sys
import time
import threading
import urllib.request
import urllib.error

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.join(THIS_DIR, "backend")
FRONTEND_DIR = os.path.join(THIS_DIR, "frontend")

for path in (BACKEND_DIR, FRONTEND_DIR):
    if path not in sys.path:
        sys.path.insert(0, path)

BACKEND_HOST = "127.0.0.1"
BACKEND_PORT = 8000


def _start_backend():
    import uvicorn
    from app.main import app as backend_app

    uvicorn.run(backend_app, host=BACKEND_HOST, port=BACKEND_PORT, log_level="warning")


def _wait_for_backend(timeout_seconds: float = 20.0) -> bool:
    url = f"http://{BACKEND_HOST}:{BACKEND_PORT}/api/health"
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        try:
            urllib.request.urlopen(url, timeout=1)
            return True
        except (urllib.error.URLError, ConnectionError, OSError):
            time.sleep(0.3)
    return False


def main():
    backend_thread = threading.Thread(target=_start_backend, daemon=True)
    backend_thread.start()

    if not _wait_for_backend():
        print("UYARI: Backend zamanında yanıt vermedi, yine de arayüz açılıyor.")

    os.environ.setdefault("FOODIST_BACKEND_URL", f"http://{BACKEND_HOST}:{BACKEND_PORT}")

    import main as frontend_entry
    frontend_entry.main()


if __name__ == "__main__":
    main()
