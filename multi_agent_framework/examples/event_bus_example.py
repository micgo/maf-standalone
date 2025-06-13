"""
Example demonstrating the hybrid event bus architecture

This example shows how to:
1. Use the in-memory event bus (default)
2. Switch to Kafka event bus via configuration
3. Create event-driven agents
"""

import os
import sys
import time

# Add the framework to path
framework_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, framework_root)

from core.event_bus_interface import Event, EventType
from core.event_bus_factory import get_event_bus, reset_event_bus


def example_inmemory_event_bus():
    """Example using in-memory event bus"""
    print("\n=== In-Memory Event Bus Example ===")
    
    # Get event bus with default configuration (in-memory)
    event_bus = get_event_bus()
    
    # Define a simple event handler
    def handle_task_created(event: Event):
        print(f"Task created: {event.data.get('description', 'No description')}")
    
    # Subscribe to task created events
    event_bus.subscribe(EventType.TASK_CREATED, handle_task_created)
    
    # Publish some events
    event_bus.publish(Event(
        id="task-1",
        type=EventType.TASK_CREATED,
        source="example",
        timestamp=time.time(),
        data={"description": "Implement user authentication"}
    ))
    
    event_bus.publish(Event(
        id="task-2",
        type=EventType.TASK_CREATED,
        source="example",
        timestamp=time.time(),
        data={"description": "Add database migrations"}
    ))
    
    # Give time for events to be processed
    time.sleep(1)
    
    # Check statistics
    stats = event_bus.get_statistics()
    print(f"\nEvent Bus Statistics:")
    print(f"  Total events: {stats['total_events_processed']}")
    print(f"  Subscribers: {stats['subscriber_count']}")
    print(f"  Queue size: {stats['queue_size']}")


def example_kafka_event_bus():
    """Example using Kafka event bus"""
    print("\n=== Kafka Event Bus Example ===")
    print("Note: This requires Kafka to be running locally on port 9092")
    
    # Reset the global event bus to switch implementations
    reset_event_bus()
    
    # Configure for Kafka
    kafka_config = {
        'type': 'kafka',
        'kafka_config': {
            'bootstrap_servers': ['localhost:9092'],
            'consumer_group': 'example-group',
            'max_workers': 5
        }
    }
    
    try:
        # Get event bus with Kafka configuration
        event_bus = get_event_bus(kafka_config)
        
        # Define event handlers
        def handle_agent_started(event: Event):
            print(f"Agent started: {event.data.get('agent', 'Unknown')}")
        
        def handle_task_completed(event: Event):
            print(f"Task completed: {event.data.get('task_id', 'Unknown')}")
        
        # Subscribe to events
        event_bus.subscribe(EventType.AGENT_STARTED, handle_agent_started)
        event_bus.subscribe(EventType.TASK_COMPLETED, handle_task_completed)
        
        # Publish events
        event_bus.publish(Event(
            id="agent-start-1",
            type=EventType.AGENT_STARTED,
            source="example",
            timestamp=time.time(),
            data={"agent": "frontend_agent"}
        ))
        
        event_bus.publish_task_event(
            EventType.TASK_COMPLETED,
            task_id="task-123",
            source="backend_agent",
            data={"result": "API endpoint created successfully"}
        )
        
        # Give time for Kafka to process
        time.sleep(2)
        
        # Check statistics
        stats = event_bus.get_statistics()
        print(f"\nKafka Event Bus Statistics:")
        print(f"  Total events: {stats['total_events_processed']}")
        print(f"  Subscribers: {stats['subscriber_count']}")
        print(f"  Consumer count: {stats['consumer_count']}")
        print(f"  Bootstrap servers: {stats['bootstrap_servers']}")
        
    except Exception as e:
        print(f"Kafka example failed: {e}")
        print("Make sure Kafka is running locally on port 9092")


def example_event_filtering():
    """Example demonstrating event filtering"""
    print("\n=== Event Filtering Example ===")
    
    # Reset to use fresh in-memory bus
    reset_event_bus()
    event_bus = get_event_bus()
    
    # Add a filter to only allow high-priority events
    def priority_filter(event: Event) -> bool:
        priority = event.data.get('priority', 'normal')
        return priority in ['high', 'critical']
    
    event_bus.add_filter(priority_filter)
    
    # Handler for all task events
    events_received = []
    def handle_all_tasks(event: Event):
        events_received.append(event)
        print(f"Received: {event.data.get('description')} (priority: {event.data.get('priority')})")
    
    event_bus.subscribe(EventType.TASK_CREATED, handle_all_tasks)
    
    # Publish events with different priorities
    test_events = [
        {"description": "Critical security fix", "priority": "critical"},
        {"description": "Normal feature", "priority": "normal"},
        {"description": "High priority bug", "priority": "high"},
        {"description": "Low priority cleanup", "priority": "low"}
    ]
    
    for i, data in enumerate(test_events):
        event_bus.publish(Event(
            id=f"filtered-task-{i}",
            type=EventType.TASK_CREATED,
            source="example",
            timestamp=time.time(),
            data=data
        ))
    
    time.sleep(1)
    print(f"\nSent {len(test_events)} events, received {len(events_received)} after filtering")


def example_event_history():
    """Example demonstrating event history and replay"""
    print("\n=== Event History Example ===")
    
    reset_event_bus()
    event_bus = get_event_bus()
    
    # Publish some events
    for i in range(5):
        event_bus.publish(Event(
            id=f"history-task-{i}",
            type=EventType.TASK_CREATED,
            source="agent-1" if i % 2 == 0 else "agent-2",
            timestamp=time.time(),
            data={"task_number": i}
        ))
        time.sleep(0.1)
    
    # Query event history
    print("\nAll events:")
    all_events = event_bus.get_event_history()
    for event in all_events:
        print(f"  {event.id} from {event.source}")
    
    print("\nEvents from agent-1:")
    agent1_events = event_bus.get_event_history(source="agent-1")
    for event in agent1_events:
        print(f"  {event.id} - task #{event.data['task_number']}")
    
    # Replay specific events
    print("\nReplaying agent-2 events...")
    
    replay_count = 0
    def count_replays(event: Event):
        nonlocal replay_count
        replay_count += 1
    
    event_bus.subscribe(EventType.TASK_CREATED, count_replays)
    
    agent2_events = event_bus.get_event_history(source="agent-2")
    event_bus.replay_events(agent2_events)
    
    time.sleep(1)
    print(f"Replayed {replay_count} events")


if __name__ == "__main__":
    # Run examples
    example_inmemory_event_bus()
    example_kafka_event_bus()
    example_event_filtering()
    example_event_history()
    
    print("\n=== Configuration via Environment Variables ===")
    print("You can also configure the event bus via environment variables:")
    print("  EVENT_BUS_TYPE=kafka")
    print("  KAFKA_BOOTSTRAP_SERVERS=broker1:9092,broker2:9092")
    print("  KAFKA_CONSUMER_GROUP=my-app")
    print("  KAFKA_MAX_WORKERS=20")