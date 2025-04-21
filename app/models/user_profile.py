import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, JSON, Integer, Boolean, Table, ForeignKey
from sqlalchemy.orm import relationship

from app.db.session import Base

# Many-to-many relationship table for expertise areas
profile_expertise_table = Table(
    "profile_expertise",
    Base.metadata,
    Column("profile_id", String, ForeignKey("user_profiles.id")),
    Column("expertise_id", String, ForeignKey("expertise_areas.id"))
)


class UserProfile(Base):
    """Model for opt-in expert network profiles."""
    
    __tablename__ = "user_profiles"
    
    id = Column(String, primary_key=True, index=True, default=lambda: f"prof_{uuid.uuid4().hex[:8]}")
    
    # Basic profile information (anonymized)
    display_name = Column(String, nullable=True)  # Optional display name
    email_hash = Column(String, nullable=True, index=True)  # Hashed email for identification
    
    # Expertise and preferences
    primary_language = Column(String, nullable=True)
    additional_languages = Column(JSON, default=list)  # List of language codes
    timezone = Column(String, nullable=True)
    
    # Expert profile
    expertise_level = Column(Integer, default=0)  # 0-4 scale, based on tasks completed
    verified = Column(Boolean, default=False)  # Whether the user is a verified expert
    
    # Settings
    notification_preferences = Column(JSON, default=dict)
    privacy_settings = Column(JSON, default=dict)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_active = Column(DateTime, default=datetime.utcnow)
    
    # Task history
    tasks_completed = Column(Integer, default=0)
    quality_score = Column(Integer, default=0)  # 0-100 score based on task quality
    
    # Additional profile data
    profile_metadata = Column(JSON, default=dict)
    
    # Relationships
    sessions = relationship("UserSession", back_populates="profile")
    statistics = relationship("UserStatistics", back_populates="profile", uselist=False)
    expertise_areas = relationship("ExpertiseArea", secondary=profile_expertise_table, back_populates="profiles")
