import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, JSON, Integer, ForeignKey
from sqlalchemy.orm import relationship

from app.db.session import Base


class UserSession(Base):
    """Model for anonymous user sessions."""
    
    __tablename__ = "user_sessions"
    
    id = Column(String, primary_key=True, index=True, default=lambda: f"sess_{uuid.uuid4().hex[:8]}")
    
    # Publisher relationship
    publisher_id = Column(String, index=True, nullable=False)
    
    # Browser data (anonymized)
    browser_fingerprint = Column(String, index=True, nullable=True)  # Hashed browser fingerprint
    user_agent = Column(String, nullable=True)
    language = Column(String, index=True, nullable=True)
    timezone = Column(String, nullable=True)
    
    # Session metadata
    referrer = Column(String, nullable=True)
    country = Column(String, index=True, nullable=True)
    device_type = Column(String, nullable=True)  # mobile, desktop, tablet
    platform = Column(String, nullable=True)  # OS
    
    # Tracking data
    last_active = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Privacy and consent
    consent_given = Column(Boolean, default=False)
    analytics_opt_in = Column(Boolean, default=False)
    personalization_opt_in = Column(Boolean, default=False)
    
    # Additional data
    session_metadata = Column(JSON, default=dict)  # Additional session data
    
    # Task tracking
    tasks_completed = Column(Integer, default=0)
    tasks_attempted = Column(Integer, default=0)
    
    # Expert network relationship (optional)
    profile_id = Column(String, ForeignKey("user_profiles.id"), nullable=True)
    profile = relationship("UserProfile", back_populates="sessions")
    
    # Statistics
    statistics = relationship("UserStatistics", back_populates="session", uselist=False)
