from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import Field, EmailStr

from app.schemas.base import BaseSchema, TimestampedSchema, IDSchema


class UserProfileBase(BaseSchema):
    """Base schema for user profile data."""
    
    # Basic profile information
    display_name: Optional[str] = Field(None, description="Display name for the user")
    primary_language: Optional[str] = Field(None, description="Primary language code")
    additional_languages: Optional[List[str]] = Field(default_factory=list, description="Additional language codes")
    timezone: Optional[str] = Field(None, description="User timezone")
    
    # Preferences
    notification_preferences: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Notification settings")
    privacy_settings: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Privacy settings")
    
    # Additional data
    profile_metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional profile data")


class UserProfileCreate(UserProfileBase):
    """Schema for creating a new user profile."""
    
    email: EmailStr = Field(..., description="User email")
    session_id: str = Field(..., description="Associated session ID")


class UserProfileUpdate(BaseSchema):
    """Schema for updating a user profile."""
    
    display_name: Optional[str] = None
    email: Optional[EmailStr] = None
    primary_language: Optional[str] = None
    additional_languages: Optional[List[str]] = None
    timezone: Optional[str] = None
    notification_preferences: Optional[Dict[str, Any]] = None
    privacy_settings: Optional[Dict[str, Any]] = None
    profile_metadata: Optional[Dict[str, Any]] = None
    expertise_areas: Optional[List[str]] = None


class UserProfile(IDSchema, UserProfileBase, TimestampedSchema):
    """Complete user profile schema."""
    
    email_hash: Optional[str] = Field(None, description="Hashed email for identification")
    expertise_level: int = Field(0, description="Expertise level (0-4)")
    verified: bool = Field(False, description="Whether the user is a verified expert")
    last_active: datetime = Field(..., description="Last active timestamp")
    tasks_completed: int = Field(0, description="Total tasks completed")
    quality_score: int = Field(0, description="Quality score (0-100)")
    expertise_areas: List[str] = Field(default_factory=list, description="List of expertise area IDs")


class UserProfileWithStats(UserProfile):
    """User profile with additional statistics."""
    
    success_rate: Optional[float] = Field(None, description="Task success rate")
    average_task_time_ms: Optional[int] = Field(None, description="Average task completion time")
    session_count: Optional[int] = Field(None, description="Number of associated sessions")
    active_days: Optional[int] = Field(None, description="Number of active days")
    first_activity: Optional[datetime] = Field(None, description="Date of first activity")
    engagement_score: Optional[float] = Field(None, description="Engagement score")
    consistency_score: Optional[float] = Field(None, description="Consistency score")
