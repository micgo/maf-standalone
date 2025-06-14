#!/usr/bin/env python3
"""
Test the complete working flow with proper timing
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


def test_working_flow():
    """Test the complete event-driven flow"""
    print("=== Testing Complete Event-Driven Flow ===\n")
    
    # Get event bus and ensure it's started
    event_bus = get_event_bus(config.EVENT_BUS_CONFIG)
    time.sleep(1)  # Give event bus time to fully start
    
    # Create all migrated agents
    print("Creating event-driven agents...")
    agents = {}
    agent_types = ['orchestrator', 'frontend', 'backend', 'db']
    
    for agent_type in agent_types:
        agents[agent_type] = create_agent(agent_type, mode='event_driven')
        print(f"✓ Created {agent_type} agent")
    
    # Start all agents
    print("\nStarting agents...")
    threads = []
    for name, agent in agents.items():
        thread = threading.Thread(target=agent.run, daemon=True)
        thread.start()
        threads.append(thread)
        print(f"✓ Started {name} agent")
    
    # IMPORTANT: Give agents time to fully initialize and subscribe to events
    print("\n⏳ Waiting for agents to initialize...")
    time.sleep(3)
    
    # Verify subscriptions
    stats = event_bus.get_statistics()
    print(f"\n📊 Event Bus Ready:")
    print(f"   Active subscribers: {stats['subscriber_count']}")
    print(f"   Event types monitored: {len(stats['event_types'])}")
    
    # Test 1: Send a feature request via custom event
    print("\n=== Test 1: Feature Request via Custom Event ===")
    
    feature_desc = "Create a notification system with email and in-app alerts"
    
    event_bus.publish(Event(
        id="feature-request-1",
        type=EventType.CUSTOM,
        source="client",
        timestamp=time.time(),
        data={
            'event_name': 'new_feature_request',
            'description': feature_desc
        }
    ))
    
    print(f"📤 Sent feature request: {feature_desc}")
    
    # Wait for processing (LLM calls can take time)
    print("⏳ Processing...")
    time.sleep(15)
    
    # Check what happened
    print("\n📋 Checking results...")
    history = event_bus.get_event_history()
    
    # Count event types
    event_counts = {}
    for event in history:
        event_type = event.type.value
        event_counts[event_type] = event_counts.get(event_type, 0) + 1
    
    print("\nEvent counts:")
    for event_type, count in sorted(event_counts.items()):
        print(f"  {event_type}: {count}")
    
    # Show task assignments
    task_events = [e for e in history if e.type == EventType.TASK_ASSIGNED]
    if task_events:
        print(f"\n✅ Tasks assigned: {len(task_events)}")
        for task in task_events:
            agent = task.data.get('assigned_agent', 'unknown')
            desc = task.data.get('description', 'no description')[:60]
            print(f"   → {agent}: {desc}...")
    else:
        print("\n⚠️  No tasks were assigned")
    
    # Test 2: Direct feature created event
    print("\n=== Test 2: Direct Feature Created Event ===")
    
    event_bus.publish(Event(
        id="direct-feature-1",
        type=EventType.FEATURE_CREATED,
        source="admin",
        timestamp=time.time(),
        data={
            'feature_id': 'feat-001',
            'description': 'Add dark mode toggle to settings'
        }
    ))
    
    print("📤 Sent direct FEATURE_CREATED event")
    
    time.sleep(5)
    
    # Check new events
    new_history = event_bus.get_event_history(since=time.time() - 6)
    new_tasks = [e for e in new_history if e.type == EventType.TASK_ASSIGNED]
    
    if new_tasks:
        print(f"\n✅ New tasks assigned: {len(new_tasks)}")
    else:
        print("\n⚠️  No new tasks from direct event")
    
    print("\n=== Test Complete ===")
    
    # Graceful shutdown
    event_bus.publish(Event(
        id="shutdown",
        type=EventType.SYSTEM_SHUTDOWN,
        source="test_script",
        timestamp=time.time(),
        data={}
    ))
    
    time.sleep(2)
    event_bus.stop()
    print("\n✅ Shutdown complete")


if __name__ == "__main__":
    test_working_flow()