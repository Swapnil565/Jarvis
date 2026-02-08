from sqlalchemy import Column, Integer, String, Text, Float, Boolean, DateTime
from sqlalchemy.orm import declarative_base
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime

Base = declarative_base()


class Event(Base):
    __tablename__ = 'events'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False)
    category = Column(String, nullable=False)
    event_type = Column(String, nullable=False)
    timestamp = Column(String, nullable=False)
    feeling = Column(String, nullable=True)
    data = Column(Text, nullable=False)  # keep as text for compatibility


class Pattern(Base):
    __tablename__ = 'patterns'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False)
    pattern_type = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    confidence = Column(Float, nullable=False)
    frequency = Column(Integer, default=1)
    first_detected = Column(String, nullable=False)
    last_seen = Column(String, nullable=False)
    data = Column(Text, nullable=False)
    is_active = Column(Boolean, default=True)


class Intervention(Base):
    __tablename__ = 'interventions'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False)
    intervention_type = Column(String, nullable=False)
    urgency = Column(String, nullable=False)
    title = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    created_at = Column(String, nullable=False)
    delivered_at = Column(String, nullable=True)
    acknowledged_at = Column(String, nullable=True)
    user_rating = Column(Integer, nullable=True)
    was_helpful = Column(Boolean, nullable=True)
    data = Column(Text, nullable=False)
