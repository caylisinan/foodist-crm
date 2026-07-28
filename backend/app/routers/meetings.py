import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from sqlalchemy.orm import Session
from typing import List, Optional

from .. import models, schemas, calendar_ics, email_service
from ..database import get_db

router = APIRouter(prefix="/meetings", tags=["meetings"])


def _add_minutes(hhmm: str, minutes: int) -> str:
    h, m = map(int, hhmm.split(":"))
    total = h * 60 + m + minutes
    return f"{(total // 60) % 24:02d}:{total % 60:02d}"


@router.get("", response_model=List[schemas.MeetingOut])
def list_meetings(event_id: int = Query(...), meeting_date: Optional[str] = Query(None), db: Session = Depends(get_db)):
    q = db.query(models.Meeting).filter(models.Meeting.event_id == event_id)
    if meeting_date:
        q = q.filter(models.Meeting.meeting_date == meeting_date)
    meetings = q.order_by(models.Meeting.meeting_date, models.Meeting.start_time).all()

    out = []
    for meeting in meetings:
        match = db.query(models.Match).get(meeting.match_id)
        buyer = db.query(models.Buyer).get(match.buyer_id) if match else None
        participant = db.query(models.Participant).get(match.participant_id) if match else None
        out.append(schemas.MeetingOut(
            id=meeting.id, match_id=meeting.match_id, event_id=meeting.event_id,
            meeting_date=meeting.meeting_date, start_time=meeting.start_time,
            end_time=meeting.end_time, stand_no=meeting.stand_no, status=meeting.status,
            buyer_name=buyer.company_name if buyer else None,
            participant_name=participant.company_name if participant else None,
        ))
    return out


@router.post("/schedule")
def schedule_meeting(payload: schemas.MeetingCreate, db: Session = Depends(get_db)):
    match = db.query(models.Match).get(payload.match_id)
    if not match:
        raise HTTPException(404, "Eşleşme bulunamadı")
    if match.status not in ("Karşılıklı Onaylandı", "Toplantı Planlandı"):
        raise HTTPException(400, "Toplantı sadece 'Karşılıklı Onaylandı' durumundaki eşleşmeler için planlanabilir.")

    buyer = db.query(models.Buyer).get(match.buyer_id)
    participant = db.query(models.Participant).get(match.participant_id)

    end_time = _add_minutes(payload.start_time, 15)

    # --- Çakışma kontrolleri ---
    same_day_meetings = db.query(models.Meeting).filter(
        models.Meeting.event_id == match.event_id,
        models.Meeting.meeting_date == payload.meeting_date,
        models.Meeting.status != "Katılmadı",
    ).all()

    buyer_meeting_count = 0
    buyer_minutes_used = 0
    for m in same_day_meetings:
        other_match = db.query(models.Match).get(m.match_id)
        if not other_match:
            continue
        overlap = not (end_time <= m.start_time or payload.start_time >= m.end_time)
        if other_match.buyer_id == match.buyer_id:
            buyer_meeting_count += 1
            buyer_minutes_used += 15
            if overlap:
                raise HTTPException(400, f"Buyer'ın bu saatte ({m.start_time}-{m.end_time}) zaten bir toplantısı var.")
        if other_match.participant_id == match.participant_id and overlap:
            raise HTTPException(400, f"Katılımcının bu saatte ({m.start_time}-{m.end_time}) zaten bir toplantısı var.")

    max_meetings = buyer.max_meetings or 4
    max_minutes = buyer.max_minutes or 60
    if buyer_meeting_count + 1 > max_meetings:
        raise HTTPException(400, f"Buyer için günlük maksimum toplantı sayısı ({max_meetings}) aşılıyor.")
    if buyer_minutes_used + 15 > max_minutes:
        raise HTTPException(400, f"Buyer için günlük maksimum dakika limiti ({max_minutes} dk) aşılıyor.")

    existing_meeting = db.query(models.Meeting).filter(models.Meeting.match_id == match.id).first()
    if existing_meeting:
        existing_meeting.meeting_date = payload.meeting_date
        existing_meeting.start_time = payload.start_time
        existing_meeting.end_time = end_time
        existing_meeting.stand_no = payload.stand_no or (participant.stand_no if participant else None)
        existing_meeting.reminder_24h_sent = False
        existing_meeting.reminder_1h_sent = False
        meeting = existing_meeting
    else:
        meeting = models.Meeting(
            match_id=match.id, event_id=match.event_id,
            meeting_date=payload.meeting_date, start_time=payload.start_time, end_time=end_time,
            stand_no=payload.stand_no or (participant.stand_no if participant else None),
            status="Planlandı",
        )
        db.add(meeting)

    match.status = "Toplantı Planlandı"
    db.commit()
    db.refresh(meeting)

    mail_result = {"buyer_mail_sent": None, "participant_mail_sent": None}

    # Bilgilendirme maili (tarih/saat/stand no) — sadece send_email=True ise gönderilir
    if payload.send_email:
        if buyer and buyer.contact_email:
            subject, body = email_service.build_meeting_confirmation_email(
                buyer.contact_name or buyer.company_name, participant.company_name, meeting, meeting.stand_no)
            ok, err = email_service.send_email(db, buyer.contact_email, subject, body)
            db.add(models.EmailLog(match_id=match.id, meeting_id=meeting.id, recipient_type="buyer",
                                    recipient_email=buyer.contact_email, subject=subject,
                                    status="sent" if ok else "failed", error=err))
            mail_result["buyer_mail_sent"] = ok
        if participant and participant.contact_email:
            subject, body = email_service.build_meeting_confirmation_email(
                participant.contact_name or participant.company_name, buyer.company_name, meeting, meeting.stand_no)
            ok, err = email_service.send_email(db, participant.contact_email, subject, body)
            db.add(models.EmailLog(match_id=match.id, meeting_id=meeting.id, recipient_type="participant",
                                    recipient_email=participant.contact_email, subject=subject,
                                    status="sent" if ok else "failed", error=err))
            mail_result["participant_mail_sent"] = ok
        db.commit()

    return {"ok": True, "meeting_id": meeting.id, **mail_result}


