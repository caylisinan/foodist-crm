from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from .. import models, schemas
from ..database import get_db
from ..deps import require_admin

router = APIRouter(prefix="/buyers", tags=["buyers"], dependencies=[Depends(require_admin)])


@router.get("", response_model=List[schemas.BuyerOut])
def list_buyers(event_id: Optional[int] = Query(None), db: Session = Depends(get_db)):
    q = db.query(models.Buyer)
    if event_id:
        q = q.filter(models.Buyer.event_id == event_id)
    return q.order_by(models.Buyer.company_name).all()


@router.post("", response_model=schemas.BuyerOut)
def create_buyer(payload: schemas.BuyerCreate, db: Session = Depends(get_db)):
    buyer = models.Buyer(**payload.model_dump())
    db.add(buyer)
    db.commit()
    db.refresh(buyer)
    return buyer


@router.put("/{buyer_id}", response_model=schemas.BuyerOut)
def update_buyer(buyer_id: int, payload: schemas.BuyerCreate, db: Session = Depends(get_db)):
    buyer = db.query(models.Buyer).get(buyer_id)
    if not buyer:
        raise HTTPException(404, "Buyer bulunamadı")
    for k, v in payload.model_dump().items():
        setattr(buyer, k, v)
    db.commit()
    db.refresh(buyer)
    return buyer


@router.delete("/{buyer_id}")
def delete_buyer(buyer_id: int, db: Session = Depends(get_db)):
    buyer = db.query(models.Buyer).get(buyer_id)
    if buyer:
        db.delete(buyer)
        db.commit()
    return {"ok": True}


@router.get("/{buyer_id}/history")
def buyer_history(buyer_id: int, db: Session = Depends(get_db)):
    """CRM geçmişi: bu buyer'ın (aynı isimdeki) tüm etkinliklerdeki
    katılımları, görüştüğü firmalar, no-show geçmişi, toplam toplantı sayısı."""
    buyer = db.query(models.Buyer).get(buyer_id)
    if not buyer:
        raise HTTPException(404, "Buyer bulunamadı")

    same_name_buyers = db.query(models.Buyer).filter(
        models.Buyer.company_name == buyer.company_name).all()
    buyer_ids = [b.id for b in same_name_buyers]

    matches = db.query(models.Match).filter(models.Match.buyer_id.in_(buyer_ids)).all()
    meetings = db.query(models.Meeting).join(models.Match).filter(
        models.Match.buyer_id.in_(buyer_ids)).all()

    no_show_count = sum(1 for m in meetings if m.status == "Katılmadı")
    completed_count = sum(1 for m in meetings if m.status == "Tamamlandı")

    participant_names = []
    for m in matches:
        p = db.query(models.Participant).get(m.participant_id)
        if p:
            participant_names.append(p.company_name)

    return {
        "company_name": buyer.company_name,
        "events_participated": len(set(b.event_id for b in same_name_buyers)),
        "total_meetings": len(meetings),
        "completed_meetings": completed_count,
        "no_show_count": no_show_count,
        "met_companies": sorted(set(participant_names)),
    }
