"""All SQLAlchemy ORM models."""
import enum
from datetime import datetime, timezone
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime,
    Text, ForeignKey, JSON, Enum as SAEnum
)
from sqlalchemy.orm import relationship
from core.database import Base


def _now():
    return datetime.now(timezone.utc)


class UserRole(str, enum.Enum):
    ADMIN = "admin"
    RANGER = "ranger"
    VISITOR = "visitor"
    VOLUNTEER = "volunteer"


# ── Users ──
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    full_name = Column(String(100), default="")
    hashed_password = Column(String(200), nullable=False)
    role = Column(SAEnum(UserRole), default=UserRole.VISITOR, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=_now)
    last_login = Column(DateTime, nullable=True)

    ranger_profile = relationship("Ranger", back_populates="user", uselist=False)
    visitor_profile = relationship("Visitor", back_populates="user", uselist=False)
    volunteer_profile = relationship("Volunteer", back_populates="user", uselist=False)


# ── Rangers ──
class Ranger(Base):
    __tablename__ = "rangers"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    badge_number = Column(String(20), unique=True, nullable=False)
    sector = Column(String(50), default="Zone-A")
    current_lat = Column(Float, default=11.4916)
    current_lon = Column(Float, default=76.9294)
    is_on_duty = Column(Boolean, default=True)
    status = Column(String(20), default="patrolling")
    phone = Column(String(20), default="")
    patrol_route = Column(JSON, default=list)
    last_updated = Column(DateTime, default=_now)
    user = relationship("User", back_populates="ranger_profile")
    dispatches = relationship("RangerDispatch", back_populates="ranger")


class RangerDispatch(Base):
    __tablename__ = "ranger_dispatches"
    id = Column(Integer, primary_key=True, index=True)
    ranger_id = Column(Integer, ForeignKey("rangers.id"), nullable=False)
    alert_id = Column(Integer, ForeignKey("alerts.id"), nullable=True)
    incident_lat = Column(Float, nullable=False)
    incident_lon = Column(Float, nullable=False)
    dispatched_at = Column(DateTime, default=_now)
    arrived_at = Column(DateTime, nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    notes = Column(Text, default="")
    status = Column(String(20), default="dispatched")
    ranger = relationship("Ranger", back_populates="dispatches")
    alert = relationship("Alert")


# ── Visitors ──
class Visitor(Base):
    __tablename__ = "visitors"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    permit_type = Column(String(30), default="day_pass")
    vehicle_number = Column(String(20), default="")
    entry_time = Column(DateTime, nullable=True)
    exit_time = Column(DateTime, nullable=True)
    ticket_qr = Column(Text, default="")
    group_size = Column(Integer, default=1)
    is_inside = Column(Boolean, default=False)
    overstay_alerted = Column(Boolean, default=False)
    user = relationship("User", back_populates="visitor_profile")
    visit_logs = relationship("VisitLog", back_populates="visitor")


class VisitLog(Base):
    __tablename__ = "visit_logs"
    id = Column(Integer, primary_key=True, index=True)
    visitor_id = Column(Integer, ForeignKey("visitors.id"), nullable=False)
    action = Column(String(10), nullable=False)
    timestamp = Column(DateTime, default=_now)
    gate = Column(String(30), default="main")
    notes = Column(Text, default="")
    visitor = relationship("Visitor", back_populates="visit_logs")


# ── Volunteers ──
class Volunteer(Base):
    __tablename__ = "volunteers"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    skills = Column(JSON, default=list)
    points = Column(Integer, default=0)
    is_verified = Column(Boolean, default=False)
    zone_assigned = Column(String(50), default="Zone-A")
    joined_at = Column(DateTime, default=_now)
    user = relationship("User", back_populates="volunteer_profile")
    reports = relationship("VolunteerReport", back_populates="volunteer")


class VolunteerReport(Base):
    __tablename__ = "volunteer_reports"
    id = Column(Integer, primary_key=True, index=True)
    volunteer_id = Column(Integer, ForeignKey("volunteers.id"), nullable=False)
    incident_type = Column(String(50), nullable=False)
    description = Column(Text, nullable=False)
    lat = Column(Float, nullable=False)
    lon = Column(Float, nullable=False)
    image_path = Column(String(200), default="")
    status = Column(String(20), default="pending")
    created_at = Column(DateTime, default=_now)
    points_awarded = Column(Integer, default=0)
    volunteer = relationship("Volunteer", back_populates="reports")


# ── Alerts ──
class Alert(Base):
    __tablename__ = "alerts"
    id = Column(Integer, primary_key=True, index=True)
    alert_type = Column(String(30), nullable=False)
    severity = Column(String(20), default="medium")
    status = Column(String(20), default="active")
    lat = Column(Float, nullable=False)
    lon = Column(Float, nullable=False)
    zone = Column(String(50), default="Unknown")
    description = Column(Text, default="")
    source = Column(String(30), default="system")
    confidence = Column(Float, default=0.8)
    created_at = Column(DateTime, default=_now)
    acknowledged_at = Column(DateTime, nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    acknowledged_by = Column(String(50), default="")
    extra_data = Column(JSON, default=dict)


# ── Animal Sightings ──
class AnimalSighting(Base):
    __tablename__ = "animal_sightings"
    id = Column(Integer, primary_key=True, index=True)
    animal_id = Column(String(20), nullable=False)
    species = Column(String(50), nullable=False)
    lat = Column(Float, nullable=False)
    lon = Column(Float, nullable=False)
    confidence = Column(Float, default=0.9)
    image_path = Column(String(200), default="")
    seen_at = Column(DateTime, default=_now)
    zone = Column(String(50), default="")
    notes = Column(Text, default="")


# ── Incidents ──
class Incident(Base):
    __tablename__ = "incidents"
    id = Column(Integer, primary_key=True, index=True)
    incident_type = Column(String(50), nullable=False)
    severity = Column(String(20), default="medium")
    lat = Column(Float, nullable=False)
    lon = Column(Float, nullable=False)
    zone = Column(String(50), default="")
    description = Column(Text, default="")
    reported_by = Column(String(50), default="system")
    status = Column(String(20), default="open")
    created_at = Column(DateTime, default=_now)
    resolved_at = Column(DateTime, nullable=True)
    resolution_notes = Column(Text, default="")


# ── Weather Cache ──
class WeatherRecord(Base):
    __tablename__ = "weather_records"
    id = Column(Integer, primary_key=True, index=True)
    temperature = Column(Float, default=0.0)
    humidity = Column(Float, default=0.0)
    wind_speed = Column(Float, default=0.0)
    wind_direction = Column(Float, default=0.0)
    conditions = Column(String(100), default="Clear")
    fire_risk_score = Column(Float, default=0.0)
    recorded_at = Column(DateTime, default=_now)
    raw_data = Column(JSON, default=dict)


# ── Daily Reports ──
class DailyReport(Base):
    __tablename__ = "daily_reports"
    id = Column(Integer, primary_key=True, index=True)
    report_date = Column(String(20), nullable=False, unique=True)
    total_alerts = Column(Integer, default=0)
    critical_alerts = Column(Integer, default=0)
    visitors_today = Column(Integer, default=0)
    animal_sightings = Column(Integer, default=0)
    incidents_resolved = Column(Integer, default=0)
    rangers_on_duty = Column(Integer, default=0)
    pdf_path = Column(String(200), default="")
    summary = Column(Text, default="")
    created_at = Column(DateTime, default=_now)
    raw_data = Column(JSON, default=dict)
