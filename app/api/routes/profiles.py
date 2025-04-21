from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import hashlib

from app.db.session import get_db
from app.db.repositories.user_profile_repository import UserProfileRepository
from app.db.repositories.user_session_repository import UserSessionRepository
from app.db.repositories.user_statistics_repository import UserStatisticsRepository
from app.db.repositories.expertise_area_repository import ExpertiseAreaRepository
from app.schemas.user_profile import (
    UserProfile,
    UserProfileCreate,
    UserProfileUpdate,
    UserProfileWithStats
)
from app.core.exceptions import ResourceNotFound, BadRequest

router = APIRouter(prefix="/profiles", tags=["profiles"])

# Initialize repositories
profile_repository = UserProfileRepository()
session_repository = UserSessionRepository()
statistics_repository = UserStatisticsRepository()
expertise_repository = ExpertiseAreaRepository()


@router.post("", response_model=UserProfile, status_code=status.HTTP_201_CREATED)
def create_profile(
    profile_data: UserProfileCreate,
    db: Session = Depends(get_db)
):
    """Create a new user profile (opt-in to expert network)."""
    # Check if session exists
    session = session_repository.get(db, profile_data.session_id)
    if not session:
        raise ResourceNotFound("Session", profile_data.session_id)
    
    # Hash email for storage
    email_hash = hashlib.sha256(profile_data.email.encode()).hexdigest()
    
    # Check if profile with this email already exists
    existing_profile = profile_repository.get_by_email_hash(db, email_hash)
    if existing_profile:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A profile with this email already exists"
        )
    
    # Prepare profile data
    profile_dict = profile_data.model_dump()
    profile_dict["email_hash"] = email_hash

    # Create profile
    profile = profile_repository.create(db, obj_in=UserProfileCreate(**profile_dict))
    
    # Associate session with profile
    session_repository.update(
        db, db_obj=session, obj_in={"profile_id": profile.id}
    )
    
    # Create statistics for profile
    statistics_repository.create_for_profile(db, profile_id=profile.id)
    
    return profile


@router.get("/{profile_id}", response_model=UserProfile)
def get_profile(
    profile_id: str,
    db: Session = Depends(get_db)
):
    """Get a user profile by ID."""
    profile = profile_repository.get(db, profile_id)
    if not profile:
        raise ResourceNotFound("Profile", profile_id)
    
    # Update last active timestamp
    profile_repository.update_last_active(db, profile_id)
    
    return profile


@router.patch("/{profile_id}", response_model=UserProfile)
def update_profile(
    profile_id: str,
    profile_data: UserProfileUpdate,
    db: Session = Depends(get_db)
):
    """Update a user profile."""
    profile = profile_repository.get(db, profile_id)
    if not profile:
        raise ResourceNotFound("Profile", profile_id)
    
    # Handle email update if provided
    if profile_data.email:
        # Hash new email
        email_hash = hashlib.sha256(profile_data.email.encode()).hexdigest()
        
        # Check if another profile already has this email
        existing_profile = profile_repository.get_by_email_hash(db, email_hash)
        if existing_profile and existing_profile.id != profile_id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A profile with this email already exists"
            )
        
        # Update email hash
        profile_data_dict = profile_data.model_dump(exclude={"email"})
        profile_data_dict["email_hash"] = email_hash
        profile_data = UserProfileUpdate(**profile_data_dict)
    
    # Update expertise areas if provided
    expertise_areas = profile_data.expertise_areas
    if expertise_areas is not None:
        # Validate expertise areas
        for area_id in expertise_areas:
            if not expertise_repository.exists(db, area_id):
                raise ResourceNotFound("Expertise area", area_id)
        
        # Update profile statistics
        stats = statistics_repository.get_by_profile_id(db, profile_id)
        if stats:
            statistics_repository.update_expertise_areas(db, stats.id, expertise_areas)
    
    return profile_repository.update(
        db, db_obj=profile, obj_in=profile_data
    )


