"""
SMTP e-posta gönderim servisi + Türkçe e-posta şablonları.

Ayarlar veritabanındaki app_settings tablosundan okunur (bkz. settings.py).
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
from sqlalchemy.orm import Session

from . import models


def get_settings_dict(db: Session) -> dict:
    rows = db.query(models.AppSetting).all()
    return {r.key: r.value for r in rows}


def send_email(db: Session, to_email: str, subject: str, body_text: str) -> tuple[bool, Optional[str]]:
    """Ayarlardaki SMTP bilgileriyle mail gönderir. (ok, error) döner."""
    settings = get_settings_dict(db)
    host = settings.get("smtp_host")
    port = settings.get("smtp_port") or "587"
    user = settings.get("smtp_user")
    password = settings.get("smtp_pass")
    from_name = settings.get("smtp_from_name") or "Foodist İstanbul"
    from_email = settings.get("smtp_from_email") or user
    secure = (settings.get("smtp_secure") or "false").lower() == "true"

    if not host or not user or not password:
        return False, "SMTP ayarları eksik. Lütfen Ayarlar ekranından e-posta sunucu bilgilerini girin."

    if not to_email:
        return False, "Alıcı e-posta adresi boş."

    try:
        msg = MIMEMultipart()
        msg["From"] = f"{from_name} <{from_email}>"
        msg["To"] = to_email
        msg["Subject"] = subject
        msg.attach(MIMEText(body_text, "plain", "utf-8"))

        if secure:
            server = smtplib.SMTP_SSL(host, int(port))
        else:
            server = smtplib.SMTP(host, int(port))
            server.starttls()
        server.login(user, password)
        server.sendmail(from_email, [to_email], msg.as_string())
        server.quit()
        return True, None
    except Exception as e:
        return False, str(e)


def build_buyer_approval_email(buyer, participant, base_url: str, token: str) -> tuple[str, str]:
    subject = f"Görüşme Önerisi: {participant.company_name}"
    body = f"""Sayın {buyer.contact_name or buyer.company_name},

Aşağıdaki firma ile görüşmeniz önerilmektedir.

Firma:
{participant.company_name}

Ürün Grubu:
{participant.offered_products or '-'}

Ülke:
{participant.country or '-'}

Görüşmeyi kabul ediyor musunuz?

Onaylamak için: {base_url}/approve/{token}
Reddetmek için: {base_url}/reject/{token}

Foodist İstanbul Hosted Buyer Programı
"""
    return subject, body


def build_participant_approval_email(buyer, participant, base_url: str, token: str) -> tuple[str, str]:
    subject = f"Görüşme Talebi: {buyer.company_name}"
    body = f"""Sayın {participant.contact_name or participant.company_name},

Aşağıdaki buyer sizinle görüşmek istemektedir.

Buyer:
{buyer.company_name}

Ülke:
{buyer.country or '-'}

İlgilendiği Ürünler:
{buyer.interested_products or '-'}

Görüşmeyi kabul ediyor musunuz?

Onaylamak için: {base_url}/approve/{token}
Reddetmek için: {base_url}/reject/{token}

Foodist İstanbul Hosted Buyer Programı
"""
    return subject, body


def build_meeting_confirmation_email(recipient_name: str, other_party_name: str, meeting, stand_no: str) -> tuple[str, str]:
    subject = f"Toplantınız Planlandı — {meeting.meeting_date} {meeting.start_time}"
    body = f"""Sayın {recipient_name},

{other_party_name} ile görüşmeniz planlanmıştır.

Tarih: {meeting.meeting_date}
Saat: {meeting.start_time} - {meeting.end_time}
Stand No: {stand_no or '-'}

Bu bilgiyi takviminize eklemek için uygulamadan ICS dosyasını indirebilirsiniz.

Foodist İstanbul Hosted Buyer Programı
"""
    return subject, body


def build_reminder_email(recipient_name: str, other_party_name: str, meeting, hours_before: int) -> tuple[str, str]:
    subject = f"Hatırlatma: {hours_before} saat sonra toplantınız var"
    body = f"""Sayın {recipient_name},

{other_party_name} ile {meeting.meeting_date} tarihli, {meeting.start_time} saatindeki
görüşmenize {hours_before} saat kalmıştır. Stand No: {meeting.stand_no or '-'}

Foodist İstanbul Hosted Buyer Programı
"""
    return subject, body
