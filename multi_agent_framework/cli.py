#!/usr/bin/env python3
"""
Multi-Agent Framework CLI

Command-line interface for managing the multi-agent framework.
"""

import click
import os
import sys
import json
import subprocess
import time
from pathlib import Path
from typing import Optional

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from multi_agent_framework.core.project_config import ProjectConfig
from multi_agent_framework.core.message_bus_configurable import MessageBus
from multi_agent_framework.core.agent_factory import create_agent, AgentFactory
from multi_agent_framework import config
from multi_agent_framework.core.error_handler import error_handler, ErrorCategory, ErrorLevel
from multi_agent_framework.core.progress_tracker import get_progress_tracker


def _get_recommended_agents(project_type: str) -> list:
    """Get recommended agents based on project type."""
    base_agents = ['orchestrator']
    
    type_specific = {
        'nextjs': ['frontend_agent', 'backend_agent', 'ux_ui_agent'],
        'react': ['frontend_agent', 'ux_ui_agent'],
        'django': ['backend_agent', 'db_agent', 'frontend_agent'],
        'flask': ['backend_agent', 'db_agent'],
        'python': ['backend_agent'],
        'auto': ['frontend_agent', 'backend_agent']
    }
    
    return base_agents + type_specific.get(project_type, type_specific['auto'])


@click.group()
@click.version_option(version="0.1.0", prog_name="Multi-Agent Framework")
def cli():
    """Multi-Agent Framework - Autonomous software development with AI agents.
    
    Quick start:
      maf init          Initialize framework in current directory
      maf launch        Start agents (uses polling mode by default)
      maf trigger       Request a new feature to be built
      maf status        Check agent health and progress
      
    Learn more:
      maf modes         Understand polling vs event-driven modes
      maf --help        Show all available commands
    """
    pass


@cli.command()
@click.argument('project_path', required=False)
@click.option('--name', '-n', help='Project name')
@click.option('--type', '-t', help='Project type (nextjs, react, django, etc.)')
def init(project_path: Optional[str], name: Optional[str], type: Optional[str]):
    """Initialize the framework for a project."""
    # Use current directory if no path provided
    project_path = project_path or os.getcwd()
    project_path = os.path.abspath(project_path)
    
    if not os.path.exists(project_path):
        click.echo(f"Error: Project path does not exist: {project_path}")
        sys.exit(1)
    
    # Initialize project configuration
    config = ProjectConfig.initialize_project(project_path)
    
    # Update with provided options
    updates = {}
    if name:
        updates['project_name'] = name
    if type:
        updates['project_type'] = type
    
    if updates:
        config.update_config(updates)
    
    # Create .env.example if it doesn't exist
    env_example_path = os.path.join(project_path, '.env.example')
    if not os.path.exists(env_example_path):
        with open(env_example_path, 'w') as f:
            f.write("""# Multi-Agent Framework Environment Variables

# LLM API Keys (at least one required)
GEMINI_API_KEY=your_gemini_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here
OPENAI_API_KEY=your_openai_api_key_here

# Optional: Override event bus type
# EVENT_BUS_TYPE=kafka
# KAFKA_BOOTSTRAP_SERVERS=localhost:9092
""")
        click.echo(f"Created .env.example - copy to .env and add your API keys")
    
    click.echo(f"\n✅ Framework initialized successfully!")
    click.echo(f"")
    click.echo(f"📋 Configuration:")
    click.echo(f"   Project: {config.config['project_name']}")
    click.echo(f"   Type: {config.config['project_type']}")
    click.echo(f"   Default mode: {config.get_default_mode()} (recommended)")
    click.echo(f"")
    click.echo(f"🚀 Next steps:")
    click.echo(f"  1. Copy .env.example to .env and add your API keys")
    click.echo(f"  2. Run 'maf launch' to start the agents")
    click.echo(f"  3. Run 'maf trigger <feature>' to start development")
    click.echo(f"")
    click.echo(f"💡 Tips:")
    click.echo(f"  - Use 'maf launch --mode event' for experimental event-driven mode")
    click.echo(f"  - Use 'maf config' to view/modify configuration")
    click.echo(f"  - Run 'maf status' to check agent health")


