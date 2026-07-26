"""
SQLAlchemy ORM tabloları. Ayrıntılı şema açıklaması için:
docs/02_veritabani_semasi.md
"""
import datetime
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime, Date, Text,
    ForeignKey, UniqueConstraint
)
from sqlalchemy.orm import relationship
from .database import Base


def utcnow():
    return datetime.datetime.utcnow()


class Event(Base):
    __tablename__ = "events"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    venue = Column(String, nullable=True)
    created_at = Column(DateTime, default=utcnow)

    buyers = relationship("Buyer", back_populates="event", cascade="all, delete-orphan")
    participants = relationship("Participant", back_populates="event", cascade="all, delete-orphan")
    matches = relationship("Match", back_populates="event", cascade="all, delete-orphan")


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    full_name = Column(String, nullable=True)
    role = Column(String, nullable=False, default="operation")  # admin | operation
    created_at = Column(DateTime, default=utcnow)


class Buyer(Base):
    __tablename__ = "buyers"
    id = Column(Integer, primary_key=True)
    event_id = Column(Integer, ForeignKey("events.id"), nullable=False)
    company_name = Column(String, nullable=False)
    contact_name = Column(String, nullable=True)
    country = Column(String, nullable=True)
    contact_email = Column(String, nullable=True)
    contact_phone = Column(String, nullable=True)
    sector = Column(String, nullable=True)
    interested_products = Column(Text, nullable=True)
    max_meetings = Column(Integer, default=4)
    max_minutes = Column(Integer, default=60)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utcnow)

    event = relationship("Event", back_populates="buyers")
    matches = relationship("Match", back_populates="buyer", cascade="all, delete-orphan")


class Participant(Base):
    __tablename__ = "participants"
    id = Column(Integer, primary_key=True)
    event_id = Column(Integer, ForeignKey("events.id"), nullable=False)
    company_name = Column(String, nullable=False)
    contact_name = Column(String, nullable=True)
    country = Column(String, nullable=True)
    contact_email = Column(String, nullable=True)
    contact_phone = Column(String, nullable=True)
    sector = Column(String, nullable=True)
    offered_products = Column(Text, nullable=True)
    stand_no = Column(String, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utcnow)

    event = relationship("Event", back_populates="participants")
    matches = relationship("Match", back_populates="participant", cascade="all, delete-orphan")


class Match(Base):
    __tablename__ = "matches"
    id = Column(Integer, primary_key=True)
    event_id = Column(Integer, ForeignKey("events.id"), nullable=False)
    buyer_id = Column(Integer, ForeignKey("buyers.id"), nullable=False)
    participant_id = Column(Integer, ForeignKey("participants.id"), nullable=False)

    product_score = Column(Float, default=0)
    sector_score = Column(Float, default=0)
    country_score = Column(Float, default=0)
    total_score = Column(Float, default=0)

    status = Column(String, default="Önerildi")
    # Önerildi / Onay Bekliyor / Buyer Onayladı / Katılımcı Onayladı /
    # Karşılıklı Onaylandı / Toplantı Planlandı / Tamamlandı / No Show / Reddedildi

    buyer_token = Column(String, nullable=True, unique=True)
    participant_token = Column(String, nullable=True, unique=True)
    buyer_responded_at = Column(DateTime, nullable=True)
    participant_responded_at = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=utcnow)

    event = relationship("Event", back_populates="matches")
    buyer = relationship("Buyer", back_populates="matches")
    participant = relationship("Participant", back_populates="matches")
    meeting = relationship("Meeting", back_populates="match", uselist=False, cascade="all, delete-orphan")

    __table_args__ = (UniqueConstraint("buyer_id", "participant_id", name="uq_buyer_participant"),)


class Meeting(Base):
    __tablename__ = "meetings"
    id = Column(Integer, primary_key=True)
    match_id = Column(Integer, ForeignKey("matches.id"), nullable=False, unique=True)
    event_id = Column(Integer, ForeignKey("events.id"), nullable=False)
    meeting_date = Column(Date, nullable=False)
    start_time = Column(String, nullable=False)  # "10:00"
    end_time = Column(String, nullable=False)    # "10:15"
    stand_no = Column(String, nullable=True)
    status = Column(String, default="Planlandı")  # Planlandı / Tamamlandı / Katılmadı
    reminder_24h_sent = Column(Boolean, default=False)
    reminder_1h_sent = Column(Boolean, default=False)
    created_at = Column(DateTime, default=utcnow)

    match = relationship("Match", back_populates="meeting")


class EmailLog(Base):
    __tablename__ = "email_log"
    id = Column(Integer, primary_key=True)
    match_id = Column(Integer, ForeignKey("matches.id"), nullable=True)
    meeting_id = Column(Integer, ForeignKey("meetings.id"), nullable=True)
    recipient_type = Column(String, nullable=True)  # buyer / participant
    recipient_email = Column(String, nullable=True)
    subject = Column(String, nullable=True)
    status = Column(String, nullable=True)  # sent / failed
    error = Column(Text, nullable=True)
    sent_at = Column(DateTime, default=utcnow)


class ImportMapping(Base):
    __tablename__ = "import_mappings"
    id = Column(Integer, primary_key=True)
    entity_type = Column(String, nullable=False)  # buyer / participant
    name = Column(String, nullable=True)
    mapping_json = Column(Text, nullable=False)
    created_at = Column(DateTime, default=utcnow)


class AppSetting(Base):
    __tablename__ = "app_settings"
    key = Column(String, primary_key=True)
    value = Column(Text, nullable=True)
