#!/usr/bin/env python3
"""
Test the event-driven agents with a real feature request
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


def test_real_feature():
    """Test with a real feature request"""
    print("=== Testing Event-Driven Agents with Real Feature ===\n")
    
    # Get event bus
    event_bus = get_event_bus(config.EVENT_BUS_CONFIG)
    
    # Create only the migrated agents
    print("Creating migrated event-driven agents...")
    agents = {
        'orchestrator': create_agent('orchestrator', mode='event_driven'),
        'frontend': create_agent('frontend', mode='event_driven'),
        'backend': create_agent('backend', mode='event_driven'),
        'db': create_agent('db', mode='event_driven')
    }
    
    # Start agents
    threads = []
    for name, agent in agents.items():
        thread = threading.Thread(target=agent.run, daemon=True)
        thread.start()
        threads.append(thread)
        print(f"✓ Started {name} agent")
    
    # Give agents time to initialize
    time.sleep(2)
    
    # Monitor events
    event_log = []
    
    def log_events(event: Event):
        event_log.append({
            'time': time.time(),
            'type': event.type.value,
            'source': event.source,
            'data': event.data
        })
        
        # Print interesting events
        if event.type in [EventType.TASK_ASSIGNED, EventType.TASK_COMPLETED, 
                         EventType.TASK_FAILED, EventType.FEATURE_CREATED]:
            print(f"\n📌 {event.type.value}: {event.data.get('description', '')}")
            if event.source != 'orchestrator':
                print(f"   Source: {event.source}")
    
    # Subscribe to all event types for monitoring
    for event_type in EventType:
        event_bus.subscribe(event_type, log_events)
    
    # Send a real feature request
    feature_description = "Create a user dashboard that shows recent activity, statistics, and quick actions"
    
    print(f"\n🚀 Sending feature request: {feature_description}\n")
    
    event_bus.publish(Event(
        id="real-feature-1",
        type=EventType.CUSTOM,
        source="test_script",
        timestamp=time.time(),
        data={
            'event_name': 'new_feature_request',
            'description': feature_description
        }
    ))
    
    # Wait for processing
    print("⏳ Waiting for agents to process the feature...")
    time.sleep(10)
    
    # Show summary
    print("\n=== Processing Summary ===")
    
    # Count events by type
    event_counts = {}
    for entry in event_log:
        event_type = entry['type']
        event_counts[event_type] = event_counts.get(event_type, 0) + 1
    
    print("\nEvent Statistics:")
    for event_type, count in sorted(event_counts.items()):
        if count > 0:
            print(f"  {event_type}: {count}")
    
    # Show task assignments
    print("\nTask Assignments:")
    task_assignments = [e for e in event_log if e['type'] == 'task.assigned']
    for assignment in task_assignments:
        agent = assignment['data'].get('assigned_agent', 'unknown')
        desc = assignment['data'].get('description', 'no description')
        print(f"  → {agent}: {desc}")
    
    # Show completed tasks
    print("\nCompleted Tasks:")
    completed = [e for e in event_log if e['type'] == 'task.completed']
    for task in completed:
        print(f"  ✓ {task['source']}: {task['data'].get('message', 'completed')}")
    
    # Show failed tasks
    failed = [e for e in event_log if e['type'] == 'task.failed']
    if failed:
        print("\nFailed Tasks:")
        for task in failed:
            print(f"  ✗ {task['source']}: {task['data'].get('error', 'unknown error')}")
    
    print("\n=== Test Complete ===")
    
    # Shutdown
    event_bus.publish(Event(
        id="shutdown",
        type=EventType.SYSTEM_SHUTDOWN,
        source="test_script",
        timestamp=time.time(),
        data={}
    ))
    
    time.sleep(2)
    event_bus.stop()


if __name__ == "__main__":
    test_real_feature()