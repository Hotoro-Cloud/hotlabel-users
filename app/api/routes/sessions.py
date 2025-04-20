from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.repositories.user_session_repository import UserSessionRepository
from app.db.repositories.user_statistics_repository import UserStatisticsRepository
from app.schemas.user_session import (
    UserSession,
    UserSessionCreate,
    UserSessionUpdate,
    UserSessionWithStats
)
from app.core.exceptions import ResourceNotFound

router = APIRouter(prefix="/sessions", tags=["sessions"])

# Initialize repositories
session_repository = UserSessionRepository()
statistics_repository = UserStatisticsRepository()


@router.post("", response_model=UserSession, status_code=status.HTTP_201_CREATED)
def create_session(
    session_data: UserSessionCreate,
    db: Session = Depends(get_db)
):
    """Create a new user session."""
    # Create session
    session = session_repository.create(db, obj_in=session_data)
    
    # Create statistics for session
    statistics_repository.create_for_session(db, session_id=session.id)
    
    return session


@router.get("/{session_id}", response_model=UserSession)
def get_session(
    session_id: str,
    db: Session = Depends(get_db)
):
    """Get a user session by ID."""
    session = session_repository.get(db, session_id)
    if not session:
        raise ResourceNotFound("Session", session_id)
    
    # Update last active timestamp
    session_repository.update_last_active(db, session_id)
    
    return session


@router.patch("/{session_id}", response_model=UserSession)
def update_session(
    session_id: str,
    session_data: UserSessionUpdate,
    db: Session = Depends(get_db)
):
    """Update a user session."""
    session = session_repository.get(db, session_id)
    if not session:
        raise ResourceNotFound("Session", session_id)
    
    return session_repository.update(
        db, db_obj=session, obj_in=session_data
    )


@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_session(
    session_id: str,
    db: Session = Depends(get_db)
):
    """Delete a user session."""
    session = session_repository.get(db, session_id)
    if not session:
        raise ResourceNotFound("Session", session_id)
    
    session_repository.remove(db, id=session_id)
    return None


@router.post("/{session_id}/consent", response_model=UserSession)
def update_consent(
    session_id: str,
    consent_data: dict,
    db: Session = Depends(get_db)
):
    """Update consent settings for a session."""
    session = session_repository.get(db, session_id)
    if not session:
        raise ResourceNotFound("Session", session_id)
    
    update_data = UserSessionUpdate(
        consent_given=consent_data.get("consent_given", False),
        analytics_opt_in=consent_data.get("analytics_opt_in", False),
        personalization_opt_in=consent_data.get("personalization_opt_in", False)
    )
    
    return session_repository.update(
        db, db_obj=session, obj_in=update_data
    )


@router.get("/{session_id}/stats", response_model=UserSessionWithStats)
def get_session_statistics(
    session_id: str,
    db: Session = Depends(get_db)
):
    """Get detailed statistics for a session."""
    session = session_repository.get(db, session_id)
    if not session:
        raise ResourceNotFound("Session", session_id)
    
    # Get statistics
    stats = statistics_repository.get_by_session_id(db, session_id)
    if not stats:
        # Create statistics if they don't exist
        stats = statistics_repository.create_for_session(db, session_id)
    
    # Combine session with stats
    session_dict = {
        **session.__dict__,
        "success_rate": stats.success_rate if stats else None,
        "average_task_time_ms": stats.average_task_time_ms if stats else None,
        "expertise_level": stats.expertise_level if stats else None
    }
    
    return session_dict


@router.get("", response_model=List[UserSession])
def list_sessions(
    publisher_id: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """List user sessions, optionally filtered by publisher."""
    if publisher_id:
        return session_repository.get_by_publisher_id(
            db, publisher_id=publisher_id, skip=skip, limit=limit
        )
    else:
        return session_repository.get_multi(
            db, skip=skip, limit=limit
        )


@router.post("/{session_id}/task-completed", response_model=UserSession)
def record_task_completion(
    session_id: str,
    task_data: dict,
    db: Session = Depends(get_db)
):
    """Record a completed task for a session."""
    session = session_repository.get(db, session_id)
    if not session:
        raise ResourceNotFound("Session", session_id)
    
    # Increment tasks completed
    session = session_repository.increment_tasks_completed(db, session_id)
    
    # Update statistics
    stats = statistics_repository.get_by_session_id(db, session_id)
    if stats:
        statistics_repository.update_task_metrics(
            db,
            stats_id=stats.id,
            task_completed=True,
            task_type=task_data.get("task_type"),
            task_time_ms=task_data.get("time_spent_ms"),
            task_quality_score=task_data.get("quality_score")
        )
    
    return session


@router.post("/{session_id}/task-attempted", response_model=UserSession)
def record_task_attempt(
    session_id: str,
    task_data: dict,
    db: Session = Depends(get_db)
):
    """Record a task attempt for a session."""
    session = session_repository.get(db, session_id)
    if not session:
        raise ResourceNotFound("Session", session_id)
    
    # Increment tasks attempted
    session = session_repository.increment_tasks_attempted(db, session_id)
    
    # Update statistics
    stats = statistics_repository.get_by_session_id(db, session_id)
    if stats:
        statistics_repository.update_task_metrics(
            db,
            stats_id=stats.id,
            task_completed=False,
            task_type=task_data.get("task_type")
        )
    
    return session


@router.get("/{session_id}/task-compatibility", response_model=dict)
def get_task_compatibility(
    session_id: str,
    task_type: Optional[str] = None,
    task_complexity: Optional[int] = None,
    task_language: Optional[str] = None,
    task_category: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get compatibility score for a session and task."""
    session = session_repository.get(db, session_id)
    if not session:
        raise ResourceNotFound("Session", session_id)
    
    # Get statistics
    stats = statistics_repository.get_by_session_id(db, session_id)
    
    # Basic compatibility check - in a real implementation, this would be more sophisticated
    compatibility = {
        "overall_score": 0.0,
        "factors": {},
        "is_compatible": False
    }
    
    # Language compatibility
    language_score = 1.0 if not task_language or task_language == session.language else 0.3
    compatibility["factors"]["language"] = language_score
    
    # Expertise compatibility
    expertise_level = stats.expertise_level if stats else 0
    expertise_score = 1.0
    if task_complexity is not None:
        # Max complexity based on expertise level (0-4)
        max_complexity = expertise_level + 1  # Allow one level higher than current expertise
        if task_complexity > max_complexity:
            expertise_score = max(0.1, 1.0 - ((task_complexity - max_complexity) * 0.3))
    compatibility["factors"]["expertise"] = expertise_score
    
    # Overall score
    compatibility["overall_score"] = (language_score * 0.4) + (expertise_score * 0.6)
    compatibility["is_compatible"] = compatibility["overall_score"] >= 0.5
    
    return compatibility
