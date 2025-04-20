import logging
from typing import Dict, List, Any, Optional, Tuple
from sqlalchemy.orm import Session

from app.db.repositories.user_session_repository import UserSessionRepository
from app.db.repositories.user_profile_repository import UserProfileRepository
from app.db.repositories.user_statistics_repository import UserStatisticsRepository
from app.db.repositories.expertise_area_repository import ExpertiseAreaRepository
from app.core.config import settings

logger = logging.getLogger(__name__)


class TaskCompatibilityService:
    """Service for task-user compatibility and the staircase model."""
    
    def __init__(
        self,
        session_repository: UserSessionRepository,
        profile_repository: UserProfileRepository,
        statistics_repository: UserStatisticsRepository,
        expertise_repository: ExpertiseAreaRepository
    ):
        self.session_repository = session_repository
        self.profile_repository = profile_repository
        self.statistics_repository = statistics_repository
        self.expertise_repository = expertise_repository
    
    async def get_compatible_tasks(
        self, db: Session, user_id: str, available_tasks: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Get tasks compatible with user based on the staircase model."""
        # Get user data
        user_data = await self._get_user_data(db, user_id)
        if not user_data:
            logger.warning(f"User {user_id} not found")
            return []
        
        # Calculate compatibility for each task
        compatible_tasks = []
        for task in available_tasks:
            compatibility = await self.calculate_task_compatibility(
                db, 
                user_id, 
                task_type=task.get("task_type"),
                task_complexity=task.get("complexity"),
                task_language=task.get("language"),
                task_category=task.get("category")
            )
            
            # Add task if compatible
            if compatibility["is_compatible"]:
                compatible_tasks.append({
                    **task,
                    "compatibility_score": compatibility["score"],
                    "compatibility_factors": compatibility["factors"]
                })
        
        # Sort by compatibility score
        compatible_tasks.sort(key=lambda x: x["compatibility_score"], reverse=True)
        
        # Implement staircase model: occasionally offer more challenging tasks
        if compatible_tasks and user_data["tasks_completed"] > 0:
            # Add a challenging task every X tasks based on tasks completed
            challenging_interval = max(3, 10 - user_data["expertise_level"])
            
            if user_data["tasks_completed"] % challenging_interval == 0:
                # Find a task slightly above user's expertise level
                challenge_tasks = [
                    t for t in available_tasks 
                    if t.get("complexity", 0) == user_data["expertise_level"] + 1
                    and t.get("language") == user_data["language"]
                ]
                
                if challenge_tasks:
                    # Insert challenge task at the beginning
                    challenge_task = challenge_tasks[0]
                    challenge_task["is_challenge"] = True
                    compatible_tasks.insert(0, challenge_task)
        
        return compatible_tasks
    
    async def calculate_task_compatibility(
        self, 
        db: Session, 
        user_id: str, 
        task_type: Optional[str] = None,
        task_complexity: Optional[int] = None,
        task_language: Optional[str] = None,
        task_category: Optional[str] = None
    ) -> Dict[str, Any]:
        """Calculate compatibility between a user and a task."""
        # Get user data
        user_data = await self._get_user_data(db, user_id)
        if not user_data:
            logger.warning(f"User {user_id} not found")
            return {
                "is_compatible": False,
                "score": 0.0,
                "factors": {}
            }
        
        # Calculate compatibility factors
        factors = {}
        
        # Language compatibility
        language_score = await self._calculate_language_compatibility(
            user_data["language"], task_language
        )
        factors["language"] = language_score
        
        # Complexity compatibility
        complexity_score = await self._calculate_complexity_compatibility(
            user_data["expertise_level"], task_complexity
        )
        factors["complexity"] = complexity_score
        
        # Category compatibility
        category_score = await self._calculate_category_compatibility(
            db, user_id, user_data, task_category
        )
        factors["category"] = category_score
        
        # Calculate overall score with weights
        weights = {
            "language": 0.5,
            "complexity": 0.3,
            "category": 0.2
        }
        
        overall_score = sum(score * weights[factor] for factor, score in factors.items())
        
        # Determine if compatible
        is_compatible = overall_score >= 0.5
        
        return {
            "is_compatible": is_compatible,
            "score": overall_score,
            "factors": factors
        }
    
    async def _get_user_data(self, db: Session, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user data from either session or profile."""
        # Try to get as session first
        session = self.session_repository.get(db, user_id)
        if session:
            # Get statistics for expertise level
            stats = self.statistics_repository.get_by_session_id(db, user_id)
            expertise_level = stats.expertise_level if stats else 0
            
            return {
                "id": session.id,
                "type": "session",
                "language": session.language,
                "tasks_completed": session.tasks_completed,
                "expertise_level": expertise_level,
                "profile_id": session.profile_id
            }
        
        # Try as profile
        profile = self.profile_repository.get(db, user_id)
        if profile:
            return {
                "id": profile.id,
                "type": "profile",
                "language": profile.primary_language,
                "tasks_completed": profile.tasks_completed,
                "expertise_level": profile.expertise_level
            }
        
        return None
    
    async def _calculate_language_compatibility(
        self, user_language: Optional[str], task_language: Optional[str]
    ) -> float:
        """Calculate language compatibility."""
        if not task_language:
            return 1.0  # No language requirement
        
        if not user_language:
            return 0.5  # Unknown user language, assume medium compatibility
        
        return 1.0 if user_language == task_language else 0.2
    
    async def _calculate_complexity_compatibility(
        self, user_expertise: int, task_complexity: Optional[int]
    ) -> float:
        """Calculate complexity compatibility using the staircase model."""
        if task_complexity is None:
            return 1.0  # No complexity requirement
        
        # Perfect match
        if task_complexity == user_expertise:
            return 1.0
        
        # One level below expertise - very easy
        if task_complexity < user_expertise:
            return 0.8
        
        # One level above expertise - challenging but possible
        if task_complexity == user_expertise + 1:
            return 0.6
        
        # Two levels above expertise - very challenging
        if task_complexity == user_expertise + 2:
            return 0.3
        
        # Too difficult
        return 0.1
    
    async def _calculate_category_compatibility(
        self, db: Session, user_id: str, user_data: Dict[str, Any], task_category: Optional[str]
    ) -> float:
        """Calculate category/expertise area compatibility."""
        if not task_category:
            return 1.0  # No category requirement
        
        # For profiles, check expertise areas
        if user_data.get("profile_id"):
            profile_id = user_data["profile_id"] if user_data["type"] == "session" else user_data["id"]
            profile = self.profile_repository.get(db, profile_id)
            
            if profile and profile.expertise_areas:
                # Check if task category matches any expertise area
                for area_id in profile.expertise_areas:
                    area = self.expertise_repository.get(db, area_id)
                    if area and task_category.lower() in area.name.lower():
                        return 1.0
                
                # No exact match, but has expertise areas
                return 0.7
        
        # For sessions or profiles with no expertise areas
        stats = None
        if user_data["type"] == "session":
            stats = self.statistics_repository.get_by_session_id(db, user_id)
        else:
            stats = self.statistics_repository.get_by_profile_id(db, user_id)
        
        if stats and stats.task_type_distribution:
            # Check if user has completed tasks in this category
            if task_category in stats.task_type_distribution:
                return 0.9
        
        # Default moderate compatibility
        return 0.5
    
    async def recommend_next_task_level(
        self, db: Session, user_id: str
    ) -> Dict[str, Any]:
        """Recommend the next task level based on the staircase model."""
        user_data = await self._get_user_data(db, user_id)
        if not user_data:
            logger.warning(f"User {user_id} not found")
            return {"error": "User not found"}
        
        # Get user statistics
        stats = None
        if user_data["type"] == "session":
            stats = self.statistics_repository.get_by_session_id(db, user_id)
        else:
            stats = self.statistics_repository.get_by_profile_id(db, user_id)
        
        # Current expertise level
        current_level = user_data["expertise_level"]
        
        # Determine if user should advance to a more challenging level
        should_advance = False
        confidence = 0.0
        
        if stats:
            # Check success rate
            if stats.success_rate >= 0.8:
                confidence += 0.5
            
            # Check completion rate
            if stats.completion_rate >= 0.9:
                confidence += 0.3
            
            # Check quality score
            if stats.average_quality_score >= 0.8:
                confidence += 0.2
            
            # Determine if user should advance
            should_advance = confidence >= 0.7
        else:
            # Fallback to basic task count
            should_advance = user_data["tasks_completed"] >= settings.EXPERT_LEVEL_THRESHOLDS[current_level]
        
        # Recommended level
        recommended_level = current_level + 1 if should_advance else current_level
        
        # Apply staircase model: occasionally offer more challenging tasks
        is_challenge_task = False
        if not should_advance and user_data["tasks_completed"] > 0:
            challenge_interval = max(3, 10 - current_level)
            is_challenge_task = user_data["tasks_completed"] % challenge_interval == 0
            
            if is_challenge_task:
                recommended_level = current_level + 1
        
        return {
            "user_id": user_id,
            "current_level": current_level,
            "recommended_level": recommended_level,
            "should_advance": should_advance,
            "is_challenge_task": is_challenge_task,
            "confidence": confidence,
            "tasks_completed": user_data["tasks_completed"]
        }
