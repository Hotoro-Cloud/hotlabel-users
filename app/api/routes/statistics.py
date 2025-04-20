from typing import List, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.repositories.user_statistics_repository import UserStatisticsRepository
from app.db.repositories.user_session_repository import UserSessionRepository
from app.db.repositories.user_profile_repository import UserProfileRepository
from app.db.repositories.expertise_area_repository import ExpertiseAreaRepository
from app.schemas.user_statistics import (
    UserStatistics,
    UserStatisticsUpdate,
    UserStatisticsPeriod
)
from app.core.exceptions import ResourceNotFound

router = APIRouter(prefix="/statistics", tags=["statistics"])

# Initialize repositories
statistics_repository = UserStatisticsRepository()
session_repository = UserSessionRepository()
profile_repository = UserProfileRepository()
expertise_repository = ExpertiseAreaRepository()


@router.get("/session/{session_id}", response_model=UserStatistics)
def get_session_statistics(
    session_id: str,
    db: Session = Depends(get_db)
):
    """Get statistics for a specific session."""
    # Check if session exists
    session = session_repository.get(db, session_id)
    if not session:
        raise ResourceNotFound("Session", session_id)
    
    # Get statistics
    stats = statistics_repository.get_by_session_id(db, session_id)
    if not stats:
        # Create statistics if they don't exist
        stats = statistics_repository.create_for_session(db, session_id)
    
    return stats


@router.get("/profile/{profile_id}", response_model=UserStatistics)
def get_profile_statistics(
    profile_id: str,
    db: Session = Depends(get_db)
):
    """Get statistics for a specific profile."""
    # Check if profile exists
    profile = profile_repository.get(db, profile_id)
    if not profile:
        raise ResourceNotFound("Profile", profile_id)
    
    # Get statistics
    stats = statistics_repository.get_by_profile_id(db, profile_id)
    if not stats:
        # Create statistics if they don't exist
        stats = statistics_repository.create_for_profile(db, profile_id)
    
    return stats


@router.patch("/session/{session_id}", response_model=UserStatistics)
def update_session_statistics(
    session_id: str,
    stats_data: UserStatisticsUpdate,
    db: Session = Depends(get_db)
):
    """Update statistics for a session."""
    # Check if session exists
    session = session_repository.get(db, session_id)
    if not session:
        raise ResourceNotFound("Session", session_id)
    
    # Get statistics
    stats = statistics_repository.get_by_session_id(db, session_id)
    if not stats:
        # Create statistics if they don't exist
        stats = statistics_repository.create_for_session(db, session_id)
    
    # Update statistics
    return statistics_repository.update(
        db, db_obj=stats, obj_in=stats_data
    )


@router.patch("/profile/{profile_id}", response_model=UserStatistics)
def update_profile_statistics(
    profile_id: str,
    stats_data: UserStatisticsUpdate,
    db: Session = Depends(get_db)
):
    """Update statistics for a profile."""
    # Check if profile exists
    profile = profile_repository.get(db, profile_id)
    if not profile:
        raise ResourceNotFound("Profile", profile_id)
    
    # Get statistics
    stats = statistics_repository.get_by_profile_id(db, profile_id)
    if not stats:
        # Create statistics if they don't exist
        stats = statistics_repository.create_for_profile(db, profile_id)
    
    # Update statistics
    return statistics_repository.update(
        db, db_obj=stats, obj_in=stats_data
    )


@router.get("/publishers/{publisher_id}/summary", response_model=dict)
def get_publisher_statistics(
    publisher_id: str,
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db)
):
    """Get summary statistics for a publisher."""
    # Calculate date range
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    # Count sessions for this publisher
    session_count = session_repository.count_by_publisher(db, publisher_id)
    
    # For demonstration purposes, we're using simple aggregation
    # In a real implementation, this would involve more complex queries
    
    # Get active sessions for this publisher in the date range
    active_sessions = session_repository.get_by_publisher_id(db, publisher_id)
    active_sessions = [s for s in active_sessions if s.last_active and s.last_active >= start_date]
    
    # Get task counts
    total_tasks_completed = sum(s.tasks_completed for s in active_sessions)
    total_tasks_attempted = sum(s.tasks_attempted for s in active_sessions)
    
    # Calculate completion rate
    completion_rate = 0
    if total_tasks_attempted > 0:
        completion_rate = total_tasks_completed / total_tasks_attempted
    
    # Calculate consent metrics
    consent_given_count = len([s for s in active_sessions if s.consent_given])
    consent_rate = 0
    if active_sessions:
        consent_rate = consent_given_count / len(active_sessions)
    
    # Return summary statistics
    return {
        "publisher_id": publisher_id,
        "period": {
            "start": start_date,
            "end": end_date,
            "days": days
        },
        "session_metrics": {
            "total_sessions": session_count,
            "active_sessions": len(active_sessions),
            "consent_given_count": consent_given_count,
            "consent_rate": consent_rate
        },
        "task_metrics": {
            "total_tasks_completed": total_tasks_completed,
            "total_tasks_attempted": total_tasks_attempted,
            "completion_rate": completion_rate
        }
    }


