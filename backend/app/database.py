"""
Veritabanı bağlantısı ve oturum yönetimi.

Öncelik sırası:
1. DATABASE_URL ortam değişkeni ayarlıysa (ör. ücretsiz Neon.tech Postgres
   veritabanı bağlantı adresi) → o veritabanı kullanılır. Bu, ücretsiz
   bulut barındırmada (Render Free) kalıcı disk olmadan bile verilerin
   silinmemesini sağlar.
2. FOODIST_DATA_DIR ortam değişkeni ayarlıysa → o klasörde SQLite dosyası.
3. Derlenmiş (.exe) modda → kullanıcının AppData/home klasörü.
4. Geliştirme modunda → backend/ klasörünün yanında.
"""
import sys
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base


def _get_persistent_data_dir() -> str:
    env_dir = os.environ.get("FOODIST_DATA_DIR")
    if env_dir:
        data_dir = env_dir
    elif getattr(sys, "frozen", False):
        base = os.environ.get("APPDATA") or os.path.expanduser("~")
        data_dir = os.path.join(base, "FoodistHostedBuyerCRM")
    else:
        data_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.makedirs(data_dir, exist_ok=True)
    return data_dir


_external_db_url = os.environ.get("DATABASE_URL")

if _external_db_url:
    # Bazı barındırma servisleri "postgres://" öneki verir, SQLAlchemy 2.x
    # "postgresql://" bekler — otomatik düzeltiyoruz.
    if _external_db_url.startswith("postgres://"):
        _external_db_url = _external_db_url.replace("postgres://", "postgresql://", 1)
    DATABASE_URL = _external_db_url
    _connect_args = {}
else:
    DB_PATH = os.path.join(_get_persistent_data_dir(), "foodist_crm.db")
    DATABASE_URL = f"sqlite:///{DB_PATH}"
    _connect_args = {"check_same_thread": False}

engine = create_engine(DATABASE_URL, connect_args=_connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()



