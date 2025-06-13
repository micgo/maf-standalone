"""
Event Bus - In-memory implementation of the event-driven architecture

This module provides an in-memory event bus for asynchronous communication
between agents using a publish/subscribe pattern.
"""

import json
import threading
import queue
import time
import uuid
from typing import Dict, List, Callable, Any, Optional
from datetime import datetime

# Import from interface
from .event_bus_interface import IEventBus, Event, EventType


class InMemoryEventBus(IEventBus):
    """
    Central event bus for the multi-agent framework.
    Implements publish/subscribe pattern with threading support.
    """
    
    def __init__(self, persist_events: bool = True):
        self._subscribers: Dict[EventType, List[Callable]] = {}
        self._event_queue: queue.Queue = queue.Queue()
        self._running = False
        self._worker_thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()
        self._persist_events = persist_events
        self._event_history: List[Event] = []
        self._max_history_size = 1000
        
        # Event filters
        self._filters: List[Callable[[Event], bool]] = []
        
    def start(self):
        """Start the event bus worker thread"""
        if self._running:
            return
            
        self._running = True
        self._worker_thread = threading.Thread(target=self._process_events, daemon=True)
        self._worker_thread.start()
        print("EventBus: Started event processing thread")
        
    def stop(self):
        """Stop the event bus"""
        self._running = False
        # Send shutdown event
        self.publish(Event(
            id=str(uuid.uuid4()),
            type=EventType.SYSTEM_SHUTDOWN,
            source="event_bus",
            timestamp=time.time(),
            data={}
        ))
        
        if self._worker_thread:
            self._worker_thread.join(timeout=5)
        print("EventBus: Stopped event processing")
        
    def subscribe(self, event_type: EventType, handler: Callable[[Event], None]):
        """
        Subscribe to events of a specific type
        
        Args:
            event_type: Type of events to subscribe to
            handler: Function to call when event occurs
        """
        with self._lock:
            if event_type not in self._subscribers:
                self._subscribers[event_type] = []
            self._subscribers[event_type].append(handler)
            print(f"EventBus: Subscribed {handler.__name__} to {event_type.value}")
            
    def unsubscribe(self, event_type: EventType, handler: Callable[[Event], None]):
        """Unsubscribe from events"""
        with self._lock:
            if event_type in self._subscribers:
                self._subscribers[event_type].remove(handler)
                
    def publish(self, event: Event):
        """
        Publish an event to the bus
        
        Args:
            event: Event to publish
        """
        # Apply filters
        for filter_func in self._filters:
            if not filter_func(event):
                return  # Event filtered out
                
        self._event_queue.put(event)
        
    def publish_task_event(self, event_type: EventType, task_id: str, 
                          source: str, data: Optional[Dict] = None):
        """Convenience method for publishing task-related events"""
        event_data = {"task_id": task_id}
        if data:
            event_data.update(data)
            
        event = Event(
            id=str(uuid.uuid4()),
            type=event_type,
            source=source,
            timestamp=time.time(),
            data=event_data,
            correlation_id=task_id
        )
        self.publish(event)
        
    def add_filter(self, filter_func: Callable[[Event], bool]):
        """Add an event filter. Return False to block event."""
        self._filters.append(filter_func)
        
    def _process_events(self):
        """Worker thread that processes events"""
        while self._running:
            try:
                # Wait for event with timeout to allow checking _running flag
                event = self._event_queue.get(timeout=1)
                
                # Store in history
                if self._persist_events:
                    self._store_event(event)
                
                # Get subscribers for this event type
                with self._lock:
                    handlers = self._subscribers.get(event.type, []).copy()
                
                if handlers:
                    print(f"EventBus: Processing {event.type.value} event with {len(handlers)} handlers")
                
                # Call each handler in separate thread to prevent blocking
                for handler in handlers:
                    threading.Thread(
                        target=self._safe_handler_call,
                        args=(handler, event),
                        daemon=True
                    ).start()
                    
            except queue.Empty:
                continue
            except Exception as e:
                print(f"EventBus: Error processing event: {e}")
                
    def _safe_handler_call(self, handler: Callable, event: Event):
        """Safely call event handler with error handling"""
        try:
            # print(f"EventBus: Calling handler {handler.__name__} for {event.type.value}")
            handler(event)
        except Exception as e:
            print(f"EventBus: Error in handler {handler.__name__}: {e}")
            import traceback
            traceback.print_exc()
            # Publish error event
            error_event = Event(
                id=str(uuid.uuid4()),
                type=EventType.AGENT_ERROR,
                source="event_bus",
                timestamp=time.time(),
                data={
                    "handler": handler.__name__,
                    "original_event": event.to_dict(),
                    "error": str(e)
                }
            )
            self._event_queue.put(error_event)
            
    def _store_event(self, event: Event):
        """Store event in history"""
        self._event_history.append(event)
        
        # Trim history if too large
        if len(self._event_history) > self._max_history_size:
            self._event_history = self._event_history[-self._max_history_size:]
            
    def get_event_history(self, event_type: Optional[EventType] = None,
                         source: Optional[str] = None,
                         since: Optional[float] = None) -> List[Event]:
        """Get filtered event history"""
        history = self._event_history.copy()
        
        if event_type:
            history = [e for e in history if e.type == event_type]
        if source:
            history = [e for e in history if e.source == source]
        if since:
            history = [e for e in history if e.timestamp >= since]
            
        return history
    
    def replay_events(self, events: List[Event]):
        """Replay a list of events (useful for recovery)"""
        for event in events:
            self.publish(event)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get event bus statistics"""
        return {
            'total_events_processed': len(self._event_history),
            'queue_size': self._event_queue.qsize(),
            'subscriber_count': sum(len(handlers) for handlers in self._subscribers.values()),
            'filter_count': len(self._filters),
            'is_running': self._running,
            'event_types': {event_type.value: len(handlers) 
                           for event_type, handlers in self._subscribers.items()}
        }


# Global event bus instance
_event_bus = None
_event_bus_lock = threading.Lock()


def get_event_bus() -> InMemoryEventBus:
    """Get the global event bus instance"""
    global _event_bus
    
    if _event_bus is None:
        with _event_bus_lock:
            if _event_bus is None:
                _event_bus = InMemoryEventBus()
                _event_bus.start()
    
    return _event_bus