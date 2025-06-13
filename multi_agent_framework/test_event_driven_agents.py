#!/usr/bin/env python3
"""
Test script for event-driven agents

Demonstrates the event-driven architecture in action.
"""

import sys
import os
import time
import threading

# Add framework to path
framework_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, framework_root)

from core.agent_factory import create_agent
from core.event_bus_factory import get_event_bus
from core.event_bus_interface import Event, EventType
import config


def test_event_driven_flow():
    """Test the event-driven agent flow"""
    print("=== Testing Event-Driven Agent Architecture ===\n")
    
    # Get event bus
    event_bus = get_event_bus(config.EVENT_BUS_CONFIG)
    print(f"Event bus initialized: {type(event_bus).__name__}")
    
    # Create agents
    print("\nCreating event-driven agents...")
    agents = {
        'orchestrator': create_agent('orchestrator', mode='event_driven'),
        'frontend': create_agent('frontend', mode='event_driven'),
        'backend': create_agent('backend', mode='event_driven'),
        'db': create_agent('db', mode='event_driven')
    }
    
    # Start agents in threads
    threads = []
    for name, agent in agents.items():
        thread = threading.Thread(target=agent.run, daemon=True)
        thread.start()
        threads.append(thread)
        print(f"Started {name} agent")
    
    # Give agents time to initialize
    time.sleep(2)
    
    # Test 1: Send a feature request
    print("\n=== Test 1: New Feature Request ===")
    feature_description = "Add user profile management with avatar upload"
    
    # Send feature request event
    event_bus.publish(Event(
        id="test-feature-1",
        type=EventType.CUSTOM,
        source="test_script",
        timestamp=time.time(),
        data={
            'event_name': 'new_feature_request',
            'description': feature_description
        }
    ))
    
    print(f"Sent feature request: {feature_description}")
    
    # Wait for processing
    time.sleep(5)
    
    # Test 2: Direct task assignment
    print("\n=== Test 2: Direct Task Assignment ===")
    
    # Assign a task directly to frontend agent
    event_bus.publish(Event(
        id="test-task-1",
        type=EventType.TASK_ASSIGNED,
        source="test_script",
        timestamp=time.time(),
        data={
            'task_id': 'test-task-1',
            'feature_id': 'test-feature',
            'description': 'Create user profile component with avatar display',
            'assigned_agent': 'frontend_agent'
        },
        correlation_id='test-task-1'
    ))
    
    print("Assigned task directly to frontend agent")
    
    # Wait for processing
    time.sleep(3)
    
    # Test 3: Database schema update event
    print("\n=== Test 3: Database Schema Update ===")
    
    # Notify about schema changes
    event_bus.publish(Event(
        id="test-schema-1",
        type=EventType.CUSTOM,
        source="test_script",
        timestamp=time.time(),
        data={
            'event_name': 'database_schema_updated',
            'migration_file': 'test_migration.sql',
            'changes': 'Added user_profiles table'
        }
    ))
    
    print("Sent database schema update notification")
    
    # Wait for reactions
    time.sleep(3)
    
    # Test 4: Check event bus statistics
    print("\n=== Event Bus Statistics ===")
    stats = event_bus.get_statistics()
    print(f"Total events processed: {stats['total_events_processed']}")
    print(f"Active subscribers: {stats['subscriber_count']}")
    print(f"Event types with subscribers: {len(stats['event_types'])}")
    
    # Test 5: System health check
    print("\n=== Test 5: System Health Check ===")
    
    event_bus.publish(Event(
        id="health-check-1",
        type=EventType.SYSTEM_HEALTH_CHECK,
        source="test_script",
        timestamp=time.time(),
        data={}
    ))
    
    print("Sent health check request")
    
    # Wait for responses
    time.sleep(2)
    
    # Test 6: Simulate task failure and retry
    print("\n=== Test 6: Task Failure and Retry ===")
    
    # Send a task that will fail
    event_bus.publish(Event(
        id="test-fail-task",
        type=EventType.TASK_ASSIGNED,
        source="test_script",
        timestamp=time.time(),
        data={
            'task_id': 'test-fail-task',
            'feature_id': 'test-feature',
            'description': 'SIMULATE_FAILURE: This task should fail',
            'assigned_agent': 'backend_agent'
        },
        correlation_id='test-fail-task'
    ))
    
    print("Sent task that should fail to test retry mechanism")
    
    # Wait for failure and retry
    time.sleep(5)
    
    # Final statistics
    print("\n=== Final Event Bus Statistics ===")
    final_stats = event_bus.get_statistics()
    print(f"Total events processed: {final_stats['total_events_processed']}")
    print(f"Queue size: {final_stats['queue_size']}")
    
    # Show event history
    print("\n=== Recent Event History ===")
    recent_events = event_bus.get_event_history(since=time.time() - 60)
    print(f"Events in last minute: {len(recent_events)}")
    
    # Group by type
    event_types = {}
    for event in recent_events:
        event_type = event.type.value
        event_types[event_type] = event_types.get(event_type, 0) + 1
    
    print("\nEvent type breakdown:")
    for event_type, count in sorted(event_types.items()):
        print(f"  {event_type}: {count}")
    
    print("\n=== Test Complete ===")
    
    # Send shutdown signal
    event_bus.publish(Event(
        id="shutdown",
        type=EventType.SYSTEM_SHUTDOWN,
        source="test_script",
        timestamp=time.time(),
        data={}
    ))
    
    # Give agents time to shutdown
    time.sleep(2)
    
    # Stop event bus
    event_bus.stop()


def test_event_filtering():
    """Test event filtering capabilities"""
    print("\n=== Testing Event Filtering ===")
    
    # Reset event bus for clean test
    from core.event_bus_factory import reset_event_bus
    reset_event_bus()
    
    event_bus = get_event_bus(config.EVENT_BUS_CONFIG)
    
    # Add filter to only allow high-priority tasks
    def priority_filter(event: Event) -> bool:
        if event.type == EventType.TASK_ASSIGNED:
            return event.data.get('priority', 'normal') == 'high'
        return True  # Allow all other events
    
    event_bus.add_filter(priority_filter)
    print("Added priority filter (only high-priority tasks)")
    
    # Track received events
    received_events = []
    
    def track_events(event: Event):
        received_events.append(event)
        print(f"Received: {event.type.value} - {event.data.get('description', '')}")
    
    event_bus.subscribe(EventType.TASK_ASSIGNED, track_events)
    
    # Send tasks with different priorities
    priorities = ['low', 'normal', 'high', 'critical']
    for i, priority in enumerate(priorities):
        event_bus.publish(Event(
            id=f"priority-test-{i}",
            type=EventType.TASK_ASSIGNED,
            source="test_script",
            timestamp=time.time(),
            data={
                'task_id': f'priority-task-{i}',
                'description': f'Task with {priority} priority',
                'priority': priority if priority != 'critical' else 'high'  # Map critical to high
            }
        ))
    
    # Wait for processing
    time.sleep(1)
    
    print(f"\nSent {len(priorities)} tasks, received {len(received_events)} after filtering")
    
    event_bus.stop()


if __name__ == "__main__":
    # Run main test
    test_event_driven_flow()
    
    # Run filtering test
    test_event_filtering()
    
    print("\nAll tests complete!")