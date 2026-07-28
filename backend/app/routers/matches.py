import uuid
import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from typing import List, Optional

from .. import models, schemas, matching, email_service
from ..database import get_db
from ..deps import require_admin

router = APIRouter(tags=["matches"])


def _get_base_url(db: Session) -> str:
    setting = db.query(models.AppSetting).filter(models.AppSetting.key == "app_base_url").first()
    return (setting.value if setting and setting.value else "http://127.0.0.1:8000")


@router.post("/matches/generate", dependencies=[Depends(require_admin)])
def generate_matches(payload: schemas.MatchGenerateRequest, db: Session = Depends(get_db)):
    buyers = db.query(models.Buyer).filter(models.Buyer.event_id == payload.event_id).all()
    participants = db.query(models.Participant).filter(models.Participant.event_id == payload.event_id).all()

    if not buyers or not participants:
        raise HTTPException(400, "Bu etkinlik için buyer veya katılımcı kaydı bulunamadı.")

    existing_pairs = {
        (m.buyer_id, m.participant_id)
        for m in db.query(models.Match).filter(models.Match.event_id == payload.event_id).all()
    }

    created = 0
    skipped_existing = 0
    below_threshold = 0
    filtered_out = 0

    for buyer in buyers:
        for participant in participants:
            if (buyer.id, participant.id) in existing_pairs:
                skipped_existing += 1
                continue

            result = matching.compute_match(
                buyer, participant,
                payload.weight_product, payload.weight_sector, payload.weight_country,
                payload.country_mode,
            )
            if result is None:
                filtered_out += 1
                continue
            if result["total_score"] < payload.threshold:
                below_threshold += 1
                continue

            match = models.Match(
                event_id=payload.event_id,
                buyer_id=buyer.id,
                participant_id=participant.id,
                product_score=result["product_score"],
                sector_score=result["sector_score"],
                country_score=result["country_score"],
                total_score=result["total_score"],
                status="Önerildi",
            )
            db.add(match)
            created += 1

    db.commit()
    return {
        "created": created,
        "skipped_existing_pairs": skipped_existing,
        "below_threshold": below_threshold,
        "filtered_by_country_rule": filtered_out,
    }


@router.post("/matches/manual", dependencies=[Depends(require_admin)])
def create_manual_match(payload: schemas.ManualMatchRequest, db: Session = Depends(get_db)):
    """
    Admin'in kendi seçtiği bir buyer + katılımcı çiftini, eşleştirme
    motorunu hiç çalıştırmadan doğrudan eşleşme listesine ekler.
    Skor bilgisi referans için hesaplanır ama filtre/eşik uygulanmaz.
    """
    buyer = db.query(models.Buyer).get(payload.buyer_id)
    participant = db.query(models.Participant).get(payload.participant_id)
    if not buyer or not participant:
        raise HTTPException(404, "Buyer veya katılımcı bulunamadı.")
    if buyer.event_id != participant.event_id:
        raise HTTPException(400, "Buyer ve katılımcı aynı etkinliğe ait olmalıdır.")

    existing = db.query(models.Match).filter(
        models.Match.buyer_id == buyer.id,
        models.Match.participant_id == participant.id,
    ).first()
    if existing:
        raise HTTPException(400, "Bu buyer ve katılımcı için zaten bir eşleşme mevcut.")

    result = matching.compute_match(buyer, participant, 50, 30, 20, "none") or {
        "product_score": 0, "sector_score": 0, "country_score": 0, "total_score": 0,
    }

    match = models.Match(
        event_id=buyer.event_id,
        buyer_id=buyer.id,
        participant_id=participant.id,
        product_score=result["product_score"],
        sector_score=result["sector_score"],
        country_score=result["country_score"],
        total_score=result["total_score"],
        status="Önerildi",
    )
    db.add(match)
    db.commit()
    db.refresh(match)
    return {"ok": True, "match_id": match.id}


