from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.db.repositories.base import BaseRepository
from app.models.user_profile import UserProfile
from app.schemas.user_profile import UserProfileCreate, UserProfileUpdate


class UserProfileRepository(BaseRepository[UserProfile, UserProfileCreate, UserProfileUpdate]):
    """Repository for user profile operations."""
    
    def __init__(self):
        super().__init__(UserProfile)
    
    def get_by_email_hash(self, db: Session, email_hash: str) -> Optional[UserProfile]:
        """Get a user profile by email hash."""
        return db.query(self.model).filter(self.model.email_hash == email_hash).first()
    
    def get_by_expertise_level(
        self, db: Session, level: int, skip: int = 0, limit: int = 100
    ) -> List[UserProfile]:
        """Get user profiles by expertise level."""
        return db.query(self.model).filter(
            self.model.expertise_level == level
        ).offset(skip).limit(limit).all()
    
    def get_by_expertise_area(
        self, db: Session, expertise_area_id: str, skip: int = 0, limit: int = 100
    ) -> List[UserProfile]:
        """Get user profiles by expertise area."""
        return db.query(self.model).join(
            self.model.expertise_areas
        ).filter(
            self.model.expertise_areas.any(id=expertise_area_id)
        ).offset(skip).limit(limit).all()
    
    def get_active_profiles(
        self, db: Session, days: int = 30, skip: int = 0, limit: int = 100
    ) -> List[UserProfile]:
        """Get profiles active within the last X days."""
        cutoff_time = datetime.utcnow() - timedelta(days=days)
        return db.query(self.model).filter(
            self.model.last_active >= cutoff_time
        ).offset(skip).limit(limit).all()
    
    def update_last_active(self, db: Session, profile_id: str) -> Optional[UserProfile]:
        """Update the last active timestamp for a profile."""
        profile = self.get(db, profile_id)
        if not profile:
            return None
        
        profile.last_active = datetime.utcnow()
        db.add(profile)
        db.commit()
        db.refresh(profile)
        return profile
    
    def increment_tasks_completed(self, db: Session, profile_id: str) -> Optional[UserProfile]:
        """Increment the tasks completed counter for a profile."""
        profile = self.get(db, profile_id)
        if not profile:
            return None
        
        profile.tasks_completed += 1
        
        # Update expertise level based on tasks completed
        profile.expertise_level = self._calculate_expertise_level(profile.tasks_completed)
        
        db.add(profile)
        db.commit()
        db.refresh(profile)
        return profile
    
    def _calculate_expertise_level(self, tasks_completed: int) -> int:
        """Calculate expertise level based on completed tasks."""
        from app.core.config import settings
        
        thresholds = settings.EXPERT_LEVEL_THRESHOLDS
        for level, threshold in enumerate(thresholds):
            if tasks_completed < threshold:
                return level
        
        # If more than all thresholds, return the highest level
        return len(thresholds)
    
    def update_expertise_areas(
        self, db: Session, profile_id: str, expertise_area_ids: List[str]
    ) -> Optional[UserProfile]:
        """Update the expertise areas for a profile."""
        from app.models.expertise_area import ExpertiseArea
        
        profile = self.get(db, profile_id)
        if not profile:
            return None
        
        # Get expertise areas by IDs
        expertise_areas = db.query(ExpertiseArea).filter(
            ExpertiseArea.id.in_(expertise_area_ids)
        ).all()
        
        # Update profile's expertise areas
        profile.expertise_areas = expertise_areas
        
        db.add(profile)
        db.commit()
        db.refresh(profile)
        return profile
    
    def update_quality_score(
        self, db: Session, profile_id: str, quality_score: int
    ) -> Optional[UserProfile]:
        """Update the quality score for a profile."""
        profile = self.get(db, profile_id)
        if not profile:
            return None
        
        profile.quality_score = min(100, max(0, quality_score))  # Ensure within 0-100 range
        
        db.add(profile)
        db.commit()
        db.refresh(profile)
        return profile
    
    def count_by_language(self, db: Session, language: str) -> int:
        """Count profiles by primary language."""
        return db.query(func.count(self.model.id)).filter(
            self.model.primary_language == language
        ).scalar()
    
    def get_verified_profiles(
        self, db: Session, skip: int = 0, limit: int = 100
    ) -> List[UserProfile]:
        """Get verified profiles."""
        return db.query(self.model).filter(
            self.model.verified == True
        ).offset(skip).limit(limit).all()
    
    def get_top_contributors(
        self, db: Session, limit: int = 10
    ) -> List[UserProfile]:
        """Get top contributors based on tasks completed."""
        return db.query(self.model).order_by(
            self.model.tasks_completed.desc()
        ).limit(limit).all()
