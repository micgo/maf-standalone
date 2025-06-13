#!/usr/bin/env python3
"""
Main script to run the multi-agent framework

Supports both polling and event-driven modes based on configuration.
"""

import os
import sys
import argparse
import threading
import time
from typing import Dict, List

# Add framework to path
framework_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, framework_root)

from multi_agent_framework import config
from multi_agent_framework.core.agent_factory import AgentFactory, create_agent
from multi_agent_framework.core.event_bus_factory import get_event_bus
from multi_agent_framework.core.event_bus_interface import Event, EventType


def run_polling_agents(agent_types: List[str]):
    """Run agents in polling mode"""
    print("Starting agents in POLLING mode...")
    
    agents = {}
    threads = []
    
    # Create and start agents
    for agent_type in agent_types:
        try:
            agent = create_agent(agent_type, mode='polling')
            agents[agent_type] = agent
            
            # Start agent in thread
            thread = threading.Thread(target=agent.run, daemon=True)
            thread.start()
            threads.append(thread)
            
            print(f"Started {agent_type} agent in polling mode")
            
        except Exception as e:
            print(f"Failed to start {agent_type}: {e}")
    
    return agents, threads


def run_event_driven_agents(agent_types: List[str]):
    """Run agents in event-driven mode"""
    print("Starting agents in EVENT-DRIVEN mode...")
    
    # Initialize event bus
    event_bus = get_event_bus(config.EVENT_BUS_CONFIG)
    print(f"Event bus initialized: {type(event_bus).__name__}")
    
    agents = {}
    threads = []
    
    # Create and start agents
    for agent_type in agent_types:
        try:
            agent = create_agent(agent_type, mode='event_driven')
            agents[agent_type] = agent
            
            # Start agent in thread
            thread = threading.Thread(target=agent.run, daemon=True)
            thread.start()
            threads.append(thread)
            
            print(f"Started {agent_type} agent in event-driven mode")
            
        except Exception as e:
            print(f"Failed to start {agent_type}: {e}")
    
    return agents, threads


def send_test_feature(description: str):
    """Send a test feature request"""
    if config.EVENT_DRIVEN_MODE:
        # Event-driven mode
        event_bus = get_event_bus()
        
        # Send custom event for new feature
        event_bus.publish(Event(
            id=f"test-feature-{time.time()}",
            type=EventType.CUSTOM,
            source="test_client",
            timestamp=time.time(),
            data={
                'event_name': 'new_feature_request',
                'description': description
            }
        ))
        
        print(f"Sent feature request via event: {description}")
        
    else:
        # Polling mode - send message to orchestrator
        from multi_agent_framework.core.message_bus import MessageBus
        
        message_bus = MessageBus()
        message_bus.send_message("orchestrator", {
            "sender": "test_client",
            "recipient": "orchestrator",
            "type": "new_feature",
            "content": description,
            "timestamp": time.time()
        })
        
        print(f"Sent feature request via message: {description}")


def monitor_event_bus():
    """Monitor event bus statistics"""
    if not config.EVENT_DRIVEN_MODE:
        return
    
    event_bus = get_event_bus()
    
    while True:
        try:
            stats = event_bus.get_statistics()
            print(f"\n=== Event Bus Stats ===")
            print(f"Total events: {stats['total_events_processed']}")
            print(f"Queue size: {stats['queue_size']}")
            print(f"Subscribers: {stats['subscriber_count']}")
            print(f"Event types: {stats['event_types']}")
            print("=" * 23)
            
            time.sleep(30)  # Update every 30 seconds
            
        except Exception as e:
            print(f"Error monitoring event bus: {e}")
            time.sleep(30)


def main():
    parser = argparse.ArgumentParser(description="Run the multi-agent framework")
    
    parser.add_argument('--agents', nargs='+', 
                       choices=['orchestrator', 'frontend', 'backend', 'db', 
                               'qa', 'security', 'devops', 'docs', 'ux_ui', 'all'],
                       default=['all'],
                       help='Agents to start (default: all)')
    
    parser.add_argument('--mode', choices=['polling', 'event_driven', 'auto'],
                       default='auto',
                       help='Operating mode (default: auto - uses config)')
    
    parser.add_argument('--test-feature', type=str,
                       help='Send a test feature request after startup')
    
    parser.add_argument('--monitor', action='store_true',
                       help='Enable event bus monitoring (event-driven mode only)')
    
    args = parser.parse_args()
    
    # Determine mode
    if args.mode == 'auto':
        use_event_driven = config.EVENT_DRIVEN_MODE
    else:
        use_event_driven = (args.mode == 'event_driven')
    
    # Get agent list
    if 'all' in args.agents:
        agent_types = ['orchestrator', 'frontend', 'backend', 'db', 
                      'qa', 'security', 'devops', 'docs', 'ux_ui']
    else:
        agent_types = args.agents
    
    # Ensure orchestrator is included
    if 'orchestrator' not in agent_types:
        agent_types.insert(0, 'orchestrator')
    
    # Start agents
    if use_event_driven:
        agents, threads = run_event_driven_agents(agent_types)
    else:
        agents, threads = run_polling_agents(agent_types)
    
    print(f"\nStarted {len(agents)} agents in {'EVENT-DRIVEN' if use_event_driven else 'POLLING'} mode")
    
    # Wait a bit for agents to initialize
    time.sleep(2)
    
    # Send test feature if requested
    if args.test_feature:
        send_test_feature(args.test_feature)
    
    # Start monitoring if requested
    if args.monitor and use_event_driven:
        monitor_thread = threading.Thread(target=monitor_event_bus, daemon=True)
        monitor_thread.start()
    
    # Keep main thread alive
    try:
        print("\nAgents are running. Press Ctrl+C to stop...")
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\nShutting down agents...")
        
        if use_event_driven:
            # Send shutdown event
            event_bus = get_event_bus()
            event_bus.publish(Event(
                id="shutdown",
                type=EventType.SYSTEM_SHUTDOWN,
                source="main",
                timestamp=time.time(),
                data={}
            ))
            
            # Give agents time to shutdown cleanly
            time.sleep(2)
            
            # Stop event bus
            event_bus.stop()
        
        print("Shutdown complete")


if __name__ == "__main__":
    main()