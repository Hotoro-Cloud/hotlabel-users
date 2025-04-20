import hashlib
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from app.db.repositories.user_session_repository import UserSessionRepository
from app.db.repositories.user_profile_repository import UserProfileRepository
from app.db.repositories.user_statistics_repository import UserStatisticsRepository
from app.db.repositories.expertise_area_repository import ExpertiseAreaRepository
from app.core.config import settings

logger = logging.getLogger(__name__)


class ProfilerService:
    """Service for user profiling and expertise inference."""
    
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
    
    async def profile_user_signals(
        self, db: Session, session_id: str, signals: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process user signals and update profile accordingly."""
        # Get session
        session = self.session_repository.get(db, session_id)
        if not session:
            logger.warning(f"Session {session_id} not found")
            return {"error": "Session not found"}
        
        # Process signals
        updates = {}
        
        # Extract language
        if "language" in signals:
            updates["language"] = signals["language"]
        
        # Extract timezone
        if "timezone" in signals:
            updates["timezone"] = signals["timezone"]
        
        # Extract device type
        if "device_type" in signals:
            updates["device_type"] = signals["device_type"]
        
        # Extract platform
        if "platform" in signals:
            updates["platform"] = signals["platform"]
        
        # Extract country
        if "geo_location" in signals and "country" in signals["geo_location"]:
            updates["country"] = signals["geo_location"]["country"]
        
        # Extract referrer
        if "referrer" in signals:
            updates["referrer"] = signals["referrer"]
        
        # Update session
        if updates:
            session = self.session_repository.update(
                db, db_obj=session, obj_in=updates
            )
        
        # Process browsing patterns for expertise inference
        if "browsing_patterns" in signals:
            expertise_areas = self._infer_expertise_areas(signals["browsing_patterns"])
            
            # If linked to a profile, update expertise areas
            if session.profile_id:
                profile = self.profile_repository.get(db, session.profile_id)
                if profile:
                    # Get expertise area IDs
                    area_ids = []
                    for area_name in expertise_areas:
                        area = self.expertise_repository.get_by_name(db, area_name)
                        if area:
                            area_ids.append(area.id)
                    
                    # Update profile expertise areas if new ones found
                    if area_ids:
                        self.profile_repository.update_expertise_areas(db, profile.id, area_ids)
        
        # Return updated session data
        return {
            "session_id": session.id,
            "updates": updates,
            "current_state": {
                "language": session.language,
                "country": session.country,
                "device_type": session.device_type,
                "platform": session.platform,
                "tasks_completed": session.tasks_completed
            }
        }
    
    def _infer_expertise_areas(self, browsing_patterns: List[Dict[str, Any]]) -> List[str]:
        """Infer expertise areas from browsing patterns."""
        # This is a simplified implementation
        # In a real system, this would use more sophisticated algorithms
        
        # Sample mapping of website categories to expertise areas
        category_to_expertise = {
            "technology": "Technology",
            "programming": "Programming",
            "science": "Science",
            "medicine": "Healthcare",
            "finance": "Finance",
            "business": "Business",
            "arts": "Arts",
            "education": "Education",
            "gaming": "Gaming"
        }
        
        # Count occurrences of each category
        category_counts = {}
        for pattern in browsing_patterns:
            if "category" in pattern:
                category = pattern["category"].lower()
                category_counts[category] = category_counts.get(category, 0) + 1
        
        # Get top categories (above a threshold)
        threshold = max(1, len(browsing_patterns) * 0.1)  # At least 10% of patterns
        top_categories = [
            cat for cat, count in category_counts.items() 
            if count >= threshold and cat in category_to_expertise
        ]
        
        # Map to expertise areas
        expertise_areas = [category_to_expertise[cat] for cat in top_categories]
        
        return expertise_areas
    
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
        # Try to get as session first
        session = self.session_repository.get(db, user_id)
        if session:
            user_data = {
                "id": session.id,
                "type": "session",
                "language": session.language,
                "expertise_level": self._calculate_expertise_level(session.tasks_completed),
                "profile_id": session.profile_id
            }
        else:
            # Try as profile
            profile = self.profile_repository.get(db, user_id)
            if profile:
                user_data = {
                    "id": profile.id,
                    "type": "profile",
                    "language": profile.primary_language,
                    "expertise_level": profile.expertise_level,
                    "profile_id": profile.id
                }
            else:
                logger.warning(f"User {user_id} not found")
                return {"error": "User not found"}
        
        # Calculate compatibility scores
        scores = {}
        
        # Language compatibility
        if task_language:
            user_language = user_data["language"] or "en"
            scores["language"] = 1.0 if user_language == task_language else 0.3
        else:
            scores["language"] = 1.0
        
        # Expertise compatibility
        if task_complexity is not None:
            user_expertise = user_data["expertise_level"]
            # Allow one level higher than current expertise
            max_complexity = user_expertise + 1
            if task_complexity > max_complexity:
                expertise_score = max(0.1, 1.0 - ((task_complexity - max_complexity) * 0.3))
            else:
                expertise_score = 1.0
            scores["expertise"] = expertise_score
        else:
            scores["expertise"] = 1.0
        
        # Category compatibility
        if task_category and user_data["profile_id"]:
            # For profiles, check expertise areas
            profile = self.profile_repository.get(db, user_data["profile_id"])
            if profile and profile.expertise_areas:
                # Check if task category matches any expertise area
                for area_id in profile.expertise_areas:
                    area = self.expertise_repository.get(db, area_id)
                    if area and task_category.lower() in area.name.lower():
                        scores["category"] = 1.0
                        break
                else:
                    # No matching expertise area found
                    scores["category"] = 0.5
            else:
                scores["category"] = 0.5
        else:
            scores["category"] = 1.0
        
        # Calculate overall score
        weights = {
            "language": 0.4,
            "expertise": 0.4,
            "category": 0.2
        }
        
        overall_score = sum(score * weights[factor] for factor, score in scores.items())
        
        return {
            "user_id": user_id,
            "user_type": user_data["type"],
            "task_compatibility": {
                "overall_score": overall_score,
                "is_compatible": overall_score >= 0.5,
                "factors": scores
            },
            "user_data": user_data
        }
    
    def _calculate_expertise_level(self, tasks_completed: int) -> int:
        """Calculate expertise level based on number of tasks completed."""
        thresholds = settings.EXPERT_LEVEL_THRESHOLDS
        for level, threshold in enumerate(thresholds):
            if tasks_completed < threshold:
                return level
        
        # If more than all thresholds, return the highest level
        return len(thresholds)
    
    async def anonymize_user_data(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Anonymize user data for privacy."""
        anonymized = user_data.copy()
        
        # Remove or hash potentially identifying information
        keys_to_remove = ["email", "ip_address", "exact_location"]
        keys_to_hash = ["user_agent", "browser_fingerprint"]
        
        for key in keys_to_remove:
            if key in anonymized:
                del anonymized[key]
        
        for key in keys_to_hash:
            if key in anonymized and anonymized[key]:
                anonymized[key] = self._hash_string(anonymized[key])
        
        return anonymized
    
    def _hash_string(self, text: str) -> str:
        """Create a SHA-256 hash of a string."""
        return hashlib.sha256(text.encode()).hexdigest()
    
    async def detect_language(self, text: str) -> Dict[str, Any]:
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
            "detected_language": detected_language,
            "confidence": confidence,
            "language_scores": scores
        }
