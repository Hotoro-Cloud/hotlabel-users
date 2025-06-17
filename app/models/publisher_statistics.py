from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.db.base_class import Base

class PublisherStatistics(Base):
    __tablename__ = "publisher_statistics"

    id = Column(UUID, primary_key=True)
    publisher_id = Column(UUID, ForeignKey("users.id"), nullable=False)
    total_tasks = Column(Integer, default=0)
    completed_tasks = Column(Integer, default=0)
    average_quality_score = Column(Float, default=0.0)
    average_confidence = Column(Float, default=0.0)
    total_earnings = Column(Float, default=0.0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now()) 