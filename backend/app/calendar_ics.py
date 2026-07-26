"""ICS (iCalendar) dosyası üretimi — Outlook/Google Calendar'a tek tıkla
içe aktarım için. Harici kütüphane gerekmez, RFC 5545 minimum alanlarla
manuel üretilir."""
import datetime


def _fmt(dt: datetime.datetime) -> str:
    return dt.strftime("%Y%m%dT%H%M%S")


def build_ics(
    summary: str,
    description: str,
    location: str,
    meeting_date: datetime.date,
    start_time: str,
    end_time: str,
    uid: str,
) -> str:
    start_h, start_m = map(int, start_time.split(":"))
    end_h, end_m = map(int, end_time.split(":"))
    start_dt = datetime.datetime.combine(meeting_date, datetime.time(start_h, start_m))
    end_dt = datetime.datetime.combine(meeting_date, datetime.time(end_h, end_m))

    ics = "\r\n".join([
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//Foodist Istanbul//Hosted Buyer CRM//TR",
        "CALSCALE:GREGORIAN",
        "BEGIN:VEVENT",
        f"UID:{uid}",
        f"DTSTAMP:{_fmt(datetime.datetime.utcnow())}Z",
        f"DTSTART:{_fmt(start_dt)}",
        f"DTEND:{_fmt(end_dt)}",
        f"SUMMARY:{summary}",
        f"DESCRIPTION:{description}",
        f"LOCATION:{location}",
        "END:VEVENT",
        "END:VCALENDAR",
        "",
    ])
    return ics
