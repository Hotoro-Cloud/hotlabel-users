import logging
from typing import Dict, Any
from datetime import datetime

from app.core.events import Event, EventType
from app.db.session import get_db
from app.db.repositories.publisher_statistics_repository import PublisherStatisticsRepository
from app.core.redis import get_redis_pool

logger = logging.getLogger(__name__)

class PublisherStatisticsEventHandler:
    def __init__(self):
        self.repository = PublisherStatisticsRepository()
    
    async def handle_event(self, event: Event) -> None:
        """Handle events and update publisher statistics accordingly."""
        try:
            if event.event_type == EventType.TASK_COMPLETED:
                await self._handle_task_completed(event.data)
            elif event.event_type == EventType.TASK_RESULT_SUBMITTED:
                await self._handle_task_result_submitted(event.data)
            elif event.event_type == EventType.SESSION_STARTED:
                await self._handle_session_started(event.data)
            elif event.event_type == EventType.SESSION_ENDED:
                await self._handle_session_ended(event.data)
            elif event.event_type == EventType.VALIDATION_CREATED:
                await self._handle_validation_created(event.data)
            elif event.event_type == EventType.CONSENSUS_REACHED:
                await self._handle_consensus_reached(event.data)
        except Exception as e:
            logger.error(f"Error handling event {event.event_type}: {str(e)}")
    
    async def _handle_task_completed(self, data: Dict[str, Any]) -> None:
        """Handle task completion event."""
        db = next(get_db())
        try:
            await self.repository.update_task_metrics(
                db=db,
                publisher_id=data["publisher_id"],
                task_completed=True,
                task_time_ms=data.get("time_spent_ms", 0),
                task_type=data.get("task_type", "unknown")
            )
        finally:
            db.close()
    
    async def _handle_task_result_submitted(self, data: Dict[str, Any]) -> None:
        """Handle task result submission event."""
        db = next(get_db())
        try:
            await self.repository.update_task_metrics(
                db=db,
                publisher_id=data["publisher_id"],
                task_completed=False,
                task_time_ms=data.get("time_spent_ms", 0),
                task_type=data.get("task_type", "unknown")
            )
        finally:
            db.close()
    
    async def _handle_session_started(self, data: Dict[str, Any]) -> None:
        """Handle session start event."""
        db = next(get_db())
        try:
            await self.repository.update_session_metrics(
                db=db,
                publisher_id=data["publisher_id"],
                session_duration_ms=0,
                is_active=True
            )
            await self.repository.update_user_metrics(
                db=db,
                publisher_id=data["publisher_id"],
                user_id=data["user_id"],
                is_active=True
            )
        finally:
            db.close()
    
    async def _handle_session_ended(self, data: Dict[str, Any]) -> None:
        """Handle session end event."""
        db = next(get_db())
        try:
            session_duration = (
                datetime.fromisoformat(data["end_time"]) -
                datetime.fromisoformat(data["start_time"])
            ).total_seconds() * 1000
            
            await self.repository.update_session_metrics(
                db=db,
                publisher_id=data["publisher_id"],
                session_duration_ms=int(session_duration),
                is_active=False
            )
        finally:
            db.close()
    
    async def _handle_validation_created(self, data: Dict[str, Any]) -> None:
        """Handle validation creation event."""
        db = next(get_db())
        try:
            if "quality_score" in data:
                await self.repository.update_quality_distribution(
                    db=db,
                    publisher_id=data["publisher_id"],
                    quality_score=data["quality_score"]
                )
        finally:
            db.close()
    
    async def _handle_consensus_reached(self, data: Dict[str, Any]) -> None:
        """Handle consensus reached event."""
        db = next(get_db())
        try:
            if "quality_score" in data:
                await self.repository.update_quality_distribution(
                    db=db,
                    publisher_id=data["publisher_id"],
                    quality_score=data["quality_score"]
                )
        finally:
            db.close() 