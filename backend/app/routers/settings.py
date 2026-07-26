from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..deps import require_admin

router = APIRouter(prefix="/settings", tags=["settings"], dependencies=[Depends(require_admin)])

DEFAULTS = {
    "smtp_host": "", "smtp_port": "587", "smtp_user": "", "smtp_pass": "",
    "smtp_from_name": "Foodist İstanbul", "smtp_from_email": "", "smtp_secure": "false",
    "weight_product": "50", "weight_sector": "30", "weight_country": "20",
    "match_threshold": "40", "default_max_meetings": "4", "default_max_minutes": "60",
    "app_base_url": "http://127.0.0.1:8000",
}


@router.get("")
def get_settings(db: Session = Depends(get_db)):
    rows = db.query(models.AppSetting).all()
    values = {r.key: r.value for r in rows}
    result = dict(DEFAULTS)
    result.update({k: v for k, v in values.items() if v is not None})
    # Şifreyi tam olarak geri döndürmek yerine maskele (arayüzde boş bırakılırsa değişmeden kalır)
    if result.get("smtp_pass"):
        result["smtp_pass"] = "••••••••"
    return result


@router.put("")
def update_settings(payload: schemas.SettingsUpdate, db: Session = Depends(get_db)):
    data = payload.model_dump(exclude_unset=True)
    for key, value in data.items():
        if key == "smtp_pass" and value == "••••••••":
            continue  # kullanıcı şifreyi değiştirmedi
        row = db.query(models.AppSetting).get(key)
        if row:
            row.value = value
        else:
            db.add(models.AppSetting(key=key, value=value))
    db.commit()
    return {"ok": True}
