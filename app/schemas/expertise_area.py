from typing import Optional, List
from pydantic import Field

from app.schemas.base import BaseSchema, TimestampedSchema, IDSchema


class ExpertiseAreaBase(BaseSchema):
    """Base schema for expertise areas."""
    
    name: str = Field(..., description="Name of the expertise area")
    slug: str = Field(..., description="URL-friendly slug")
    description: Optional[str] = Field(None, description="Description of the expertise area")
    parent_id: Optional[str] = Field(None, description="Parent expertise area ID")
    is_active: bool = Field(True, description="Whether the expertise area is active")


class ExpertiseAreaCreate(ExpertiseAreaBase):
    """Schema for creating a new expertise area."""
    pass


class ExpertiseAreaUpdate(BaseSchema):
    """Schema for updating an expertise area."""
    
    name: Optional[str] = None
    slug: Optional[str] = None
    description: Optional[str] = None
    parent_id: Optional[str] = None
    is_active: Optional[bool] = None


class ExpertiseArea(IDSchema, ExpertiseAreaBase, TimestampedSchema):
    """Complete expertise area schema."""
    
    # No additional fields


class ExpertiseAreaWithChildren(ExpertiseArea):
    """Expertise area with children."""
    
    children: List["ExpertiseAreaWithChildren"] = Field(default_factory=list, description="Child expertise areas")


# Solve forward reference
ExpertiseAreaWithChildren.model_rebuild()


class ExpertiseAreaTree(BaseSchema):
    """Tree of expertise areas."""
    
    areas: List[ExpertiseAreaWithChildren] = Field(default_factory=list, description="Top-level expertise areas")


class ExpertiseAreaStatsBase(BaseSchema):
    """Base schema for expertise area statistics."""
    
    expertise_area_id: str = Field(..., description="Expertise area ID")
    user_count: int = Field(0, description="Number of users with this expertise")
    task_count: int = Field(0, description="Number of tasks completed in this area")
    average_quality: float = Field(0.0, description="Average quality of tasks in this area")


class ExpertiseAreaStats(ExpertiseAreaStatsBase, IDSchema, TimestampedSchema):
    """Complete expertise area statistics schema."""
    
    # No additional fields
