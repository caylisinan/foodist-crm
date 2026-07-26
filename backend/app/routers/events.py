from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from .. import models, schemas
from ..database import get_db

router = APIRouter(prefix="/events", tags=["events"])


@router.get("", response_model=List[schemas.EventOut])
def list_events(db: Session = Depends(get_db)):
    return db.query(models.Event).order_by(models.Event.id.desc()).all()


@router.post("", response_model=schemas.EventOut)
def create_event(payload: schemas.EventCreate, db: Session = Depends(get_db)):
    event = models.Event(**payload.model_dump())
    db.add(event)
    db.commit()
    db.refresh(event)
    return event


@router.delete("/{event_id}")
def delete_event(event_id: int, db: Session = Depends(get_db)):
    event = db.query(models.Event).get(event_id)
    if event:
        db.delete(event)
        db.commit()
    return {"ok": True}
