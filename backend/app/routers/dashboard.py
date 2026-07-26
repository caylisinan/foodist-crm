from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from .. import models
from ..database import get_db

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/{event_id}")
def get_dashboard(event_id: int, db: Session = Depends(get_db)):
    total_buyers = db.query(models.Buyer).filter(models.Buyer.event_id == event_id).count()
    total_participants = db.query(models.Participant).filter(models.Participant.event_id == event_id).count()
    matches = db.query(models.Match).filter(models.Match.event_id == event_id).all()

    total_matches = len(matches)
    pending = sum(1 for m in matches if m.status == "Onay Bekliyor")
    approved = sum(1 for m in matches if m.status in
                   ("Karşılıklı Onaylandı", "Toplantı Planlandı", "Tamamlandı"))
    scheduled = sum(1 for m in matches if m.status in ("Toplantı Planlandı", "Tamamlandı", "No Show"))
    completed = sum(1 for m in matches if m.status == "Tamamlandı")
    no_show = sum(1 for m in matches if m.status == "No Show")

    no_show_rate = round((no_show / scheduled) * 100, 1) if scheduled else 0.0

    return {
        "total_buyers": total_buyers,
        "total_participants": total_participants,
        "total_matches": total_matches,
        "pending_approval": pending,
        "approved": approved,
        "scheduled_meetings": scheduled,
        "completed_meetings": completed,
        "no_show_count": no_show,
        "no_show_rate": no_show_rate,
    }