@router.delete("/{profile_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_profile(
    profile_id: str,
    db: Session = Depends(get_db)
):
    """Delete a user profile."""
    profile = profile_repository.get(db, profile_id)
    if not profile:
        raise ResourceNotFound("Profile", profile_id)
    
    # Remove profile_id from associated sessions
    associated_sessions = session_repository.get_by_profile_id(db, profile_id)
    for session in associated_sessions:
        session_repository.update(
            db, db_obj=session, obj_in={"profile_id": None}
        )
    
    profile_repository.remove(db, id=profile_id)
    return None


@router.get("/{profile_id}/stats", response_model=UserProfileWithStats)
def get_profile_statistics(
    profile_id: str,
    db: Session = Depends(get_db)
):
    """Get detailed statistics for a profile."""
    profile = profile_repository.get(db, profile_id)
    if not profile:
        raise ResourceNotFound("Profile", profile_id)
    
    # Get statistics
    stats = statistics_repository.get_by_profile_id(db, profile_id)
    if not stats:
        # Create statistics if they don't exist
        stats = statistics_repository.create_for_profile(db, profile_id)
    
    # Get session count
    session_count = len(session_repository.get_by_profile_id(db, profile_id))
    
    # Combine profile with stats
    profile_dict = {
        **profile.__dict__,
        "success_rate": stats.success_rate,
        "average_task_time_ms": stats.average_task_time_ms,
        "session_count": session_count,
        "active_days": stats.active_days,
        "first_activity": stats.first_task_date,
        "engagement_score": stats.engagement_score,
        "consistency_score": stats.consistency_score
    }
    
    return profile_dict


@router.get("", response_model=List[UserProfile])
def list_profiles(
    expertise_level: Optional[int] = None,
    expertise_area: Optional[str] = None,
    verified: Optional[bool] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """List user profiles, optionally filtered."""
    if expertise_level is not None:
        return profile_repository.get_by_expertise_level(
            db, level=expertise_level, skip=skip, limit=limit
        )
    elif expertise_area:
        return profile_repository.get_by_expertise_area(
            db, expertise_area_id=expertise_area, skip=skip, limit=limit
        )
    elif verified is not None:
        if verified:
            return profile_repository.get_verified_profiles(
                db, skip=skip, limit=limit
            )
        else:
            # Filter for non-verified profiles
            profiles = profile_repository.get_multi(db, skip=skip, limit=limit)
            return [p for p in profiles if not p.verified]
    else:
        return profile_repository.get_multi(
            db, skip=skip, limit=limit
        )


@router.post("/{profile_id}/task-completed", response_model=UserProfile)
def record_task_completion(
    profile_id: str,
    task_data: dict,
    db: Session = Depends(get_db)
):
    """Record a completed task for a profile."""
    profile = profile_repository.get(db, profile_id)
    if not profile:
        raise ResourceNotFound("Profile", profile_id)
    
    # Increment tasks completed
    profile = profile_repository.increment_tasks_completed(db, profile_id)
    
    # Update statistics
    stats = statistics_repository.get_by_profile_id(db, profile_id)
    if stats:
        statistics_repository.update_task_metrics(
            db,
            stats_id=stats.id,
            task_completed=True,
            task_type=task_data.get("task_type"),
            task_time_ms=task_data.get("time_spent_ms"),
            task_quality_score=task_data.get("quality_score")
        )
    
    return profile


@router.post("/{profile_id}/verify", response_model=UserProfile)
def verify_profile(
    profile_id: str,
    db: Session = Depends(get_db)
):
    """Verify a user profile as an expert."""
    profile = profile_repository.get(db, profile_id)
    if not profile:
        raise ResourceNotFound("Profile", profile_id)
    
    # Check if profile has enough tasks completed
    if profile.tasks_completed < 50:
        raise BadRequest("Profile must have completed at least 50 tasks to be verified")
    
    # Update verified status
    profile = profile_repository.update(
        db, db_obj=profile, obj_in={"verified": True}
    )
    
    return profile


@router.get("/top-contributors", response_model=List[UserProfile])
def get_top_contributors(
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """Get top contributors based on tasks completed."""
    return profile_repository.get_top_contributors(db, limit=limit)
