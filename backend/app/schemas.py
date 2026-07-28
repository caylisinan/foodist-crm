"""Pydantic modelleri — API giriş/çıkış doğrulaması."""
from typing import Optional, List
from datetime import date, datetime
from pydantic import BaseModel


# ---------- Event ----------
class EventCreate(BaseModel):
    name: str
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    venue: Optional[str] = None


class EventOut(EventCreate):
    id: int
    model_config = {"from_attributes": True}


# ---------- Buyer ----------
class BuyerCreate(BaseModel):
    event_id: int
    company_name: str
    contact_name: Optional[str] = None
    country: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    sector: Optional[str] = None
    interested_products: Optional[str] = None
    max_meetings: int = 4
    max_minutes: int = 60
    notes: Optional[str] = None


class BuyerOut(BuyerCreate):
    id: int
    model_config = {"from_attributes": True}


# ---------- Participant ----------
class ParticipantCreate(BaseModel):
    event_id: int
    company_name: str
    contact_name: Optional[str] = None
    country: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    sector: Optional[str] = None
    offered_products: Optional[str] = None
    stand_no: Optional[str] = None
    notes: Optional[str] = None


class ParticipantOut(ParticipantCreate):
    id: int
    model_config = {"from_attributes": True}


# ---------- Matching ----------
class MatchGenerateRequest(BaseModel):
    event_id: int
    weight_product: float = 50
    weight_sector: float = 30
    weight_country: float = 20
    country_mode: str = "none"  # none | same_only | exclude_same
    threshold: float = 40
    send_admin_preview: bool = False


class ManualMatchRequest(BaseModel):
    buyer_id: int
    participant_id: int


class MatchOut(BaseModel):
    id: int
    event_id: int
    buyer_id: int
    participant_id: int
    buyer_name: str
    participant_name: str
    product_score: float
    sector_score: float
    country_score: float
    total_score: float
    status: str
    created_at: datetime
    model_config = {"from_attributes": True}


class MatchStatusUpdate(BaseModel):
    status: str


class MatchApproveRequest(BaseModel):
    match_ids: List[int]
    notify: str = "both"  # both | buyer | participant


# ---------- Meeting ----------
class MeetingCreate(BaseModel):
    match_id: int
    meeting_date: date
    start_time: str
    stand_no: Optional[str] = None
    send_email: bool = True


class MeetingOut(BaseModel):
    id: int
    match_id: int
    event_id: int
    meeting_date: date
    start_time: str
    end_time: str
    stand_no: Optional[str] = None
    status: str
    buyer_name: Optional[str] = None
    participant_name: Optional[str] = None
    model_config = {"from_attributes": True}


class AttendanceUpdate(BaseModel):
    status: str  # Tamamlandı / Katılmadı


# ---------- Settings ----------
class SettingsUpdate(BaseModel):
    smtp_host: Optional[str] = None
    smtp_port: Optional[str] = None
    smtp_user: Optional[str] = None
    smtp_pass: Optional[str] = None
    smtp_from_name: Optional[str] = None
    smtp_from_email: Optional[str] = None
    smtp_secure: Optional[str] = None
    weight_product: Optional[str] = None
    weight_sector: Optional[str] = None
    weight_country: Optional[str] = None
    match_threshold: Optional[str] = None
    default_max_meetings: Optional[str] = None
    default_max_minutes: Optional[str] = None
    app_base_url: Optional[str] = None


# ---------- Import ----------
class ImportCommitRequest(BaseModel):
    event_id: int
    entity_type: str  # buyer | participant
    file_token: str
    mapping: dict
