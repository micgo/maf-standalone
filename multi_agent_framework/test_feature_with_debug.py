#!/usr/bin/env python3
"""
Test with debug output to see what's happening
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


def test_feature_debug():
    """Test with detailed debug output"""
    print("=== Testing Event-Driven Feature Processing ===\n")
    
    # Get event bus
    event_bus = get_event_bus(config.EVENT_BUS_CONFIG)
    
    # Create only orchestrator first to debug
    print("Creating orchestrator agent...")
    orchestrator = create_agent('orchestrator', mode='event_driven')
    
    # Start orchestrator
    thread = threading.Thread(target=orchestrator.run, daemon=True)
    thread.start()
    print("✓ Started orchestrator agent")
    
    # Give it time to initialize
    time.sleep(2)
    
    # First, let's publish a FEATURE_CREATED event directly
    print("\n1️⃣ Testing direct FEATURE_CREATED event...")
    
    event_bus.publish(Event(
        id="test-feature-direct",
        type=EventType.FEATURE_CREATED,
        source="test_script",
        timestamp=time.time(),
        data={
            'feature_id': 'test-123',
            'description': 'Simple test feature for dashboard'
        }
    ))
    
    time.sleep(3)
    
    # Now test the custom event path
    print("\n2️⃣ Testing CUSTOM event with new_feature_request...")
    
    event_bus.publish(Event(
        id="test-feature-custom",
        type=EventType.CUSTOM,
        source="test_script", 
        timestamp=time.time(),
        data={
            'event_name': 'new_feature_request',
            'description': 'Create user profile page with settings'
        }
    ))
    
    time.sleep(3)
    
    # Check event bus stats
    stats = event_bus.get_statistics()
    print(f"\n📊 Event Bus Stats:")
    print(f"   Total events: {stats['total_events_processed']}")
    print(f"   Subscribers by type: {stats['event_types']}")
    
    # Get event history
    history = event_bus.get_event_history()
    print(f"\n📜 Event History ({len(history)} events):")
    for event in history[-10:]:  # Last 10 events
        print(f"   {event.type.value} from {event.source}")
        if event.type == EventType.TASK_ASSIGNED:
            print(f"      → {event.data.get('assigned_agent')}: {event.data.get('description')}")
    
    print("\n=== Test Complete ===")
    
    # Shutdown
    event_bus.stop()


if __name__ == "__main__":
    test_feature_debug()