@cli.command()
@click.option('--project', '-p', help='Project path (default: current directory)')
@click.option('--agents', '-a', multiple=True, help='Specific agents to launch')
@click.option('--mode', '-m', type=click.Choice(['polling', 'event']), help='Agent mode (default from config, polling=stable, event=experimental)')
def launch(project: Optional[str], agents: tuple, mode: Optional[str]):
    """Launch the multi-agent framework."""
    project_path = project or os.getcwd()
    project_config = ProjectConfig(project_path)
    
    # Use mode from config if not specified
    if mode is None:
        mode = project_config.get_default_mode()
    
    click.echo(f"🚀 Launching Multi-Agent Framework")
    click.echo(f"   Project: {project_config.config['project_name']}")
    click.echo(f"   Path: {project_path}")
    click.echo(f"   Mode: {mode} {'(recommended for stability)' if mode == 'polling' else '(experimental - may have issues)'}")
    
    # Check for .env file
    env_path = os.path.join(project_path, '.env')
    if not os.path.exists(env_path):
        error_handler.handle_error(
            FileNotFoundError(".env file not found"),
            ErrorCategory.FILE_SYSTEM,
            {'file_path': env_path},
            ErrorLevel.ERROR
        )
        click.echo("   Copy .env.example to .env and add your API keys")
        sys.exit(1)
    
    # Determine which agents to launch
    if agents:
        agent_list = list(agents)
    else:
        agent_list = project_config.get_enabled_agents()
    
    # Check for critical agents
    critical_agents = ['orchestrator']
    missing_critical = [agent for agent in critical_agents if agent not in agent_list]
    
    if missing_critical:
        click.echo(f"\n⚠️  Warning: Critical agents missing: {', '.join(missing_critical)}")
        click.echo("   The orchestrator agent is required to coordinate other agents.")
        if click.confirm("Add orchestrator to the agent list?"):
            agent_list.insert(0, 'orchestrator')
    
    # Recommend agents based on project type
    project_type = project_config.config.get('project_type', 'auto')
    recommended_agents = _get_recommended_agents(project_type)
    missing_recommended = [agent for agent in recommended_agents if agent not in agent_list]
    
    if missing_recommended:
        click.echo(f"\n💡 Tip: For {project_type} projects, consider adding: {', '.join(missing_recommended)}")
    
    click.echo(f"\nStarting agents: {', '.join(agent_list)}")
    
    # Set mode in config
    config.EVENT_DRIVEN_MODE = (mode == 'event')
    
    # Initialize message bus
    message_bus = MessageBus(project_config.get_message_queue_dir())
    message_bus.initialize_agent_inboxes(agent_list)
    
    # Launch agents
    from multi_agent_framework.core.agent_factory import create_agent
    import threading
    
    threads = []
    for agent_name in agent_list:
        try:
            # Create agent with project config
            agent = create_agent(
                agent_name.replace('_agent', ''),
                mode='event_driven' if mode == 'event' else 'polling',
                project_config=project_config
            )
            
            # Start agent in thread
            thread = threading.Thread(target=agent.run, daemon=True)
            thread.start()
            threads.append(thread)
            
            click.echo(f"✓ Started {agent_name}")
            
        except Exception as e:
            error_handler.handle_error(
                e,
                ErrorCategory.AGENT_COMMUNICATION,
                {'agent_name': agent_name, 'details': 'during startup'},
                ErrorLevel.ERROR
            )
    
    if threads:
        click.echo("\n✅ Agents are running. Press Ctrl+C to stop...")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            click.echo("\n👋 Shutting down agents...")
    else:
        click.echo("\n❌ No agents were started")


