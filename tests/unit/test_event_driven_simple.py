#!/usr/bin/env python3
"""
Simple test of event-driven architecture
"""

import sys
import os
import time
import threading

# Add framework to path
framework_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, framework_root)

from multi_agent_framework.core.agent_factory import create_agent
from multi_agent_framework.core.event_bus_factory import get_event_bus
from multi_agent_framework.core.event_bus_interface import Event, EventType
from multi_agent_framework import config


def test_simple():
    """Simple test without waiting for LLM"""
    print("=== Simple Event-Driven Test ===\n")
    
    # Set event-driven mode
    config.EVENT_DRIVEN_MODE = True
    
    # Get event bus
    event_bus = get_event_bus(config.EVENT_BUS_CONFIG)
    
    # Create a test agent that doesn't use LLM
    print("Creating test agents...")
    
    # Mock task data
    test_task = {
        'task_id': 'test-123',
        'feature_id': 'feat-001', 
        'description': 'Create login component',
        'assigned_agent': 'frontend_agent'
    }
    
    # Subscribe to events to monitor
    events_received = []
    
    def monitor_events(event: Event):
        events_received.append({
            'type': event.type.value,
            'source': event.source,
            'data': event.data
        })
        print(f"📨 Event: {event.type.value} from {event.source}")
    
    # Subscribe to all events
    for event_type in [EventType.TASK_ASSIGNED, EventType.TASK_STARTED, 
                       EventType.TASK_COMPLETED, EventType.TASK_FAILED]:
        event_bus.subscribe(event_type, monitor_events)
    
    # Test 1: Publish task assignment
    print("\n1️⃣ Publishing TASK_ASSIGNED event...")
    
    event_bus.publish(Event(
        id="test-event-1",
        type=EventType.TASK_ASSIGNED,
        source="test_script",
        timestamp=time.time(),
        data=test_task,
        correlation_id=test_task['task_id']
    ))
    
    time.sleep(1)
    
    # Test 2: Simulate task completion
    print("\n2️⃣ Publishing TASK_COMPLETED event...")
    
    event_bus.publish(Event(
        id="test-event-2", 
        type=EventType.TASK_COMPLETED,
        source="frontend_agent",
        timestamp=time.time(),
        data={
            'task_id': test_task['task_id'],
            'result': {'path': '/components/Login.tsx', 'status': 'success'}
        },
        correlation_id=test_task['task_id']
    ))
    
    time.sleep(1)
    
    # Summary
    print(f"\n📊 Total events received: {len(events_received)}")
    for event in events_received:
        print(f"   - {event['type']} from {event['source']}")
    
    # Test that agents can communicate
    print("\n3️⃣ Testing agent event handling...")
    
    # Create just frontend agent
    frontend = create_agent('frontend', mode='event_driven')
    thread = threading.Thread(target=frontend.run, daemon=True)
    thread.start()
    
    time.sleep(2)
    
    # Send task to frontend
    print("Sending task to frontend agent...")
    event_bus.publish(Event(
        id="real-task-1",
        type=EventType.TASK_ASSIGNED,
        source="orchestrator",
        timestamp=time.time(),
        data={
            'task_id': 'real-task-1',
            'feature_id': 'feat-002',
            'description': 'Create user profile component', 
            'assigned_agent': 'frontend_agent'
        }
    ))
    
    # Wait for processing
    time.sleep(3)
    
    print("\n✅ Test complete!")
    
    # Shutdown
    event_bus.publish(Event(
        id="shutdown",
        type=EventType.SYSTEM_SHUTDOWN,
        source="test_script",
        timestamp=time.time(),
        data={}
    ))
    
    time.sleep(1)
    event_bus.stop()


if __name__ == "__main__":
    test_simple()