from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
import json

from .. import models, schemas, excel_import
from ..database import get_db
from ..deps import require_admin

router = APIRouter(prefix="/import", tags=["import"], dependencies=[Depends(require_admin)])


@router.get("/fields/{entity_type}")
def get_target_fields(entity_type: str):
    if entity_type not in excel_import.TARGET_FIELDS:
        raise HTTPException(400, "entity_type 'buyer' veya 'participant' olmalı")
    fields = excel_import.TARGET_FIELDS[entity_type]
    return [{"field": f, "label": excel_import.TARGET_FIELD_LABELS.get(f, f)} for f in fields]


@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    content = await file.read()
    token, path = excel_import.save_uploaded_file(content, file.filename)
    preview = excel_import.preview_excel(token)
    return {"file_token": token, **preview}


@router.get("/preview/{file_token}")
def preview(file_token: str):
    try:
        return excel_import.preview_excel(file_token)
    except FileNotFoundError as e:
        raise HTTPException(404, str(e))


@router.post("/commit")
def commit_import(payload: schemas.ImportCommitRequest, db: Session = Depends(get_db)):
    if payload.entity_type not in ("buyer", "participant"):
        raise HTTPException(400, "entity_type 'buyer' veya 'participant' olmalı")

    try:
        records = excel_import.apply_mapping(payload.file_token, payload.mapping)
    except FileNotFoundError as e:
        raise HTTPException(404, str(e))

    created = 0
    errors = []
    for i, rec in enumerate(records):
        rec = {k: v for k, v in rec.items() if v is not None}
        rec["event_id"] = payload.event_id
        try:
            if payload.entity_type == "buyer":
                if "max_meetings" in rec:
                    rec["max_meetings"] = int(rec["max_meetings"]) if str(rec["max_meetings"]).strip() else 4
                if "max_minutes" in rec:
                    rec["max_minutes"] = int(rec["max_minutes"]) if str(rec["max_minutes"]).strip() else 60
                obj = models.Buyer(**{k: v for k, v in rec.items() if k in
                    ["event_id", "company_name", "contact_name", "country", "contact_email",
                     "contact_phone", "sector", "interested_products", "max_meetings",
                     "max_minutes", "notes"]})
            else:
                obj = models.Participant(**{k: v for k, v in rec.items() if k in
                    ["event_id", "company_name", "contact_name", "country", "contact_email",
                     "contact_phone", "sector", "offered_products", "stand_no", "notes"]})
            db.add(obj)
            created += 1
        except Exception as e:
            errors.append(f"Satır {i+2}: {e}")

    db.commit()

    # Eşleştirme şablonunu hatırla
    db.add(models.ImportMapping(
        entity_type=payload.entity_type,
        name=f"{payload.entity_type}-otomatik-kayıt",
        mapping_json=json.dumps(payload.mapping, ensure_ascii=False),
    ))
    db.commit()

    return {"created": created, "total_rows": len(records), "errors": errors}


@router.get("/mappings/{entity_type}")
def get_saved_mappings(entity_type: str, db: Session = Depends(get_db)):
    rows = db.query(models.ImportMapping).filter(
        models.ImportMapping.entity_type == entity_type
    ).order_by(models.ImportMapping.id.desc()).limit(5).all()
    return [{"id": r.id, "name": r.name, "mapping": json.loads(r.mapping_json)} for r in rows]