@cli.command()
@click.argument('feature_description')
@click.option('--project', '-p', help='Project path (default: current directory)')
@click.option('--wait', '-w', is_flag=True, help='Wait and show progress')
def trigger(feature_description: str, project: Optional[str], wait: bool):
    """Trigger development of a new feature."""
    project_path = project or os.getcwd()
    project_config = ProjectConfig(project_path)
    
    click.echo(f"📝 Creating new feature request: {feature_description}")
    
    # Create message bus
    message_bus = MessageBus(project_config.get_message_queue_dir())
    
    # Send feature request to orchestrator
    message = {
        "sender": "cli",
        "recipient": "orchestrator",
        "type": "new_feature",
        "content": feature_description,
        "timestamp": time.time()
    }
    
    message_bus.send_message("orchestrator", message)
    
    click.echo("✅ Feature request sent to orchestrator")
    
    if wait:
        click.echo("\n⏳ Waiting for agents to start processing...\n")
        time.sleep(2)  # Give agents time to start
        
        # Show live progress
        state_file = project_config.get_state_file_path()
        progress_tracker = get_progress_tracker(state_file)
        
        try:
            with click.progressbar(length=100, label='Overall Progress', show_eta=True) as bar:
                last_progress = 0
                no_progress_count = 0
                
                while last_progress < 100:
                    # Get latest feature
                    features = progress_tracker.get_all_features()
                    if features:
                        latest_feature = features[0]  # Most recent
                        current_progress = latest_feature['feature']['progress']
                        
                        # Update bar
                        if current_progress > last_progress:
                            bar.update(current_progress - last_progress)
                            last_progress = current_progress
                            no_progress_count = 0
                        else:
                            no_progress_count += 1
                            
                        # Break if no progress for too long
                        if no_progress_count > 60:  # 60 seconds
                            click.echo("\n⚠️  No progress detected for 60 seconds")
                            break
                            
                    time.sleep(1)
                    
            # Show final status
            click.echo("\n")
            progress_tracker.display_progress(detailed=True)
            
        except KeyboardInterrupt:
            click.echo("\n\n⚠️  Progress monitoring interrupted")
            click.echo("   Run 'maf status' to check progress")
    else:
        click.echo("   Run 'maf status' to monitor progress")


@cli.command()
@click.option('--project', '-p', help='Project path (default: current directory)')
@click.option('--detailed', '-d', is_flag=True, help='Show detailed status')
def status(project: Optional[str], detailed: bool):
    """Check the status of the multi-agent framework."""
    project_path = project or os.getcwd()
    project_config = ProjectConfig(project_path)
    
    click.echo(f"📊 Multi-Agent Framework Status")
    click.echo(f"   Project: {project_config.config['project_name']}")
    
    # Check message queues
    message_bus = MessageBus(project_config.get_message_queue_dir())
    queue_status = message_bus.get_queue_status()
    
    click.echo(f"\n📬 Message Queues:")
    for agent, count in queue_status.items():
        status = "✓" if count == 0 else f"📨 {count} messages"
        click.echo(f"   {agent}: {status}")
    
    # Show progress using progress tracker
    state_file = project_config.get_state_file_path()
    progress_tracker = get_progress_tracker(state_file)
    
    # Get feature counts
    active, total = progress_tracker.get_active_features_count()
    
    if total > 0:
        click.echo(f"\n📋 Development Progress:")
        click.echo(f"   Active features: {active}")
        click.echo(f"   Total features: {total}")
        
        # Show progress bars
        progress_tracker.display_progress(detailed=detailed)
    else:
        click.echo(f"\n📋 No features in progress (use 'maf trigger' to start)")
    
    # Check agent health
    click.echo(f"\n🤖 Agent Health Check:")
    enabled_agents = project_config.get_enabled_agents()
    click.echo(f"   Enabled agents: {len(enabled_agents)}")
    
    # Check if critical agents are enabled
    if 'orchestrator' not in enabled_agents:
        click.echo(f"   ⚠️  Warning: Orchestrator agent not enabled (required for coordination)")
    
    # Check project-specific recommendations
    project_type = project_config.config.get('project_type', 'auto')
    recommended = _get_recommended_agents(project_type)
    missing = [agent for agent in recommended if agent not in enabled_agents]
    
    if missing:
        click.echo(f"   💡 Tip: For {project_type} projects, consider enabling: {', '.join(missing)}")
    
    click.echo(f"\n⚙️  Configuration:")
    click.echo(f"   Default mode: {project_config.get_default_mode()}")
    click.echo(f"   Default model: {project_config.get_model_config()['provider']}")
    click.echo(f"   Event bus: {project_config.get_event_bus_type()}")


