from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.repositories.expertise_area_repository import ExpertiseAreaRepository
from app.schemas.expertise_area import (
    ExpertiseArea,
    ExpertiseAreaCreate,
    ExpertiseAreaUpdate,
    ExpertiseAreaWithChildren,
    ExpertiseAreaTree
)
from app.core.exceptions import ResourceNotFound, ConflictError

router = APIRouter(prefix="/expertise-areas", tags=["expertise-areas"])

# Initialize repository
expertise_repository = ExpertiseAreaRepository()


@router.post("", response_model=ExpertiseArea, status_code=status.HTTP_201_CREATED)
def create_expertise_area(
    area_data: ExpertiseAreaCreate,
    db: Session = Depends(get_db)
):
    """Create a new expertise area."""
    # Check if slug is unique
    if area_data.slug:
        existing_area = expertise_repository.get_by_slug(db, area_data.slug)
        if existing_area:
            raise ConflictError(f"An expertise area with slug '{area_data.slug}' already exists")
    
    # Check if name is unique
    existing_area = expertise_repository.get_by_name(db, area_data.name)
    if existing_area:
        raise ConflictError(f"An expertise area with name '{area_data.name}' already exists")
    
    # Check if parent exists
    if area_data.parent_id:
        parent = expertise_repository.get(db, area_data.parent_id)
        if not parent:
            raise ResourceNotFound("Parent expertise area", area_data.parent_id)
    
    # Create area with generated slug if needed
    return expertise_repository.create_with_slug(db, obj_in=area_data)


@router.get("/{area_id}", response_model=ExpertiseArea)
def get_expertise_area(
    area_id: str,
    db: Session = Depends(get_db)
):
    """Get an expertise area by ID."""
    area = expertise_repository.get(db, area_id)
    if not area:
        raise ResourceNotFound("Expertise area", area_id)
    
    return area


@router.get("/slug/{slug}", response_model=ExpertiseArea)
def get_expertise_area_by_slug(
    slug: str,
    db: Session = Depends(get_db)
):
    """Get an expertise area by slug."""
    area = expertise_repository.get_by_slug(db, slug)
    if not area:
        raise ResourceNotFound("Expertise area", f"with slug '{slug}'")
    
    return area


@router.patch("/{area_id}", response_model=ExpertiseArea)
def update_expertise_area(
    area_id: str,
    area_data: ExpertiseAreaUpdate,
    db: Session = Depends(get_db)
):
    """Update an expertise area."""
    # Check if area exists
    area = expertise_repository.get(db, area_id)
    if not area:
        raise ResourceNotFound("Expertise area", area_id)
    
    # Check if updating to a duplicate slug
    if area_data.slug and area_data.slug != area.slug:
        existing_area = expertise_repository.get_by_slug(db, area_data.slug)
        if existing_area and existing_area.id != area_id:
            raise ConflictError(f"An expertise area with slug '{area_data.slug}' already exists")
    
    # Check if updating to a duplicate name
    if area_data.name and area_data.name != area.name:
        existing_area = expertise_repository.get_by_name(db, area_data.name)
        if existing_area and existing_area.id != area_id:
            raise ConflictError(f"An expertise area with name '{area_data.name}' already exists")
    
    # Check if parent exists
    if area_data.parent_id and area_data.parent_id != area.parent_id:
        if area_data.parent_id == area_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="An expertise area cannot be its own parent"
            )
        
        parent = expertise_repository.get(db, area_data.parent_id)
        if not parent:
            raise ResourceNotFound("Parent expertise area", area_data.parent_id)
    
    # Update area
    return expertise_repository.update(
        db, db_obj=area, obj_in=area_data
    )


@router.delete("/{area_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_expertise_area(
    area_id: str,
    db: Session = Depends(get_db)
):
    """Delete an expertise area."""
    # Check if area exists
    area = expertise_repository.get(db, area_id)
    if not area:
        raise ResourceNotFound("Expertise area", area_id)
    
    # Check if area has children
    children = expertise_repository.get_children(db, area_id)
    if children:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete an expertise area with children"
        )
    
    # Delete area
    expertise_repository.remove(db, id=area_id)
    return None


@router.get("", response_model=List[ExpertiseArea])
def list_expertise_areas(
    parent_id: Optional[str] = None,
    active_only: bool = True,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """List expertise areas, optionally filtered by parent or active status."""
    if parent_id:
        # Check if parent exists
        parent = expertise_repository.get(db, parent_id)
        if not parent:
            raise ResourceNotFound("Parent expertise area", parent_id)
        
        # Get children
        children = expertise_repository.get_children(db, parent_id)
        if active_only:
            children = [c for c in children if c.is_active]
        
        # Apply pagination
        return children[skip:skip+limit]
    
    if active_only:
        return expertise_repository.get_active(db, skip=skip, limit=limit)
    else:
        return expertise_repository.get_multi(db, skip=skip, limit=limit)


@router.get("/tree", response_model=ExpertiseAreaTree)
def get_expertise_area_tree(
    active_only: bool = True,
    db: Session = Depends(get_db)
):
    """Get the full expertise area tree."""
    tree = expertise_repository.get_full_tree(db)
    
    # Filter for active areas if needed
    if active_only:
        def filter_active(areas):
            result = []
            for area in areas:
                if area["is_active"]:
                    # Also filter children
                    area["children"] = filter_active(area["children"])
                    result.append(area)
            return result
        
        tree["areas"] = filter_active(tree["areas"])
    
    return tree


@router.get("/{area_id}/path", response_model=List[ExpertiseArea])
def get_path_to_root(
    area_id: str,
    db: Session = Depends(get_db)
):
    """Get the path from an expertise area to the root."""
    # Check if area exists
    area = expertise_repository.get(db, area_id)
    if not area:
        raise ResourceNotFound("Expertise area", area_id)
    
    # Get path
    return expertise_repository.get_path_to_root(db, area_id)


@router.get("/{area_id}/users-count", response_model=dict)
def get_users_count(
    area_id: str,
    db: Session = Depends(get_db)
):
    """Get the number of users with this expertise area."""
    # Check if area exists
    area = expertise_repository.get(db, area_id)
    if not area:
        raise ResourceNotFound("Expertise area", area_id)
    
    # Get count
    count = expertise_repository.count_users_by_area(db, area_id)
    
    return {
        "expertise_area_id": area_id,
        "name": area.name,
        "users_count": count
    }
