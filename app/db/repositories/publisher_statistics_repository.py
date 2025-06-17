from typing import Optional, Dict, List
from datetime import datetime, timedelta
import logging
from sqlalchemy.orm import Session
from sqlalchemy import func
from redis import Redis

from app.models.publisher_statistics import PublisherStatistics
from app.schemas.user_statistics import PublisherStatistics as PublisherStatisticsSchema
from app.core.redis import get_redis_pool
from app.core.config import settings

logger = logging.getLogger(__name__)

class PublisherStatisticsRepository:
    def __init__(self):
        self.model = PublisherStatistics
        self.cache_ttl = 300  # 5 minutes cache TTL
        
    async def get(self, db: Session, publisher_id: str) -> Optional[PublisherStatistics]:
        """Get publisher statistics from cache or database."""
        # Try to get from cache first
        redis = await get_redis_pool()
        cache_key = f"publisher_stats:{publisher_id}"
        cached_stats = await redis.get(cache_key)
        
        if cached_stats:
            return PublisherStatisticsSchema.parse_raw(cached_stats)
        
        # If not in cache, get from database
        stats = db.query(self.model).filter(self.model.publisher_id == publisher_id).first()
        
        if stats:
            # Cache the result
            await redis.setex(
                cache_key,
                self.cache_ttl,
                stats.json()
            )
        
        return stats
    
    async def create_or_update(
        self,
        db: Session,
        publisher_id: str,
        stats_data: Dict
    ) -> PublisherStatistics:
        """Create or update publisher statistics."""
        stats = await self.get(db, publisher_id)
        
        if not stats:
            stats = self.model(
                publisher_id=publisher_id,
                **stats_data
            )
            db.add(stats)
        else:
            for key, value in stats_data.items():
                setattr(stats, key, value)
        
        db.commit()
        db.refresh(stats)
        
        # Update cache
        redis = await get_redis_pool()
        cache_key = f"publisher_stats:{publisher_id}"
        await redis.setex(
            cache_key,
            self.cache_ttl,
            stats.json()
        )
        
        return stats
    
    async def update_quality_distribution(
        self,
        db: Session,
        publisher_id: str,
        quality_score: float
    ) -> None:
        """Update quality distribution for a publisher."""
        stats = await self.get(db, publisher_id)
        if not stats:
            return
        
        # Define quality ranges
        ranges = {
            "excellent": (0.9, 1.0),
            "good": (0.7, 0.9),
            "average": (0.5, 0.7),
            "poor": (0.3, 0.5),
            "very_poor": (0.0, 0.3)
        }
        
        # Update distribution
        distribution = stats.quality_distribution or {}
        for range_name, (min_score, max_score) in ranges.items():
            if min_score <= quality_score < max_score:
                distribution[range_name] = distribution.get(range_name, 0) + 1
                break
        
        # Update statistics
        stats.quality_distribution = distribution
        db.commit()
        
        # Update cache
        redis = await get_redis_pool()
        cache_key = f"publisher_stats:{publisher_id}"
        await redis.setex(
            cache_key,
            self.cache_ttl,
            stats.json()
        )
    
    async def update_task_metrics(
        self,
        db: Session,
        publisher_id: str,
        task_completed: bool,
        task_time_ms: int,
        task_type: str
    ) -> None:
        """Update task-related metrics for a publisher."""
        stats = await self.get(db, publisher_id)
        if not stats:
            return
        
        # Update task counts
        stats.total_tasks_attempted += 1
        if task_completed:
            stats.total_tasks_completed += 1
        
        # Update task type distribution
        distribution = stats.task_type_distribution or {}
        distribution[task_type] = distribution.get(task_type, 0) + 1
        stats.task_type_distribution = distribution
        
        # Update task times
        if stats.fastest_task_time_ms == 0 or task_time_ms < stats.fastest_task_time_ms:
            stats.fastest_task_time_ms = task_time_ms
        if task_time_ms > stats.slowest_task_time_ms:
            stats.slowest_task_time_ms = task_time_ms
        
        # Update average task time
        total_time = stats.average_task_time_ms * (stats.total_tasks_completed - 1) + task_time_ms
        stats.average_task_time_ms = total_time / stats.total_tasks_completed
        
        # Update completion rate
        stats.completion_rate = stats.total_tasks_completed / stats.total_tasks_attempted
        
        db.commit()
        
        # Update cache
        redis = await get_redis_pool()
        cache_key = f"publisher_stats:{publisher_id}"
        await redis.setex(
            cache_key,
            self.cache_ttl,
            stats.json()
        )
    
    async def update_session_metrics(
        self,
        db: Session,
        publisher_id: str,
        session_duration_ms: int,
        is_active: bool
    ) -> None:
        """Update session-related metrics for a publisher."""
        stats = await self.get(db, publisher_id)
        if not stats:
            return
        
        # Update session counts
        stats.total_sessions += 1
        if is_active:
            stats.active_sessions += 1
        
        # Update average session duration
        total_duration = stats.average_session_duration_ms * (stats.total_sessions - 1) + session_duration_ms
        stats.average_session_duration_ms = total_duration / stats.total_sessions
        
        db.commit()
        
        # Update cache
        redis = await get_redis_pool()
        cache_key = f"publisher_stats:{publisher_id}"
        await redis.setex(
            cache_key,
            self.cache_ttl,
            stats.json()
        )
    
    async def update_user_metrics(
        self,
        db: Session,
        publisher_id: str,
        user_id: str,
        is_active: bool
    ) -> None:
        """Update user-related metrics for a publisher."""
        stats = await self.get(db, publisher_id)
        if not stats:
            return
        
        # Update active users count
        if is_active:
            stats.active_users += 1
        
        # Update retention rate
        if stats.total_sessions > 0:
            stats.user_retention_rate = stats.active_users / stats.total_sessions
        
        db.commit()
        
        # Update cache
        redis = await get_redis_pool()
        cache_key = f"publisher_stats:{publisher_id}"
        await redis.setex(
            cache_key,
            self.cache_ttl,
            stats.json()
        ) 