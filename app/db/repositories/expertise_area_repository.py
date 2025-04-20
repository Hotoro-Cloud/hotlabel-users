from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.db.repositories.base import BaseRepository
from app.models.expertise_area import ExpertiseArea
from app.schemas.expertise_area import ExpertiseAreaCreate, ExpertiseAreaUpdate


class ExpertiseAreaRepository(BaseRepository[ExpertiseArea, ExpertiseAreaCreate, ExpertiseAreaUpdate]):
    """Repository for expertise area operations."""
    
    def __init__(self):
        super().__init__(ExpertiseArea)
    
    def get_by_slug(self, db: Session, slug: str) -> Optional[ExpertiseArea]:
        """Get an expertise area by slug."""
        return db.query(self.model).filter(self.model.slug == slug).first()
    
    def get_by_name(self, db: Session, name: str) -> Optional[ExpertiseArea]:
        """Get an expertise area by name."""
        return db.query(self.model).filter(func.lower(self.model.name) == func.lower(name)).first()
    
    def get_children(self, db: Session, parent_id: str) -> List[ExpertiseArea]:
        """Get child expertise areas for a parent."""
        return db.query(self.model).filter(self.model.parent_id == parent_id).all()
    
    def get_top_level(self, db: Session) -> List[ExpertiseArea]:
        """Get top-level expertise areas (no parent)."""
        return db.query(self.model).filter(self.model.parent_id == None).all()
    
    def get_active(
        self, db: Session, skip: int = 0, limit: int = 100
    ) -> List[ExpertiseArea]:
        """Get active expertise areas."""
        return db.query(self.model).filter(
            self.model.is_active == True
        ).offset(skip).limit(limit).all()
    
    def get_full_tree(self, db: Session) -> Dict[str, Any]:
        """Get the full expertise area tree."""
        # Get top level areas
        top_level = self.get_top_level(db)
        result = []
        
        # Recursively build the tree
        for area in top_level:
            result.append(self._build_tree_node(db, area))
        
        return {"areas": result}
    
    def _build_tree_node(self, db: Session, area: ExpertiseArea) -> Dict[str, Any]:
        """Build a tree node for an expertise area with its children."""
        # Get children
        children = self.get_children(db, area.id)
        
        # Convert to dict
        area_dict = {
            "id": area.id,
            "name": area.name,
            "slug": area.slug,
            "description": area.description,
            "is_active": area.is_active,
            "created_at": area.created_at,
            "updated_at": area.updated_at,
            "children": []
        }
        
        # Add children recursively
        for child in children:
            area_dict["children"].append(self._build_tree_node(db, child))
        
        return area_dict
    
    def count_users_by_area(self, db: Session, area_id: str) -> int:
        """Count users with a specific expertise area."""
        from app.models.user_profile import UserProfile, profile_expertise_table
        
        return db.query(func.count(profile_expertise_table.c.profile_id)).filter(
            profile_expertise_table.c.expertise_id == area_id
        ).scalar()
    
    def get_areas_with_user_counts(self, db: Session) -> List[Dict[str, Any]]:
        """Get all expertise areas with user counts."""
        from app.models.user_profile import profile_expertise_table
        
        # Query for areas with user counts
        result = db.query(
            self.model,
            func.count(profile_expertise_table.c.profile_id).label("user_count")
        ).outerjoin(
            profile_expertise_table,
            self.model.id == profile_expertise_table.c.expertise_id
        ).group_by(
            self.model.id
        ).all()
        
        # Format result
        return [
            {
                "id": area.id,
                "name": area.name,
                "slug": area.slug,
                "user_count": user_count
            }
            for area, user_count in result
        ]
    
    def create_slug(self, name: str) -> str:
        """Create a URL-friendly slug from a name."""
        import re
        
        # Convert to lowercase and replace spaces with hyphens
        slug = name.lower().strip().replace(' ', '-')
        
        # Remove special characters
        slug = re.sub(r'[^a-z0-9\-]', '', slug)
        
        # Replace multiple hyphens with a single one
        slug = re.sub(r'\-+', '-', slug)
        
        return slug
    
    def create_with_slug(
        self, db: Session, obj_in: ExpertiseAreaCreate
    ) -> ExpertiseArea:
        """Create a new expertise area with a generated slug."""
        # Generate slug if not provided
        if not obj_in.slug:
            obj_in.slug = self.create_slug(obj_in.name)
        
        return self.create(db, obj_in=obj_in)
    
    def get_path_to_root(self, db: Session, area_id: str) -> List[ExpertiseArea]:
        """Get the path from an expertise area to the root."""
        area = self.get(db, area_id)
        if not area:
            return []
        
        result = [area]
        current = area
        
        # Traverse up the tree until we reach the root
        while current.parent_id:
            parent = self.get(db, current.parent_id)
            if not parent:
                break
            
            result.insert(0, parent)
            current = parent
        
        return result