@cli.command()
@click.option('--project', '-p', help='Project path (default: current directory)')
@click.confirmation_option(prompt='Are you sure you want to reset the framework state?')
def reset(project: Optional[str]):
    """Reset the framework state for a project."""
    project_path = project or os.getcwd()
    project_config = ProjectConfig(project_path)
    
    click.echo("🔄 Resetting framework state...")
    
    # Clear message queues
    message_bus = MessageBus(project_config.get_message_queue_dir())
    message_bus.clear_all_messages()
    click.echo("✓ Cleared message queues")
    
    # Reset state file
    state_file = project_config.get_state_file_path()
    if os.path.exists(state_file):
        os.remove(state_file)
        click.echo("✓ Removed state file")
    
    # Clear logs
    log_dir = project_config.get_log_dir()
    if os.path.exists(log_dir):
        import shutil
        shutil.rmtree(log_dir)
        os.makedirs(log_dir)
        click.echo("✓ Cleared logs")
    
    click.echo("\n✅ Framework state reset successfully")


@cli.command()
@click.argument('action', required=False)
def modes(action: Optional[str]):
    """Explain the different agent communication modes."""
    click.echo("📡 Multi-Agent Framework Communication Modes\n")
    
    click.echo("🔄 Polling Mode (Default - Recommended):")
    click.echo("   - Agents check for messages at regular intervals")
    click.echo("   - More stable and predictable behavior")
    click.echo("   - Lower resource usage")
    click.echo("   - Slight delay between message send and processing")
    click.echo("   - Best for: Most projects, especially when starting out")
    click.echo("")
    
    click.echo("⚡ Event-Driven Mode (Experimental):")
    click.echo("   - Agents react immediately to new messages")
    click.echo("   - Real-time communication between agents")
    click.echo("   - Higher resource usage")
    click.echo("   - May have stability issues with message processing")
    click.echo("   - Best for: Projects requiring real-time coordination")
    click.echo("")
    
    click.echo("🚀 Usage:")
    click.echo("   maf launch                    # Uses default (polling)")
    click.echo("   maf launch --mode polling     # Explicitly use polling")
    click.echo("   maf launch --mode event       # Use event-driven mode")
    click.echo("")
    
    click.echo("💡 To change the default mode:")
    click.echo("   Edit .maf-config.json and set framework_config.default_mode")


@cli.command()
@click.option('--save', '-s', help='Save configuration to file')
@click.option('--load', '-l', help='Load configuration from file')
def config_cmd(save: Optional[str], load: Optional[str]):
    """Manage framework configuration."""
    if save:
        # Export current configuration
        project_config = ProjectConfig()
        with open(save, 'w') as f:
            json.dump(project_config.config, f, indent=2)
        click.echo(f"✅ Configuration saved to {save}")
        
    elif load:
        # Import configuration
        if not os.path.exists(load):
            click.echo(f"❌ Configuration file not found: {load}")
            sys.exit(1)
        
        with open(load, 'r') as f:
            new_config = json.load(f)
        
        project_config = ProjectConfig()
        project_config.update_config(new_config)
        click.echo(f"✅ Configuration loaded from {load}")
        
    else:
        # Show current configuration
        project_config = ProjectConfig()
        click.echo("Current Configuration:")
        click.echo(json.dumps(project_config.config, indent=2))


def main():
    """Main entry point for the CLI."""
    cli()


if __name__ == '__main__':
    main()