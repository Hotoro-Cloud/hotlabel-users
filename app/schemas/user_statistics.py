from datetime import datetime
from typing import Optional, Dict, List, Any
from pydantic import Field

from app.schemas.base import BaseSchema, TimestampedSchema, IDSchema


class UserStatisticsBase(BaseSchema):
    """Base schema for user statistics."""
    
    # Associated user ID (either session or profile)
    session_id: Optional[str] = Field(None, description="Associated session ID")
    profile_id: Optional[str] = Field(None, description="Associated profile ID")
    
    # General statistics
    total_tasks_completed: int = Field(0, description="Total tasks completed")
    total_tasks_attempted: int = Field(0, description="Total tasks attempted")
    completion_rate: float = Field(0.0, description="Percentage of tasks completed")
    success_rate: float = Field(0.0, description="Percentage of successful tasks")
    
    # Performance metrics
    average_task_time_ms: int = Field(0, description="Average task time in milliseconds")
    fastest_task_time_ms: int = Field(0, description="Fastest task time in milliseconds")
    slowest_task_time_ms: int = Field(0, description="Slowest task time in milliseconds")
    
    # Task breakdown
    task_type_distribution: Dict[str, int] = Field(
        default_factory=dict, 
        description="Distribution of tasks by type"
    )
    
    # Quality metrics
    average_quality_score: float = Field(0.0, description="Average quality score (0-1)")
    quality_distribution: Dict[str, int] = Field(
        default_factory=dict, 
        description="Distribution of tasks by quality score range"
    )
    
    # Expertise metrics
    expertise_level: int = Field(0, description="Expertise level (0-4)")
    expertise_areas: List[str] = Field(
        default_factory=list, 
        description="List of expertise area IDs"
    )
    
    # Time-based metrics
    active_days: int = Field(0, description="Number of active days")
    
    # Additional metrics
    engagement_score: float = Field(0.0, description="Engagement score (0-1)")
    consistency_score: float = Field(0.0, description="Consistency score (0-1)")


class UserStatisticsCreate(BaseSchema):
    """Schema for creating user statistics."""
    
    session_id: Optional[str] = None
    profile_id: Optional[str] = None


class UserStatisticsUpdate(BaseSchema):
    """Schema for updating user statistics."""
    
    total_tasks_completed: Optional[int] = None
    total_tasks_attempted: Optional[int] = None
    completion_rate: Optional[float] = None
    success_rate: Optional[float] = None
    average_task_time_ms: Optional[int] = None
    fastest_task_time_ms: Optional[int] = None
    slowest_task_time_ms: Optional[int] = None
    task_type_distribution: Optional[Dict[str, int]] = None
    average_quality_score: Optional[float] = None
    quality_distribution: Optional[Dict[str, int]] = None
    expertise_level: Optional[int] = None
    expertise_areas: Optional[List[str]] = None
    active_days: Optional[int] = None
    engagement_score: Optional[float] = None
    consistency_score: Optional[float] = None


class UserStatistics(IDSchema, UserStatisticsBase, TimestampedSchema):
    """Complete user statistics schema."""
    
    first_task_date: Optional[datetime] = Field(None, description="First task date")
    last_task_date: Optional[datetime] = Field(None, description="Last task date")


class UserStatisticsPeriod(BaseSchema):
    """Statistics for a specific time period."""
    
    period_start: datetime = Field(..., description="Period start date")
    period_end: datetime = Field(..., description="Period end date")
    tasks_completed: int = Field(0, description="Tasks completed in period")
    tasks_attempted: int = Field(0, description="Tasks attempted in period")
    success_rate: float = Field(0.0, description="Success rate in period")
    average_task_time_ms: int = Field(0, description="Average task time in period")
    quality_score: float = Field(0.0, description="Average quality score in period")
