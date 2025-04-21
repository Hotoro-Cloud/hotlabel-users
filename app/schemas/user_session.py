from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import Field

from app.schemas.base import BaseSchema, TimestampedSchema, IDSchema


class UserSessionBase(BaseSchema):
    """Base schema for user session data."""
    
    # Publisher data
    publisher_id: str = Field(..., description="Publisher ID")
    
    # Browser data
    browser_fingerprint: Optional[str] = Field(None, description="Anonymized browser fingerprint")
    user_agent: Optional[str] = Field(None, description="User agent string")
    language: Optional[str] = Field(None, description="Browser language")
    timezone: Optional[str] = Field(None, description="User timezone")
    
    # Session metadata
    referrer: Optional[str] = Field(None, description="Referring URL")
    country: Optional[str] = Field(None, description="User country code")
    device_type: Optional[str] = Field(None, description="Device type (mobile, desktop, tablet)")
    platform: Optional[str] = Field(None, description="Operating system")
    
    # Privacy and consent
    consent_given: bool = Field(False, description="Whether user consent has been given")
    analytics_opt_in: bool = Field(False, description="Whether analytics consent has been given")
    personalization_opt_in: bool = Field(False, description="Whether personalization consent has been given")
    
    # Additional data
    session_metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional session data")


class UserSessionCreate(UserSessionBase):
    """Schema for creating a new user session."""
    pass


class UserSessionUpdate(BaseSchema):
    """Schema for updating a user session."""
    
    browser_fingerprint: Optional[str] = None
    user_agent: Optional[str] = None
    language: Optional[str] = None
    timezone: Optional[str] = None
    referrer: Optional[str] = None
    country: Optional[str] = None
    device_type: Optional[str] = None
    platform: Optional[str] = None
    consent_given: Optional[bool] = None
    analytics_opt_in: Optional[bool] = None
    personalization_opt_in: Optional[bool] = None
    session_metadata: Optional[Dict[str, Any]] = None
    tasks_completed: Optional[int] = None
    tasks_attempted: Optional[int] = None
    profile_id: Optional[str] = None


class UserSession(IDSchema, UserSessionBase, TimestampedSchema):
    """Complete user session schema."""
    
    last_active: datetime = Field(..., description="Last active timestamp")
    tasks_completed: int = Field(0, description="Number of tasks completed")
    tasks_attempted: int = Field(0, description="Number of tasks attempted")
    profile_id: Optional[str] = Field(None, description="Associated expert profile ID if opt-in")


class UserSessionWithStats(UserSession):
    """User session with statistics."""
    
    success_rate: Optional[float] = Field(None, description="Task success rate")
    average_task_time_ms: Optional[int] = Field(None, description="Average task completion time")
    expertise_level: Optional[int] = Field(None, description="Expertise level (0-4)")
