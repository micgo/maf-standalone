"""
Event Bus Interface - Abstract base for pluggable event bus implementations

This module defines the interface that all event bus implementations must follow,
enabling easy switching between different messaging backends.
"""

from abc import ABC, abstractmethod
from typing import Callable, List, Optional, Dict, Any
from enum import Enum
from dataclasses import dataclass


class EventType(Enum):
    """Standard event types in the system"""
    # Task lifecycle events
    TASK_CREATED = "task.created"
    TASK_ASSIGNED = "task.assigned"
    TASK_STARTED = "task.started"
    TASK_COMPLETED = "task.completed"
    TASK_FAILED = "task.failed"
    TASK_RETRY = "task.retry"
    
    # Feature lifecycle events
    FEATURE_CREATED = "feature.created"
    FEATURE_STARTED = "feature.started"
    FEATURE_COMPLETED = "feature.completed"
    FEATURE_BLOCKED = "feature.blocked"
    
    # Agent events
    AGENT_STARTED = "agent.started"
    AGENT_STOPPED = "agent.stopped"
    AGENT_HEARTBEAT = "agent.heartbeat"
    AGENT_ERROR = "agent.error"
    
    # System events
    SYSTEM_SHUTDOWN = "system.shutdown"
    SYSTEM_HEALTH_CHECK = "system.health_check"
    
    # Custom events
    CUSTOM = "custom"


@dataclass
class Event:
    """Event data structure"""
    id: str
    type: EventType
    source: str  # Agent or component that generated the event
    timestamp: float
    data: Dict[str, Any]
    correlation_id: Optional[str] = None  # For tracking related events
    
    def to_dict(self) -> Dict:
        """Convert event to dictionary"""
        result = {
            'id': self.id,
            'type': self.type.value,
            'source': self.source,
            'timestamp': self.timestamp,
            'data': self.data,
            'correlation_id': self.correlation_id
        }
        return result
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Event':
        """Create event from dictionary"""
        return cls(
            id=data['id'],
            type=EventType(data['type']),
            source=data['source'],
            timestamp=data['timestamp'],
            data=data['data'],
            correlation_id=data.get('correlation_id')
        )


class IEventBus(ABC):
    """
    Abstract interface for event bus implementations.
    All event bus implementations must inherit from this interface.
    """
    
    @abstractmethod
    def start(self) -> None:
        """Start the event bus (connect to brokers, start threads, etc.)"""
        pass
    
    @abstractmethod
    def stop(self) -> None:
        """Stop the event bus and clean up resources"""
        pass
    
    @abstractmethod
    def publish(self, event: Event) -> None:
        """
        Publish an event to the bus
        
        Args:
            event: Event to publish
        """
        pass
    
    @abstractmethod
    def subscribe(self, event_type: EventType, handler: Callable[[Event], None]) -> None:
        """
        Subscribe to events of a specific type
        
        Args:
            event_type: Type of events to subscribe to
            handler: Function to call when event occurs
        """
        pass
    
    @abstractmethod
    def unsubscribe(self, event_type: EventType, handler: Callable[[Event], None]) -> None:
        """
        Unsubscribe from events
        
        Args:
            event_type: Type of events to unsubscribe from
            handler: Handler function to remove
        """
        pass
    
    @abstractmethod
    def publish_task_event(self, event_type: EventType, task_id: str, 
                          source: str, data: Optional[Dict] = None) -> None:
        """
        Convenience method for publishing task-related events
        
        Args:
            event_type: Type of task event
            task_id: Task identifier
            source: Source agent/component
            data: Additional event data
        """
        pass
    
    @abstractmethod
    def add_filter(self, filter_func: Callable[[Event], bool]) -> None:
        """
        Add an event filter. Return False to block event.
        
        Args:
            filter_func: Function that returns True to allow event, False to block
        """
        pass
    
    @abstractmethod
    def get_event_history(self, event_type: Optional[EventType] = None,
                         source: Optional[str] = None,
                         since: Optional[float] = None) -> List[Event]:
        """
        Get filtered event history
        
        Args:
            event_type: Filter by event type
            source: Filter by source
            since: Filter by timestamp (events after this time)
            
        Returns:
            List of events matching filters
        """
        pass
    
    @abstractmethod
    def replay_events(self, events: List[Event]) -> None:
        """
        Replay a list of events (useful for recovery)
        
        Args:
            events: List of events to replay
        """
        pass
    
    @abstractmethod
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get event bus statistics
        
        Returns:
            Dictionary with statistics (events processed, queue size, etc.)
        """
        pass