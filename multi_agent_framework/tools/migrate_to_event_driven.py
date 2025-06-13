#!/usr/bin/env python3
"""
Migration tool to convert polling agents to event-driven agents

This script helps migrate the multi-agent framework from polling
to event-driven architecture.
"""

import os
import sys
import argparse
import shutil
from datetime import datetime

# Add framework to path
framework_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, framework_root)


def backup_file(file_path: str) -> str:
    """Create a backup of a file"""
    backup_path = f"{file_path}.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    shutil.copy2(file_path, backup_path)
    print(f"Created backup: {backup_path}")
    return backup_path


def update_config_file(enable_event_driven: bool = True):
    """Update the config file to enable/disable event-driven mode"""
    config_path = os.path.join(framework_root, 'config.py')
    
    # Backup config
    backup_file(config_path)
    
    # Read config
    with open(config_path, 'r') as f:
        content = f.read()
    
    # Update EVENT_DRIVEN_MODE
    if 'EVENT_DRIVEN_MODE = ' in content:
        content = content.replace(
            f'EVENT_DRIVEN_MODE = {not enable_event_driven}',
            f'EVENT_DRIVEN_MODE = {enable_event_driven}'
        )
    else:
        # Add if not present
        content += f"\n\n# Event-driven mode configuration\nEVENT_DRIVEN_MODE = {enable_event_driven}\n"
    
    # Write updated config
    with open(config_path, 'w') as f:
        f.write(content)
    
    print(f"Updated config.py: EVENT_DRIVEN_MODE = {enable_event_driven}")


def generate_agent_template(agent_name: str, class_name: str) -> str:
    """Generate event-driven agent template"""
    return f'''"""
Event-Driven {class_name}

This is the event-driven version of the {agent_name} agent.
"""

import os
import sys
from typing import Dict, Any

# Add framework to path
framework_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, framework_root)

from multi_agent_framework.agents.event_driven_base_agent import EventDrivenBaseAgent
from multi_agent_framework.core.event_bus_interface import Event, EventType


class EventDriven{class_name}(EventDrivenBaseAgent):
    """
    Event-driven {agent_name} agent
    """
    
    def __init__(self, model_provider="gemini", model_name="gemini-2.0-flash-exp"):
        super().__init__("{agent_name}", model_provider, model_name)
    
    def _subscribe_to_events(self):
        """Subscribe to {agent_name}-specific events"""
        super()._subscribe_to_events()
        
        # Subscribe to task retry events
        self.event_bus.subscribe(EventType.TASK_RETRY, self._handle_task_retry)
    
    def _handle_task_retry(self, event: Event):
        """Handle task retry events"""
        data = event.data
        
        # Check if retry is for this agent
        if data.get("assigned_agent") != self.name:
            return
        
        task_id = data.get("task_id")
        if not task_id:
            return
        
        print(f"{{self.name}}: Retrying task {{task_id}}")
        
        # Process as a new task assignment
        self._handle_task_assigned(Event(
            id=event.id,
            type=EventType.TASK_ASSIGNED,
            source=event.source,
            timestamp=event.timestamp,
            data=data,
            correlation_id=event.correlation_id
        ))
    
    def process_task(self, task_id: str, task_data: Dict[str, Any]) -> Any:
        """
        Process {agent_name} tasks
        
        Args:
            task_id: Unique task identifier
            task_data: Task information including description
            
        Returns:
            Task result
        """
        description = task_data.get('description', '')
        print(f"{{self.name}}: Processing task - {{description}}")
        
        try:
            # TODO: Implement actual task processing logic
            # This is where you would migrate the logic from the polling agent
            
            result = {{
                'status': 'success',
                'message': f'Task completed by {{self.name}}'
            }}
            
            return result
            
        except Exception as e:
            error_msg = f"Error processing task: {{str(e)}}"
            print(f"{{self.name}}: {{error_msg}}")
            raise


if __name__ == "__main__":
    agent = EventDriven{class_name}()
    agent.run()
'''


