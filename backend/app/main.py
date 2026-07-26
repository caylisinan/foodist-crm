"""
FastAPI backend giriş noktası.
Çalıştırma: uvicorn app.main:app --reload  (backend/ klasöründen)

Bu süreç hem API'yi hem de tarayıcıdan erişilen web arayüzünü
(backend/webapp/) aynı adres üzerinden sunar — ayrı bir sunucu/kurulum
gerekmez. Ağdaki herkes bu sürecin çalıştığı bilgisayarın IP'sine
(ör. http://192.168.1.25:8000) tarayıcıdan girerek aynı veriye erişir.
"""
import os
import hashlib
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse

from .database import Base, engine, SessionLocal
from . import models
from .routers import (
    events, buyers, participants, import_data, matches,
    meetings, dashboard, settings as settings_router, reports, auth,
)
from .scheduler import start_scheduler

app = FastAPI(title="Foodist İstanbul — Hosted Buyer B2B CRM")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(events.router)
app.include_router(buyers.router)
app.include_router(participants.router)
app.include_router(import_data.router)
app.include_router(matches.router)
app.include_router(meetings.router)
app.include_router(dashboard.router)
app.include_router(settings_router.router)
app.include_router(reports.router)

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WEBAPP_DIR = os.path.join(BACKEND_DIR, "webapp")

if os.path.isdir(os.path.join(WEBAPP_DIR, "static")):
    app.mount("/static", StaticFiles(directory=os.path.join(WEBAPP_DIR, "static")), name="static")


def _ensure_default_admin():
    db = SessionLocal()
    try:
        if db.query(models.User).count() == 0:
            default_password = "admin123"
            db.add(models.User(
                username="admin",
                password_hash=hashlib.sha256(default_password.encode("utf-8")).hexdigest(),
                full_name="Sistem Yöneticisi",
                role="admin",
            ))
            db.commit()
            print("İlk kurulum: varsayılan kullanıcı oluşturuldu → admin / admin123")
            print("Güvenlik için ilk girişten sonra şifreyi değiştirmeniz önerilir.")
    finally:
        db.close()


@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)
    _ensure_default_admin()
    start_scheduler()


@app.get("/api/health")
def health_check():
    return {"status": "ok", "service": "Foodist Hosted Buyer CRM Backend"}


@app.get("/", response_class=HTMLResponse)
def serve_web_app():
    index_path = os.path.join(WEBAPP_DIR, "index.html")
    if not os.path.isfile(index_path):
        return HTMLResponse(
            "<h1>Web arayüzü bulunamadı</h1><p>backend/webapp/index.html eksik.</p>",
            status_code=500,
        )
    with open(index_path, encoding="utf-8") as f:
        return f.read()

