from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from .. import models, schemas
from ..database import get_db
from ..deps import require_admin

router = APIRouter(prefix="/participants", tags=["participants"], dependencies=[Depends(require_admin)])


@router.get("", response_model=List[schemas.ParticipantOut])
def list_participants(event_id: Optional[int] = Query(None), db: Session = Depends(get_db)):
    q = db.query(models.Participant)
    if event_id:
        q = q.filter(models.Participant.event_id == event_id)
    return q.order_by(models.Participant.company_name).all()


@router.post("", response_model=schemas.ParticipantOut)
def create_participant(payload: schemas.ParticipantCreate, db: Session = Depends(get_db)):
    participant = models.Participant(**payload.model_dump())
    db.add(participant)
    db.commit()
    db.refresh(participant)
    return participant


@router.put("/{participant_id}", response_model=schemas.ParticipantOut)
def update_participant(participant_id: int, payload: schemas.ParticipantCreate, db: Session = Depends(get_db)):
    participant = db.query(models.Participant).get(participant_id)
    if not participant:
        raise HTTPException(404, "Katılımcı bulunamadı")
    for k, v in payload.model_dump().items():
        setattr(participant, k, v)
    db.commit()
    db.refresh(participant)
    return participant


@router.delete("/{participant_id}")
def delete_participant(participant_id: int, db: Session = Depends(get_db)):
    participant = db.query(models.Participant).get(participant_id)
    if participant:
        db.delete(participant)
        db.commit()
    return {"ok": True}
