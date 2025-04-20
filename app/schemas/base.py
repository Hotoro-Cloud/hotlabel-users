from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class BaseSchema(BaseModel):
    """Base schema with common fields."""
    
    class Config:
        from_attributes = True
        populate_by_name = True


class TimestampedSchema(BaseSchema):
    """Schema with timestamp fields."""
    
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class IDSchema(BaseSchema):
    """Schema with ID field."""
    
    id: str = Field(..., description="Unique identifier")