@router.put("/{meeting_id}/attendance")
def update_attendance(meeting_id: int, payload: schemas.AttendanceUpdate, db: Session = Depends(get_db)):
    meeting = db.query(models.Meeting).get(meeting_id)
    if not meeting:
        raise HTTPException(404, "Toplantı bulunamadı")
    meeting.status = payload.status
    match = db.query(models.Match).get(meeting.match_id)
    if match:
        match.status = "Tamamlandı" if payload.status == "Tamamlandı" else "No Show"
    db.commit()
    return {"ok": True}


@router.get("/{meeting_id}/ics")
def download_ics(meeting_id: int, db: Session = Depends(get_db)):
    meeting = db.query(models.Meeting).get(meeting_id)
    if not meeting:
        raise HTTPException(404, "Toplantı bulunamadı")
    match = db.query(models.Match).get(meeting.match_id)
    buyer = db.query(models.Buyer).get(match.buyer_id)
    participant = db.query(models.Participant).get(match.participant_id)

    ics_content = calendar_ics.build_ics(
        summary=f"B2B Görüşme: {buyer.company_name} - {participant.company_name}",
        description=f"Foodist İstanbul Hosted Buyer görüşmesi. Stand No: {meeting.stand_no or '-'}",
        location=f"Stand {meeting.stand_no or '-'}",
        meeting_date=meeting.meeting_date, start_time=meeting.start_time, end_time=meeting.end_time,
        uid=f"foodist-meeting-{meeting.id}@foodistexpo.com",
    )
    return Response(
        content=ics_content, media_type="text/calendar",
        headers={"Content-Disposition": f"attachment; filename=toplanti-{meeting.id}.ics"},
    )
