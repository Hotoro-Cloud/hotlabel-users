from typing import List, Optional, Dict, Any, Union
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.db.repositories.base import BaseRepository
from app.models.user_statistics import UserStatistics
from app.schemas.user_statistics import UserStatisticsCreate, UserStatisticsUpdate


class UserStatisticsRepository(BaseRepository[UserStatistics, UserStatisticsCreate, UserStatisticsUpdate]):
    """Repository for user statistics operations."""
    
    def __init__(self):
        super().__init__(UserStatistics)
    
    def get_by_session_id(self, db: Session, session_id: str) -> Optional[UserStatistics]:
        """Get statistics by session ID."""
        return db.query(self.model).filter(self.model.session_id == session_id).first()
    
    def get_by_profile_id(self, db: Session, profile_id: str) -> Optional[UserStatistics]:
        """Get statistics by profile ID."""
        return db.query(self.model).filter(self.model.profile_id == profile_id).first()
    
    def get_by_user(self, db: Session, user_id: str) -> Optional[UserStatistics]:
        """Get statistics by user ID (either session or profile)."""
        return db.query(self.model).filter(
            or_(self.model.session_id == user_id, self.model.profile_id == user_id)
        ).first()
    
    def create_for_session(
        self, db: Session, session_id: str
    ) -> UserStatistics:
        """Create statistics for a session."""
        stats = UserStatisticsCreate(session_id=session_id)
        return self.create(db, obj_in=stats)
    
    def create_for_profile(
        self, db: Session, profile_id: str
    ) -> UserStatistics:
        """Create statistics for a profile."""
        stats = UserStatisticsCreate(profile_id=profile_id)
        return self.create(db, obj_in=stats)
    
    def update_task_metrics(
        self, 
        db: Session, 
        stats_id: str, 
        task_completed: bool = True,
        task_type: str = None,
        task_time_ms: int = None,
        task_quality_score: float = None
    ) -> Optional[UserStatistics]:
        """Update statistics after a task is completed or attempted."""
        stats = self.get(db, stats_id)
        if not stats:
            return None
        
        # Update task counts
        stats.total_tasks_attempted += 1
        if task_completed:
            stats.total_tasks_completed += 1
        
        # Calculate completion rate
        if stats.total_tasks_attempted > 0:
            stats.completion_rate = stats.total_tasks_completed / stats.total_tasks_attempted
        
        # Update task type distribution
        if task_type:
            task_type_dist = stats.task_type_distribution or {}
            task_type_dist[task_type] = task_type_dist.get(task_type, 0) + 1
            stats.task_type_distribution = task_type_dist
        
        # Update task time metrics
        if task_time_ms is not None:
            # Update fastest time
            if stats.fastest_task_time_ms == 0 or task_time_ms < stats.fastest_task_time_ms:
                stats.fastest_task_time_ms = task_time_ms
            
            # Update slowest time
            if task_time_ms > stats.slowest_task_time_ms:
                stats.slowest_task_time_ms = task_time_ms
            
            # Update average time
            total_completed = stats.total_tasks_completed or 1  # Avoid division by zero
            current_total_time = stats.average_task_time_ms * (total_completed - 1)
            stats.average_task_time_ms = (current_total_time + task_time_ms) / total_completed
        
        # Update quality metrics
        if task_quality_score is not None:
            # Update quality distribution
            quality_range = f"{int(task_quality_score * 10) / 10:.1f}"  # Round to nearest 0.1
            quality_dist = stats.quality_distribution or {}
            quality_dist[quality_range] = quality_dist.get(quality_range, 0) + 1
            stats.quality_distribution = quality_dist
            
            # Update average quality score
            total_completed = stats.total_tasks_completed or 1  # Avoid division by zero
            current_total_quality = stats.average_quality_score * (total_completed - 1)
            stats.average_quality_score = (current_total_quality + task_quality_score) / total_completed
        
        # Update task dates
        now = datetime.utcnow()
        if stats.first_task_date is None:
            stats.first_task_date = now
        stats.last_task_date = now
        
        # Calculate active days
        if stats.first_task_date:
            # Simplified - in a real implementation, we'd count unique days
            days_diff = (now - stats.first_task_date).days + 1
            stats.active_days = min(days_diff, stats.active_days + 1)
        
        # Update engagement and consistency scores
        self._update_engagement_score(stats)
        self._update_consistency_score(stats)
        
        db.add(stats)
        db.commit()
        db.refresh(stats)
        return stats
    
    def _update_engagement_score(self, stats: UserStatistics) -> None:
        """Calculate and update engagement score."""
        # Simple calculation based on tasks completed and quality
        tasks_factor = min(1.0, stats.total_tasks_completed / 100)  # Max at 100 tasks
        quality_factor = stats.average_quality_score
        
        # Combine factors with weights
        stats.engagement_score = 0.7 * tasks_factor + 0.3 * quality_factor
    
    def _update_consistency_score(self, stats: UserStatistics) -> None:
        """Calculate and update consistency score."""
        if not stats.first_task_date or not stats.last_task_date:
            stats.consistency_score = 0.0
            return
        
        # Calculate days since first task
        days_since_first = (datetime.utcnow() - stats.first_task_date).days + 1
        
        # Calculate consistency based on active days vs total days
        if days_since_first > 0:
            stats.consistency_score = min(1.0, stats.active_days / days_since_first)
        else:
            stats.consistency_score = 1.0  # Started today
    
    def update_expertise_areas(
        self, db: Session, stats_id: str, expertise_areas: List[str]
    ) -> Optional[UserStatistics]:
        """Update expertise areas for statistics."""
        stats = self.get(db, stats_id)
        if not stats:
            return None
        
        stats.expertise_areas = expertise_areas
        
        db.add(stats)
        db.commit()
        db.refresh(stats)
        return stats
    
    def update_expertise_level(
        self, db: Session, stats_id: str, expertise_level: int
    ) -> Optional[UserStatistics]:
        """Update expertise level for statistics."""
        stats = self.get(db, stats_id)
        if not stats:
            return None
        
        stats.expertise_level = expertise_level
        
        db.add(stats)
        db.commit()
        db.refresh(stats)
        return stats