@router.get("/matches", response_model=List[schemas.MatchOut])
def list_matches(
    event_id: int = Query(...),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    q = db.query(models.Match).filter(models.Match.event_id == event_id)
    if status and status != "Tümü":
        q = q.filter(models.Match.status == status)
    matches = q.order_by(models.Match.total_score.desc()).all()

    out = []
    for m in matches:
        buyer = db.query(models.Buyer).get(m.buyer_id)
        participant = db.query(models.Participant).get(m.participant_id)
        out.append(schemas.MatchOut(
            id=m.id, event_id=m.event_id, buyer_id=m.buyer_id, participant_id=m.participant_id,
            buyer_name=buyer.company_name if buyer else "?",
            participant_name=participant.company_name if participant else "?",
            product_score=m.product_score, sector_score=m.sector_score,
            country_score=m.country_score, total_score=m.total_score,
            status=m.status, created_at=m.created_at,
        ))
    return out


@router.post("/matches/approve", dependencies=[Depends(require_admin)])
def admin_approve_matches(payload: schemas.MatchApproveRequest, db: Session = Depends(get_db)):
    """
    Admin'in seçtiği eşleşmeleri sisteme resmi olarak sokar: durum
    'Onay Bekliyor'a çekilir, buyer ve katılımcıya onay linkli mail atılır.
    """
    base_url = _get_base_url(db)
    results = []

    for match_id in payload.match_ids:
        match = db.query(models.Match).get(match_id)
        if not match:
            results.append({"match_id": match_id, "ok": False, "error": "Eşleşme bulunamadı"})
            continue

        buyer = db.query(models.Buyer).get(match.buyer_id)
        participant = db.query(models.Participant).get(match.participant_id)

        match.buyer_token = match.buyer_token or str(uuid.uuid4())
        match.participant_token = match.participant_token or str(uuid.uuid4())
        match.status = "Onay Bekliyor"

        send_to_buyer = payload.notify in ("both", "buyer")
        send_to_participant = payload.notify in ("both", "participant")

        buyer_ok = participant_ok = None
        buyer_err = participant_err = None
        buyer_skipped = not send_to_buyer
        participant_skipped = not send_to_participant

        if send_to_buyer and buyer and buyer.contact_email:
            subject, body = email_service.build_buyer_approval_email(buyer, participant, base_url, match.buyer_token)
            buyer_ok, buyer_err = email_service.send_email(db, buyer.contact_email, subject, body)
            db.add(models.EmailLog(match_id=match.id, recipient_type="buyer",
                                    recipient_email=buyer.contact_email, subject=subject,
                                    status="sent" if buyer_ok else "failed", error=buyer_err))
        elif send_to_buyer:
            buyer_ok = False
            buyer_err = "Buyer için e-posta adresi kayıtlı değil."

        if send_to_participant and participant and participant.contact_email:
            subject, body = email_service.build_participant_approval_email(buyer, participant, base_url, match.participant_token)
            participant_ok, participant_err = email_service.send_email(db, participant.contact_email, subject, body)
            db.add(models.EmailLog(match_id=match.id, recipient_type="participant",
                                    recipient_email=participant.contact_email, subject=subject,
                                    status="sent" if participant_ok else "failed", error=participant_err))
        elif send_to_participant:
            participant_ok = False
            participant_err = "Katılımcı için e-posta adresi kayıtlı değil."

        db.commit()
        results.append({
            "match_id": match_id, "ok": True,
            "buyer_mail_sent": buyer_ok, "buyer_mail_error": buyer_err, "buyer_mail_skipped": buyer_skipped,
            "participant_mail_sent": participant_ok, "participant_mail_error": participant_err,
            "participant_mail_skipped": participant_skipped,
        })

    return {"results": results}


@router.put("/matches/{match_id}/status", dependencies=[Depends(require_admin)])
def update_match_status(match_id: int, payload: schemas.MatchStatusUpdate, db: Session = Depends(get_db)):
    match = db.query(models.Match).get(match_id)
    if not match:
        raise HTTPException(404, "Eşleşme bulunamadı")
    match.status = payload.status
    db.commit()
    return {"ok": True}


def _render_response_page(title: str, message: str) -> str:
    return f"""
    <html><head><meta charset="utf-8"><title>{title}</title>
    <style>
      body{{font-family:Arial,sans-serif;background:#F7F3EA;color:#1E1712;
            display:flex;align-items:center;justify-content:center;height:100vh;margin:0;}}
      .box{{background:#fff;border:1px solid #ddd;padding:36px 44px;border-radius:4px;
            max-width:480px;text-align:center;}}
      h1{{font-size:20px;margin-bottom:12px;}}
      p{{color:#555;font-size:14px;}}
    </style></head>
    <body><div class="box"><h1>{title}</h1><p>{message}</p></div></body></html>
    """


@router.get("/approve/{token}", response_class=HTMLResponse)
def approve_via_link(token: str, db: Session = Depends(get_db)):
    match = db.query(models.Match).filter(
        (models.Match.buyer_token == token) | (models.Match.participant_token == token)
    ).first()
    if not match:
        return _render_response_page("Bağlantı geçersiz", "Bu onay bağlantısı bulunamadı veya süresi dolmuş olabilir.")

    is_buyer = (match.buyer_token == token)
    now = datetime.datetime.utcnow()

    if is_buyer:
        match.buyer_responded_at = now
        new_status = "Buyer Onayladı"
    else:
        match.participant_responded_at = now
        new_status = "Katılımcı Onayladı"

    if match.status == "Reddedildi":
        pass
    elif match.buyer_responded_at and match.participant_responded_at:
        match.status = "Karşılıklı Onaylandı"
    else:
        match.status = new_status

    db.commit()
    return _render_response_page("Onaylandı", "Görüşme talebini onayladınız. Karşı taraf da onayladığında toplantı planlama süreci başlayacaktır. Bilgilendirme e-postası ile tarafınıza ulaşılacaktır.")


@router.get("/reject/{token}", response_class=HTMLResponse)
def reject_via_link(token: str, db: Session = Depends(get_db)):
    match = db.query(models.Match).filter(
        (models.Match.buyer_token == token) | (models.Match.participant_token == token)
    ).first()
    if not match:
        return _render_response_page("Bağlantı geçersiz", "Bu onay bağlantısı bulunamadı veya süresi dolmuş olabilir.")

    match.status = "Reddedildi"
    db.commit()
    return _render_response_page("Reddedildi", "Görüşme talebini reddettiniz. İlgili taraf bilgilendirilecektir.")