def create_event_driven_agent(agent_type: str, force: bool = False):
    """Create an event-driven version of an agent"""
    # Map agent types to class names
    agent_class_map = {
        'backend': 'BackendAgent',
        'db': 'DatabaseAgent',
        'qa': 'QAAgent',
        'security': 'SecurityAgent',
        'devops': 'DevOpsAgent',
        'docs': 'DocumentationAgent',
        'ux_ui': 'UXUIAgent'
    }
    
    if agent_type not in agent_class_map:
        print(f"Unknown agent type: {agent_type}")
        return False
    
    class_name = agent_class_map[agent_type]
    agent_name = f"{agent_type}_agent"
    
    # Output path
    output_path = os.path.join(
        framework_root, 
        'agents', 
        f'event_driven_{agent_name}.py'
    )
    
    # Check if already exists
    if os.path.exists(output_path) and not force:
        print(f"Event-driven agent already exists: {output_path}")
        print("Use --force to overwrite")
        return False
    
    # Generate template
    template = generate_agent_template(agent_name, class_name)
    
    # Write file
    with open(output_path, 'w') as f:
        f.write(template)
    
    print(f"Created event-driven agent: {output_path}")
    return True


def show_migration_status():
    """Show the current migration status"""
    from core.agent_factory import AgentFactory
    
    print("\n=== Migration Status ===")
    print("\nAgent Implementation Status:")
    print("-" * 50)
    
    for agent_type in AgentFactory.AGENT_MAPPINGS:
        polling_module, _ = AgentFactory.AGENT_MAPPINGS[agent_type]['polling']
        event_module, _ = AgentFactory.AGENT_MAPPINGS[agent_type].get('event_driven', ('', ''))
        
        # Check if files exist
        polling_exists = False
        event_exists = False
        
        try:
            __import__(polling_module)
            polling_exists = True
        except:
            pass
        
        try:
            if event_module:
                __import__(event_module)
                event_exists = True
        except:
            pass
        
        status = "✓ Migrated" if event_exists else "⚠ Pending"
        print(f"{agent_type:15} Polling: {'✓' if polling_exists else '✗'}  "
              f"Event-Driven: {'✓' if event_exists else '✗'}  "
              f"Status: {status}")
    
    # Check current mode
    try:
        import config
        mode = "Event-Driven" if config.EVENT_DRIVEN_MODE else "Polling"
        print(f"\nCurrent Mode: {mode}")
    except:
        print("\nCurrent Mode: Unknown")
    
    print("-" * 50)


def main():
    parser = argparse.ArgumentParser(
        description="Migrate multi-agent framework to event-driven architecture"
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Status command
    status_parser = subparsers.add_parser('status', help='Show migration status')
    
    # Enable command
    enable_parser = subparsers.add_parser('enable', help='Enable event-driven mode')
    
    # Disable command
    disable_parser = subparsers.add_parser('disable', help='Disable event-driven mode')
    
    # Create command
    create_parser = subparsers.add_parser('create', help='Create event-driven agent')
    create_parser.add_argument('agent_type', 
                              choices=['backend', 'db', 'qa', 'security', 'devops', 'docs', 'ux_ui'],
                              help='Type of agent to create')
    create_parser.add_argument('--force', action='store_true', 
                              help='Overwrite existing agent')
    
    # Create all command
    create_all_parser = subparsers.add_parser('create-all', 
                                             help='Create all event-driven agents')
    create_all_parser.add_argument('--force', action='store_true',
                                  help='Overwrite existing agents')
    
    args = parser.parse_args()
    
    if args.command == 'status':
        show_migration_status()
    
    elif args.command == 'enable':
        update_config_file(enable_event_driven=True)
        print("\nEvent-driven mode ENABLED")
        print("Restart your agents to use event-driven architecture")
    
    elif args.command == 'disable':
        update_config_file(enable_event_driven=False)
        print("\nEvent-driven mode DISABLED")
        print("Agents will use polling architecture")
    
    elif args.command == 'create':
        success = create_event_driven_agent(args.agent_type, args.force)
        if success:
            print(f"\nNext steps:")
            print(f"1. Implement the process_task method in the new agent")
            print(f"2. Test the agent in event-driven mode")
            print(f"3. Run 'python migrate_to_event_driven.py enable' when ready")
    
    elif args.command == 'create-all':
        agent_types = ['backend', 'db', 'qa', 'security', 'devops', 'docs', 'ux_ui']
        created = 0
        
        for agent_type in agent_types:
            if create_event_driven_agent(agent_type, args.force):
                created += 1
        
        print(f"\nCreated {created} event-driven agent templates")
        print("Remember to implement the process_task method in each agent")
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()