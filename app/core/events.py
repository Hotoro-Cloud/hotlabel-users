from enum import Enum
from typing import Any, Dict, Optional, List
from pydantic import BaseModel
from app.core.redis import get_redis

class EventType(str, Enum):
    # Task Events
    TASK_CREATED = "task.created"
    TASK_ASSIGNED = "task.assigned"
    TASK_COMPLETED = "task.completed"
    TASK_RESULT_SUBMITTED = "task.result_submitted"
    TASK_REJECTED = "task.rejected"
    
    # Validation Events
    VALIDATION_CREATED = "validation.created"
    VALIDATION_STATUS_UPDATED = "validation.status_updated"
    
    # Consensus Events
    CONSENSUS_CREATED = "consensus.created"
    CONSENSUS_UPDATED = "consensus.updated"
    CONSENSUS_REACHED = "consensus.reached"
    
    # Session Events
    SESSION_STARTED = "session.started"
    SESSION_ENDED = "session.ended"
    
    # Statistics Events
    STATISTICS_UPDATED = "statistics.updated"
    
    # Task Management Events
    TASK_UPDATED = "task.updated"
    TASK_DELETED = "task.deleted"

class Event(BaseModel):
    type: EventType
    data: Dict[str, Any]
    metadata: Optional[Dict[str, Any]] = None

class RedisEventBus:
    def __init__(self):
        self.redis_client = None
        self.pubsub = None

    async def connect(self):
        """Connect to Redis and get a client instance."""
        self.redis_client = await get_redis()
        self.pubsub = self.redis_client.pubsub()

    async def publish(self, event: Event):
        """Publish an event to the Redis event bus."""
        if not self.redis_client:
            await self.connect()
        await self.redis_client.publish(event.type, event.json())

    async def subscribe(self, event_types: List[EventType]):
        """Subscribe to a list of event types."""
        if not self.pubsub:
            await self.connect()
        for event_type in event_types:
            await self.pubsub.subscribe(event_type)

    async def get_next_event(self):
        """Retrieve the next event from the Redis pub/sub channel."""
        if not self.pubsub:
            await self.connect()
        message = await self.pubsub.get_message(ignore_subscribe_messages=True)
        if message and message['type'] == 'message':
            return Event.parse_raw(message['data'])
        return None

redis_event_bus = RedisEventBus() 