import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Text, ForeignKey, Boolean
from sqlalchemy.orm import relationship

from app.db.session import Base
from app.models.user_profile import profile_expertise_table


class ExpertiseArea(Base):
    """Model for categorizing expertise domains."""
    
    __tablename__ = "expertise_areas"
    
    id = Column(String, primary_key=True, index=True, default=lambda: f"exp_{uuid.uuid4().hex[:8]}")
    
    # Basic information
    name = Column(String, index=True, nullable=False)
    slug = Column(String, index=True, nullable=False, unique=True)
    description = Column(Text, nullable=True)
    
    # Hierarchical structure
    parent_id = Column(String, ForeignKey("expertise_areas.id"), nullable=True)
    parent = relationship("ExpertiseArea", remote_side=[id], backref="children")
    
    # Status
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    profiles = relationship("UserProfile", secondary=profile_expertise_table, back_populates="expertise_areas")
    
    def __repr__(self):
        return f"<ExpertiseArea {self.name}>"
