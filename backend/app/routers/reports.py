from fastapi import APIRouter, Depends, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from collections import Counter

from .. import models, reports as report_gen
from ..database import get_db

router = APIRouter(prefix="/reports", tags=["reports"])


def _meeting_rows(db: Session, event_id: int):
    meetings = db.query(models.Meeting).filter(models.Meeting.event_id == event_id).all()
    rows = []
    for meeting in meetings:
        match = db.query(models.Match).get(meeting.match_id)
        buyer = db.query(models.Buyer).get(match.buyer_id) if match else None
        participant = db.query(models.Participant).get(match.participant_id) if match else None
        rows.append({
            "buyer": buyer.company_name if buyer else "",
            "buyer_country": buyer.country if buyer else "",
            "participant": participant.company_name if participant else "",
            "participant_country": participant.country if participant else "",
            "date": str(meeting.meeting_date),
            "start_time": meeting.start_time,
            "end_time": meeting.end_time,
            "stand_no": meeting.stand_no or "",
            "status": meeting.status,
        })
    return rows


@router.get("/buyer-calendar")
def buyer_calendar_excel(event_id: int = Query(...), db: Session = Depends(get_db)):
    rows = _meeting_rows(db, event_id)
    headers = ["buyer", "date", "start_time", "end_time", "participant", "stand_no", "status"]
    labels = ["Buyer", "Tarih", "Başlangıç", "Bitiş", "Katılımcı Firma", "Stand No", "Durum"]
    path = report_gen.export_rows_to_excel(rows, headers, labels, f"buyer_takvimi_{event_id}")
    return FileResponse(path, filename="buyer_takvimi.xlsx")


@router.get("/participant-calendar")
def participant_calendar_excel(event_id: int = Query(...), db: Session = Depends(get_db)):
    rows = _meeting_rows(db, event_id)
    headers = ["participant", "date", "start_time", "end_time", "buyer", "stand_no", "status"]
    labels = ["Katılımcı Firma", "Tarih", "Başlangıç", "Bitiş", "Buyer", "Stand No", "Durum"]
    path = report_gen.export_rows_to_excel(rows, headers, labels, f"firma_takvimi_{event_id}")
    return FileResponse(path, filename="firma_takvimi.xlsx")


@router.get("/daily-schedule-pdf")
def daily_schedule_pdf(event_id: int = Query(...), meeting_date: str = Query(...), db: Session = Depends(get_db)):
    rows = _meeting_rows(db, event_id)
    rows = [r for r in rows if r["date"] == meeting_date]
    table_rows = [[r["start_time"], r["buyer"], r["participant"], r["stand_no"], r["status"]] for r in rows]
    path = report_gen.export_rows_to_pdf(
        f"Günlük Toplantı Programı — {meeting_date}",
        table_rows, ["Saat", "Buyer", "Katılımcı", "Stand No", "Durum"],
        f"gunluk_program_{event_id}_{meeting_date}",
    )
    return FileResponse(path, filename=f"gunluk_program_{meeting_date}.pdf")


@router.get("/no-show")
def no_show_report_excel(event_id: int = Query(...), db: Session = Depends(get_db)):
    rows = _meeting_rows(db, event_id)
    rows = [r for r in rows if r["status"] == "Katılmadı"]
    headers = ["buyer", "participant", "date", "start_time", "stand_no"]
    labels = ["Buyer", "Katılımcı Firma", "Tarih", "Saat", "Stand No"]
    path = report_gen.export_rows_to_excel(rows, headers, labels, f"no_show_{event_id}")
    return FileResponse(path, filename="no_show_raporu.xlsx")


@router.get("/top-companies")
def top_companies_excel(event_id: int = Query(...), db: Session = Depends(get_db)):
    rows = _meeting_rows(db, event_id)
    counter = Counter(r["participant"] for r in rows if r["participant"])
    ranked = [{"company": c, "meeting_count": n} for c, n in counter.most_common()]
    path = report_gen.export_rows_to_excel(
        ranked, ["company", "meeting_count"], ["Firma", "Toplantı Sayısı"],
        f"en_cok_gorusme_{event_id}")
    return FileResponse(path, filename="en_cok_gorusme_alan_firmalar.xlsx")


@router.get("/country-analysis")
def country_analysis_excel(event_id: int = Query(...), db: Session = Depends(get_db)):
    rows = _meeting_rows(db, event_id)
    counter = Counter(r["buyer_country"] for r in rows if r["buyer_country"])
    ranked = [{"country": c, "meeting_count": n} for c, n in counter.most_common()]
    path = report_gen.export_rows_to_excel(
        ranked, ["country", "meeting_count"], ["Ülke", "Toplantı Sayısı"],
        f"ulke_analiz_{event_id}")
    return FileResponse(path, filename="ulke_bazli_analiz.xlsx")


@router.get("/sector-analysis")
def sector_analysis_excel(event_id: int = Query(...), db: Session = Depends(get_db)):
    buyers = {b.id: b.sector for b in db.query(models.Buyer).filter(models.Buyer.event_id == event_id).all()}
    matches = db.query(models.Match).filter(models.Match.event_id == event_id).all()
    counter = Counter(buyers.get(m.buyer_id) for m in matches if buyers.get(m.buyer_id))
    ranked = [{"sector": s, "match_count": n} for s, n in counter.most_common()]
    path = report_gen.export_rows_to_excel(
        ranked, ["sector", "match_count"], ["Sektör", "Eşleşme Sayısı"],
        f"sektor_analiz_{event_id}")
    return FileResponse(path, filename="sektor_bazli_analiz.xlsx")
