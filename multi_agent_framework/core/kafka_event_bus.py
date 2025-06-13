"""
Kafka Event Bus - Kafka implementation of the event bus interface

This module provides a Kafka-based event bus for distributed communication
between agents. This implementation is designed for high-scale deployments.
"""

import json
import threading
import uuid
from typing import Dict, List, Callable, Any, Optional
from concurrent.futures import ThreadPoolExecutor

# Import from interface  
from .event_bus_interface import IEventBus, Event, EventType


class KafkaEventBus(IEventBus):
    """
    Kafka-based event bus implementation.
    Requires kafka-python: pip install kafka-python
    """
    
    def __init__(self, bootstrap_servers: List[str] = None, 
                 consumer_group: str = "multi-agent-framework",
                 max_workers: int = 10):
        """
        Initialize Kafka event bus
        
        Args:
            bootstrap_servers: List of Kafka broker addresses
            consumer_group: Consumer group name for this application
            max_workers: Maximum worker threads for handling events
        """
        self.bootstrap_servers = bootstrap_servers or ['localhost:9092']
        self.consumer_group = consumer_group
        self.max_workers = max_workers
        
        self._subscribers: Dict[EventType, List[Callable]] = {}
        self._consumers: Dict[EventType, Any] = {}  # topic -> consumer
        self._producer = None
        self._running = False
        self._executor = ThreadPoolExecutor(max_workers=max_workers)
        self._lock = threading.Lock()
        self._filters: List[Callable[[Event], bool]] = []
        
        # For now, we'll store a simple in-memory history
        # In production, this would query Kafka's log
        self._event_history: List[Event] = []
        self._max_history_size = 1000
        
    def start(self) -> None:
        """Start the Kafka event bus"""
        try:
            from kafka import KafkaProducer
            
            self._producer = KafkaProducer(
                bootstrap_servers=self.bootstrap_servers,
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                key_serializer=lambda k: k.encode('utf-8') if k else None
            )
            self._running = True
            print(f"KafkaEventBus: Connected to Kafka brokers: {self.bootstrap_servers}")
            
        except ImportError:
            raise ImportError(
                "kafka-python is required for KafkaEventBus. "
                "Install it with: pip install kafka-python"
            )
        except Exception as e:
            print(f"KafkaEventBus: Failed to connect to Kafka: {e}")
            raise
    
    def stop(self) -> None:
        """Stop the Kafka event bus"""
        self._running = False
        
        # Stop all consumers
        for consumer in self._consumers.values():
            consumer.close()
        self._consumers.clear()
        
        # Close producer
        if self._producer:
            self._producer.close()
            
        # Shutdown executor
        self._executor.shutdown(wait=True)
        
        print("KafkaEventBus: Stopped")
    
    def publish(self, event: Event) -> None:
        """Publish an event to Kafka"""
        if not self._running or not self._producer:
            raise RuntimeError("KafkaEventBus is not running")
        
        # Apply filters
        for filter_func in self._filters:
            if not filter_func(event):
                return  # Event filtered out
        
        # Convert event to dict for serialization
        event_data = event.to_dict()
        
        # Use event type as topic name
        topic = f"events.{event.type.value}"
        
        # Send to Kafka
        future = self._producer.send(
            topic,
            key=event.correlation_id,
            value=event_data
        )
        
        # Store in history (in production, this would be queried from Kafka)
        self._event_history.append(event)
        if len(self._event_history) > self._max_history_size:
            self._event_history = self._event_history[-self._max_history_size:]
        
        # Optionally wait for send to complete
        try:
            future.get(timeout=10)
        except Exception as e:
            print(f"KafkaEventBus: Failed to publish event: {e}")
            raise
    
    def subscribe(self, event_type: EventType, handler: Callable[[Event], None]) -> None:
        """Subscribe to events of a specific type"""
        with self._lock:
            if event_type not in self._subscribers:
                self._subscribers[event_type] = []
                self._start_consumer_for_topic(event_type)
            
            self._subscribers[event_type].append(handler)
            print(f"KafkaEventBus: Subscribed {handler.__name__} to {event_type.value}")
    
    def unsubscribe(self, event_type: EventType, handler: Callable[[Event], None]) -> None:
        """Unsubscribe from events"""
        with self._lock:
            if event_type in self._subscribers:
                self._subscribers[event_type].remove(handler)
                
                # If no more subscribers, stop consumer
                if not self._subscribers[event_type]:
                    self._stop_consumer_for_topic(event_type)
                    del self._subscribers[event_type]
    
    def publish_task_event(self, event_type: EventType, task_id: str, 
                          source: str, data: Optional[Dict] = None) -> None:
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
    
    def add_filter(self, filter_func: Callable[[Event], bool]) -> None:
        """Add an event filter"""
        self._filters.append(filter_func)
    
    def get_event_history(self, event_type: Optional[EventType] = None,
                         source: Optional[str] = None,
                         since: Optional[float] = None) -> List[Event]:
        """Get filtered event history"""
        # In production, this would query Kafka's log
        history = self._event_history.copy()
        
        if event_type:
            history = [e for e in history if e.type == event_type]
        if source:
            history = [e for e in history if e.source == source]
        if since:
            history = [e for e in history if e.timestamp >= since]
        
        return history
    
    def replay_events(self, events: List[Event]) -> None:
        """Replay a list of events"""
        for event in events:
            self.publish(event)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get event bus statistics"""
        return {
            'total_events_processed': len(self._event_history),
            'subscriber_count': sum(len(handlers) for handlers in self._subscribers.values()),
            'filter_count': len(self._filters),
            'is_running': self._running,
            'consumer_count': len(self._consumers),
            'event_types': {event_type.value: len(handlers) 
                           for event_type, handlers in self._subscribers.items()},
            'bootstrap_servers': self.bootstrap_servers,
            'consumer_group': self.consumer_group
        }
    
    def _start_consumer_for_topic(self, event_type: EventType) -> None:
        """Start a Kafka consumer for a specific event type"""
        try:
            from kafka import KafkaConsumer
            import time
            
            topic = f"events.{event_type.value}"
            
            # Create consumer in a separate thread
            def consume():
                consumer = KafkaConsumer(
                    topic,
                    bootstrap_servers=self.bootstrap_servers,
                    group_id=self.consumer_group,
                    value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                    auto_offset_reset='latest',
                    enable_auto_commit=True
                )
                
                self._consumers[event_type] = consumer
                
                print(f"KafkaEventBus: Started consumer for topic {topic}")
                
                while self._running and event_type in self._consumers:
                    try:
                        # Poll for messages
                        messages = consumer.poll(timeout_ms=1000)
                        
                        for topic_partition, records in messages.items():
                            for record in records:
                                # Convert back to Event object
                                event = Event.from_dict(record.value)
                                
                                # Get handlers
                                with self._lock:
                                    handlers = self._subscribers.get(event_type, []).copy()
                                
                                # Call each handler in executor
                                for handler in handlers:
                                    self._executor.submit(self._safe_handler_call, handler, event)
                                    
                    except Exception as e:
                        print(f"KafkaEventBus: Error in consumer for {topic}: {e}")
                        time.sleep(1)  # Back off on error
                
                consumer.close()
                print(f"KafkaEventBus: Stopped consumer for topic {topic}")
            
            # Start consumer thread
            consumer_thread = threading.Thread(target=consume, daemon=True)
            consumer_thread.start()
            
        except ImportError:
            raise ImportError(
                "kafka-python is required for KafkaEventBus. "
                "Install it with: pip install kafka-python"
            )
    
    def _stop_consumer_for_topic(self, event_type: EventType) -> None:
        """Stop the Kafka consumer for a specific event type"""
        if event_type in self._consumers:
            # Consumer will stop when it sees event_type is not in _consumers
            del self._consumers[event_type]
    
    def _safe_handler_call(self, handler: Callable, event: Event) -> None:
        """Safely call event handler with error handling"""
        try:
            handler(event)
        except Exception as e:
            print(f"KafkaEventBus: Error in handler {handler.__name__}: {e}")
            
            # Publish error event
            error_event = Event(
                id=str(uuid.uuid4()),
                type=EventType.AGENT_ERROR,
                source="kafka_event_bus",
                timestamp=time.time(),
                data={
                    "handler": handler.__name__,
                    "original_event": event.to_dict(),
                    "error": str(e)
                }
            )
            # Note: Be careful not to create infinite loop if error handler fails
            try:
                self.publish(error_event)
            except:
                pass  # Silently fail to avoid infinite loop


# Import time at the top if not already imported
import time