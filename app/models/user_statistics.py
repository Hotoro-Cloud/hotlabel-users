import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, JSON, Integer, Float, ForeignKey
from sqlalchemy.orm import relationship

from app.db.session import Base


class UserStatistics(Base):
    """Model for tracking user performance and statistics."""
    
    __tablename__ = "user_statistics"
    
    id = Column(String, primary_key=True, index=True, default=lambda: f"stat_{uuid.uuid4().hex[:8]}")
    
    # Associated user (either session or profile)
    session_id = Column(String, ForeignKey("user_sessions.id"), nullable=True)
    profile_id = Column(String, ForeignKey("user_profiles.id"), nullable=True)
    
    # General statistics
    total_tasks_completed = Column(Integer, default=0)
    total_tasks_attempted = Column(Integer, default=0)
    completion_rate = Column(Float, default=0.0)  # Percentage of tasks completed
    success_rate = Column(Float, default=0.0)  # Percentage of successful tasks
    
    # Performance metrics
    average_task_time_ms = Column(Integer, default=0)
    fastest_task_time_ms = Column(Integer, default=0)
    slowest_task_time_ms = Column(Integer, default=0)
    
    # Task type breakdown
    task_type_distribution = Column(JSON, default=dict)  # {"task_type": count}
    
    # Quality metrics
    average_quality_score = Column(Float, default=0.0)  # 0-1 scale
    quality_distribution = Column(JSON, default=dict)  # {"score_range": count}
    
    # Expertise metrics
    expertise_level = Column(Integer, default=0)  # 0-4 scale
    expertise_areas = Column(JSON, default=list)  # List of expertise area IDs
    
    # Time-based metrics
    first_task_date = Column(DateTime, nullable=True)
    last_task_date = Column(DateTime, nullable=True)
    active_days = Column(Integer, default=0)
    
    # Additional metrics
    engagement_score = Column(Float, default=0.0)  # Composite score based on multiple factors
    consistency_score = Column(Float, default=0.0)  # Measures regular participation
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    session = relationship("UserSession", back_populates="statistics")
    profile = relationship("UserProfile", back_populates="statistics")
