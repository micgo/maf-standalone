#!/usr/bin/env python3
"""
Simple script to check migration status
"""

import os
import glob

def check_migration_status():
    """Check which agents have event-driven versions"""
    
    base_dir = os.path.dirname(__file__)
    agents_dir = os.path.join(base_dir, 'agents')
    specialized_dir = os.path.join(agents_dir, 'specialized')
    
    # Find all agent files
    polling_agents = []
    event_driven_agents = []
    
    # Check main agents directory
    for file in glob.glob(os.path.join(agents_dir, '*.py')):
        filename = os.path.basename(file)
        if filename.startswith('event_driven_'):
            agent_name = filename.replace('event_driven_', '').replace('.py', '')
            event_driven_agents.append(agent_name)
        elif filename.endswith('_agent.py') and not filename.startswith('base_'):
            agent_name = filename.replace('.py', '')
            polling_agents.append(agent_name)
    
    # Check specialized directory
    for file in glob.glob(os.path.join(specialized_dir, '*_agent.py')):
        filename = os.path.basename(file)
        agent_name = filename.replace('.py', '')
        if agent_name not in polling_agents:
            polling_agents.append(agent_name)
    
    print("\n=== Migration Status ===")
    print("\nAgent Implementation Status:")
    print("-" * 50)
    
    # Check each polling agent
    for agent in polling_agents:
        has_event_driven = agent in event_driven_agents
        status = "✓ Migrated" if has_event_driven else "⚠ Pending"
        print(f"{agent:25} Event-Driven: {'✓' if has_event_driven else '✗'}  Status: {status}")
    
    # Check config
    try:
        import config
        mode = "Event-Driven" if config.EVENT_DRIVEN_MODE else "Polling"
        print(f"\nCurrent Mode: {mode}")
    except:
        print("\nCurrent Mode: Unknown")
    
    print("-" * 50)
    
    # Summary
    migrated = sum(1 for agent in polling_agents if agent in event_driven_agents)
    total = len(polling_agents)
    print(f"\nProgress: {migrated}/{total} agents migrated ({migrated/total*100:.0f}%)")
    
    # List pending agents
    pending = [agent for agent in polling_agents if agent not in event_driven_agents]
    if pending:
        print("\nPending migrations:")
        for agent in pending:
            print(f"  - {agent}")

if __name__ == "__main__":
    check_migration_status()