@router.get("/expertise-areas", response_model=List[dict])
def get_expertise_area_statistics(
    db: Session = Depends(get_db)
):
    """Get statistics for expertise areas."""
    # Get expertise areas with user counts
    return expertise_repository.get_areas_with_user_counts(db)


@router.get("/sessions/time-periods", response_model=List[UserStatisticsPeriod])
def get_session_statistics_by_period(
    session_id: str,
    period: str = Query("day", enum=["day", "week", "month"]),
    count: int = Query(7, ge=1, le=30),
    db: Session = Depends(get_db)
):
    """Get statistics for a session broken down by time periods."""
    # Check if session exists
    session = session_repository.get(db, session_id)
    if not session:
        raise ResourceNotFound("Session", session_id)
    
    # Get statistics
    stats = statistics_repository.get_by_session_id(db, session_id)
    if not stats:
        raise ResourceNotFound("Statistics", f"for session {session_id}")
    
    # For demonstration purposes, we're generating sample data
    # In a real implementation, this would involve more complex queries
    
    # Calculate date range
    end_date = datetime.utcnow()
    
    # Determine period duration
    if period == "day":
        delta = timedelta(days=1)
    elif period == "week":
        delta = timedelta(weeks=1)
    else:  # month
        delta = timedelta(days=30)
    
    # Generate periods
    periods = []
    for i in range(count):
        period_end = end_date - (i * delta)
        period_start = period_end - delta
        
        # Sample data for demonstration
        periods.append(
            UserStatisticsPeriod(
                period_start=period_start,
                period_end=period_end,
                tasks_completed=int(stats.total_tasks_completed / count),
                tasks_attempted=int(stats.total_tasks_attempted / count),
                success_rate=stats.success_rate,
                average_task_time_ms=stats.average_task_time_ms,
                quality_score=stats.average_quality_score
            )
        )
    
    return periods


@router.get("/global/averages", response_model=dict)
def get_global_statistics(
    db: Session = Depends(get_db)
):
    """Get global platform statistics averages."""
    # For demonstration purposes, we're using sample data
    # In a real implementation, this would involve complex aggregation queries
    
    # Get all statistics
    session_stats = db.query(statistics_repository.model).filter(
        statistics_repository.model.session_id.isnot(None)
    ).all()
    
    profile_stats = db.query(statistics_repository.model).filter(
        statistics_repository.model.profile_id.isnot(None)
    ).all()
    
    # Calculate averages
    avg_completion_rate = sum(s.completion_rate for s in session_stats + profile_stats) / max(1, len(session_stats) + len(profile_stats))
    avg_success_rate = sum(s.success_rate for s in session_stats + profile_stats) / max(1, len(session_stats) + len(profile_stats))
    avg_task_time = sum(s.average_task_time_ms for s in session_stats + profile_stats) / max(1, len(session_stats) + len(profile_stats))
    avg_quality = sum(s.average_quality_score for s in session_stats + profile_stats) / max(1, len(session_stats) + len(profile_stats))
    
    # Return global averages
    return {
        "averages": {
            "completion_rate": avg_completion_rate,
            "success_rate": avg_success_rate,
            "average_task_time_ms": avg_task_time,
            "average_quality_score": avg_quality
        },
        "counts": {
            "total_sessions": len(session_stats),
            "total_profiles": len(profile_stats),
            "total_users": len(session_stats) + len(profile_stats)
        }
    }


@router.get("/task-compatibility-metrics", response_model=dict)
def get_task_compatibility_metrics(
    db: Session = Depends(get_db)
):
    """Get metrics on task compatibility across the platform."""
    # For demonstration purposes, using sample data
    # In a real implementation, this would involve complex queries
    
    # Return sample compatibility metrics
    return {
        "overall_compatibility": 0.78,
        "compatibility_by_expertise_level": {
            "level_0": 0.95,
            "level_1": 0.85,
            "level_2": 0.75,
            "level_3": 0.65,
            "level_4": 0.55
        },
        "compatibility_by_language": {
            "en": 0.92,
            "fr": 0.85,
            "es": 0.80,
            "de": 0.75,
            "other": 0.60
        },
        "task_type_distribution": {
            "vqa": 45,
            "text_classification": 30,
            "text_generation": 15,
            "other": 10
        }
    }
