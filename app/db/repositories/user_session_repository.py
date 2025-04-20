from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, func

from app.db.repositories.base import BaseRepository
from app.models.user_session import UserSession
from app.schemas.user_session import UserSessionCreate, UserSessionUpdate


class UserSessionRepository(BaseRepository[UserSession, UserSessionCreate, UserSessionUpdate]):
    """Repository for user session operations."""
    
    def __init__(self):
        super().__init__(UserSession)
    
    def get_by_browser_fingerprint(self, db: Session, browser_fingerprint: str) -> Optional[UserSession]:
        """Get a user session by browser fingerprint."""
        return db.query(self.model).filter(self.model.browser_fingerprint == browser_fingerprint).first()
    
    def get_by_publisher_id(
        self, db: Session, publisher_id: str, skip: int = 0, limit: int = 100
    ) -> List[UserSession]:
        """Get user sessions by publisher ID."""
        return db.query(self.model).filter(
            self.model.publisher_id == publisher_id
        ).offset(skip).limit(limit).all()
    
    def get_by_profile_id(
        self, db: Session, profile_id: str, skip: int = 0, limit: int = 100
    ) -> List[UserSession]:
        """Get user sessions by profile ID."""
        return db.query(self.model).filter(
            self.model.profile_id == profile_id
        ).offset(skip).limit(limit).all()
    
    def get_active_sessions(
        self, db: Session, hours: int = 24, skip: int = 0, limit: int = 100
    ) -> List[UserSession]:
        """Get active sessions within the last X hours."""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        return db.query(self.model).filter(
            self.model.last_active >= cutoff_time
        ).offset(skip).limit(limit).all()
    
    def update_last_active(self, db: Session, session_id: str) -> Optional[UserSession]:
        """Update the last active timestamp for a session."""
        session = self.get(db, session_id)
        if not session:
            return None
        
        session.last_active = datetime.utcnow()
        db.add(session)
        db.commit()
        db.refresh(session)
        return session
    
    def increment_tasks_completed(self, db: Session, session_id: str) -> Optional[UserSession]:
        """Increment the tasks completed counter for a session."""
        session = self.get(db, session_id)
        if not session:
            return None
        
        session.tasks_completed += 1
        db.add(session)
        db.commit()
        db.refresh(session)
        return session
    
    def increment_tasks_attempted(self, db: Session, session_id: str) -> Optional[UserSession]:
        """Increment the tasks attempted counter for a session."""
        session = self.get(db, session_id)
        if not session:
            return None
        
        session.tasks_attempted += 1
        db.add(session)
        db.commit()
        db.refresh(session)
        return session
    
    def count_by_publisher(self, db: Session, publisher_id: str) -> int:
        """Count sessions for a publisher."""
        return db.query(func.count(self.model.id)).filter(
            self.model.publisher_id == publisher_id
        ).scalar()
    
    def get_by_consent_status(
        self, db: Session, consent_given: bool, skip: int = 0, limit: int = 100
    ) -> List[UserSession]:
        """Get sessions by consent status."""
        return db.query(self.model).filter(
            self.model.consent_given == consent_given
        ).offset(skip).limit(limit).all()
    
    def bulk_update(
        self, db: Session, updates: Dict[str, Dict[str, Any]]
    ) -> List[UserSession]:
        """Bulk update sessions with a dictionary of {id: update_data}."""
        updated_sessions = []
        for session_id, update_data in updates.items():
            session = self.get(db, session_id)
            if session:
                for key, value in update_data.items():
                    setattr(session, key, value)
                db.add(session)
                updated_sessions.append(session)
        
        db.commit()
        for session in updated_sessions:
            db.refresh(session)
        
        return updated_sessions
    
    def delete_expired_sessions(self, db: Session, retention_days: int) -> int:
        """Delete sessions older than the retention period."""
        cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
        result = db.query(self.model).filter(
            self.model.updated_at < cutoff_date
        ).delete()
        db.commit()
        return result
