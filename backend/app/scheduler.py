"""
Toplantı hatırlatma zamanlayıcısı. Uygulama açıkken her 5 dakikada bir
kontrol eder: 24 saat / 1 saat kalan toplantılar için hatırlatma maili
gönderir (her toplantı için sadece bir kez).

Not: Bu zamanlayıcı yalnızca backend süreci çalışırken işler. Uygulama
kapalıyken hatırlatma gönderilmez — bu nedenle fuar günlerinde backend'in
(masaüstü uygulamasıyla birlikte) açık bırakılması gerekir.
"""
import datetime
import logging
from apscheduler.schedulers.background import BackgroundScheduler

from .database import SessionLocal
from . import models, email_service

logger = logging.getLogger("scheduler")


def check_reminders():
    db = SessionLocal()
    try:
        now = datetime.datetime.now()
        meetings = db.query(models.Meeting).filter(models.Meeting.status == "Planlandı").all()
        for meeting in meetings:
            try:
                start_h, start_m = map(int, meeting.start_time.split(":"))
            except Exception:
                continue
            meeting_dt = datetime.datetime.combine(meeting.meeting_date, datetime.time(start_h, start_m))
            delta_hours = (meeting_dt - now).total_seconds() / 3600.0

            match = db.query(models.Match).get(meeting.match_id)
            if not match:
                continue
            buyer = db.query(models.Buyer).get(match.buyer_id)
            participant = db.query(models.Participant).get(match.participant_id)

            if not meeting.reminder_24h_sent and 0 < delta_hours <= 24:
                _send_reminder(db, meeting, buyer, participant, 24)
                meeting.reminder_24h_sent = True
                db.commit()

            if not meeting.reminder_1h_sent and 0 < delta_hours <= 1:
                _send_reminder(db, meeting, buyer, participant, 1)
                meeting.reminder_1h_sent = True
                db.commit()
    except Exception as e:
        logger.error(f"Hatırlatma taraması hatası: {e}")
    finally:
        db.close()


def _send_reminder(db, meeting, buyer, participant, hours_before):
    if buyer and buyer.contact_email:
        subject, body = email_service.build_reminder_email(
            buyer.contact_name or buyer.company_name, participant.company_name, meeting, hours_before)
        ok, err = email_service.send_email(db, buyer.contact_email, subject, body)
        db.add(models.EmailLog(
            match_id=meeting.match_id, meeting_id=meeting.id, recipient_type="buyer",
            recipient_email=buyer.contact_email, subject=subject,
            status="sent" if ok else "failed", error=err))
    if participant and participant.contact_email:
        subject, body = email_service.build_reminder_email(
            participant.contact_name or participant.company_name, buyer.company_name, meeting, hours_before)
        ok, err = email_service.send_email(db, participant.contact_email, subject, body)
        db.add(models.EmailLog(
            match_id=meeting.match_id, meeting_id=meeting.id, recipient_type="participant",
            recipient_email=participant.contact_email, subject=subject,
            status="sent" if ok else "failed", error=err))
    db.commit()


def start_scheduler():
    scheduler = BackgroundScheduler()
    scheduler.add_job(check_reminders, "interval", minutes=5, id="reminder_check")
    scheduler.start()
    return scheduler
