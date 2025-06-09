from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr

from app.db.session import get_db
from app.db.repositories.user_session_repository import UserSessionRepository
from app.db.repositories.user_profile_repository import UserProfileRepository
from app.db.repositories.expertise_area_repository import ExpertiseAreaRepository
from app.core.exceptions import ResourceNotFound

# Request and response models
class UserCreate(BaseModel):
    email: EmailStr
    full_name: str
    is_active: bool = True
    is_superuser: bool = False
    password: str

class UserResponse(BaseModel):
    id: str
    email: EmailStr
    full_name: str
    is_active: bool
    is_superuser: bool

router = APIRouter(prefix="/users", tags=["users"])

# Initialize repositories
session_repository = UserSessionRepository()
profile_repository = UserProfileRepository()
expertise_repository = ExpertiseAreaRepository()

@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(
    user: UserCreate,
    db: Session = Depends(get_db)
):
    """Create a new user."""
    # Check if user with email already exists
    existing_user = profile_repository.get_by_email(db, user.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user profile
    user_data = user.dict()
    user_data.pop("password")  # Remove password from dict before creating profile
    new_user = profile_repository.create(db, obj_in=user_data)
    
    # In a real implementation, you would hash the password and store it securely
    # For this demo, we'll just store it as is (NOT recommended for production)
    new_user.password = user.password
    
    return new_user

@router.get("/search")
def search_users(
    query: str,
    search_type: str = "session",  # "session", "profile", or "all"
    db: Session = Depends(get_db)
):
    """Search for users across sessions and/or profiles."""
    results = []
    
    # Search sessions
    if search_type in ["session", "all"]:
        # In a real implementation, this would use a more sophisticated search
        # For the demo, we'll just do a simple filter
        sessions = session_repository.get_multi(db, skip=0, limit=100)
        for session in sessions:
            # Check for matches in various fields
            if (query.lower() in session.id.lower() or
                    (session.country and query.lower() in session.country.lower()) or
                    (session.language and query.lower() in session.language.lower())):
                results.append({
                    "id": session.id,
                    "type": "session",
                    "language": session.language,
                    "country": session.country,
                    "tasks_completed": session.tasks_completed,
                    "created_at": session.created_at
                })
    
    # Search profiles
    if search_type in ["profile", "all"]:
        profiles = profile_repository.get_multi(db, skip=0, limit=100)
        for profile in profiles:
            # Check for matches in various fields
            if (query.lower() in profile.id.lower() or
                    (profile.display_name and query.lower() in profile.display_name.lower()) or
                    (profile.primary_language and query.lower() in profile.primary_language.lower())):
                results.append({
                    "id": profile.id,
                    "type": "profile",
                    "display_name": profile.display_name,
                    "language": profile.primary_language,
                    "expertise_level": profile.expertise_level,
                    "tasks_completed": profile.tasks_completed,
                    "created_at": profile.created_at
                })
    
    return {"results": results, "count": len(results)}


@router.get("/task-compatibility")
def get_task_compatibility(
    user_id: str,
    task_type: Optional[str] = None,
    task_complexity: Optional[int] = None,
    task_language: Optional[str] = None,
    task_expertise: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get compatibility score for a user (session or profile) and task."""
    # Try to get as session first
    session = session_repository.get(db, user_id)
    if session:
        # Get user language from session
        user_language = session.language
        
        # Get user expertise level (simplified for demo)
        user_expertise_level = 0
        if session.tasks_completed >= 100:
            user_expertise_level = 4
        elif session.tasks_completed >= 50:
            user_expertise_level = 3
        elif session.tasks_completed >= 25:
            user_expertise_level = 2
        elif session.tasks_completed >= 10:
            user_expertise_level = 1
        
        user_type = "session"
    else:
        # Try as profile
        profile = profile_repository.get(db, user_id)
        if profile:
            # Get user language from profile
            user_language = profile.primary_language
            
            # Get user expertise level
            user_expertise_level = profile.expertise_level
            
            user_type = "profile"
        else:
            raise ResourceNotFound("User", user_id)
    
    # Basic compatibility check - in a real implementation, this would be more sophisticated
    compatibility = {
        "user_id": user_id,
        "user_type": user_type,
        "overall_score": 0.0,
        "factors": {},
        "is_compatible": False
    }
    
    # Language compatibility
    language_score = 1.0 if not task_language or task_language == user_language else 0.3
    compatibility["factors"]["language"] = language_score
    
    # Expertise compatibility
    expertise_score = 1.0
    if task_complexity is not None:
        # Max complexity based on expertise level (0-4)
        max_complexity = user_expertise_level + 1  # Allow one level higher than current expertise
        if task_complexity > max_complexity:
            expertise_score = max(0.1, 1.0 - ((task_complexity - max_complexity) * 0.3))
    compatibility["factors"]["expertise"] = expertise_score
    
    # Task type compatibility (simplified for demo)
    task_type_score = 1.0
    compatibility["factors"]["task_type"] = task_type_score
    
    # Overall score
    compatibility["overall_score"] = (
        (language_score * 0.4) + 
        (expertise_score * 0.4) + 
        (task_type_score * 0.2)
    )
    compatibility["is_compatible"] = compatibility["overall_score"] >= 0.5
    
    return compatibility


@router.get("/match-task")
def match_users_for_task(
    task_id: str,
    task_type: str,
    task_complexity: int = 0,
    task_language: Optional[str] = None,
    task_expertise: Optional[str] = None,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """Find users that match task requirements."""
    matches = []
    
    # Get all sessions and profiles
    sessions = session_repository.get_multi(db, skip=0, limit=500)
    profiles = profile_repository.get_multi(db, skip=0, limit=500)
    
    # Check sessions for matching
    for session in sessions:
        match_score = 0.0
        
        # Language compatibility
        if not task_language or session.language == task_language:
            match_score += 0.5
        
        # Expertise level (simplified)
        user_expertise_level = 0
        if session.tasks_completed >= 100:
            user_expertise_level = 4
        elif session.tasks_completed >= 50:
            user_expertise_level = 3
        elif session.tasks_completed >= 25:
            user_expertise_level = 2
        elif session.tasks_completed >= 10:
            user_expertise_level = 1
        
        if user_expertise_level >= task_complexity:
            match_score += 0.5
        
        # Add as a match if score is good
        if match_score >= 0.5:
            matches.append({
                "user_id": session.id,
                "user_type": "session",
                "match_score": match_score,
                "language": session.language,
                "expertise_level": user_expertise_level
            })
    
    # Check profiles for matching
    for profile in profiles:
        match_score = 0.0
        
        # Language compatibility
        if not task_language or profile.primary_language == task_language:
            match_score += 0.5
        
        # Expertise level
        if profile.expertise_level >= task_complexity:
            match_score += 0.5
        
        # Add as a match if score is good
        if match_score >= 0.5:
            matches.append({
                "user_id": profile.id,
                "user_type": "profile",
                "match_score": match_score,
                "language": profile.primary_language,
                "expertise_level": profile.expertise_level
            })
    
    # Sort by match score
    matches.sort(key=lambda x: x["match_score"], reverse=True)
    
    # Return top matches
    return {
        "task_id": task_id,
        "matches": matches[:limit],
        "total_matches": len(matches)
    }


@router.get("/detect-language")
def detect_language(
    text: str,
    db: Session = Depends(get_db)
):
    """Detect language of text (simplified implementation)."""
    # In a real implementation, this would use a proper language detection library
    # For the demo, we'll use a very simplified approach
    
    # Common words/patterns for a few languages
    language_patterns = {
        "en": ["the", "is", "and", "to", "of", "in", "that", "this"],
        "es": ["el", "la", "es", "y", "de", "en", "que", "para"],
        "fr": ["le", "la", "est", "et", "de", "en", "que", "pour"],
        "de": ["der", "die", "das", "ist", "und", "zu", "in", "mit"]
    }
    
    # Count matches for each language
    scores = {}
    text_lower = text.lower()
    for lang, patterns in language_patterns.items():
        score = sum(1 for pat in patterns if f" {pat} " in f" {text_lower} ")
        scores[lang] = score
    
    # Get the language with the highest score
    if not scores or max(scores.values()) == 0:
        # Default to English if no matches or empty text
        detected_language = "en"
        confidence = 0.5
    else:
        detected_language = max(scores, key=scores.get)
        confidence = 0.5 + (0.5 * (scores[detected_language] / len(language_patterns[detected_language])))
    
    return {
        "text": text[:50] + ("..." if len(text) > 50 else ""),
        "detected_language": detected_language,
        "confidence": confidence,
        "all_scores": scores
    }
