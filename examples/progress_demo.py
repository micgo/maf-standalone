#!/usr/bin/env python3
"""
Demo script to showcase progress tracking features
"""
import os
import sys
import time
import click

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from multi_agent_framework.core.progress_tracker import ProgressTracker


def demo_progress():
    """Demonstrate progress tracking capabilities"""
    click.echo("🎯 Multi-Agent Framework Progress Tracking Demo\n")
    
    # Create a progress tracker
    tracker = ProgressTracker("demo_state.json")
    
    # Simulate a feature being developed
    click.echo("📝 Creating feature: 'Add user authentication system'")
    tracker.create_feature("feat-001", "Add user authentication system with email verification")
    
    time.sleep(1)
    
    # Simulate orchestrator breaking down into tasks
    click.echo("\n🎯 Orchestrator breaking down feature into tasks...")
    tasks = [
        ("task-001", "Create user model and database schema", "db_agent"),
        ("task-002", "Build authentication API endpoints", "backend_agent"),
        ("task-003", "Design login and signup forms", "ux_ui_agent"),
        ("task-004", "Implement login/signup UI components", "frontend_agent"),
        ("task-005", "Add JWT token management", "security_agent"),
        ("task-006", "Write authentication tests", "qa_agent"),
        ("task-007", "Document authentication API", "docs_agent")
    ]
    
    for task_id, desc, agent in tasks:
        tracker.create_task(task_id, "feat-001", desc, agent)
        click.echo(f"   ✓ Assigned to {agent}: {desc}")
        time.sleep(0.5)
    
    click.echo("\n🚀 Agents starting work...\n")
    time.sleep(1)
    
    # Simulate task progress
    progress_updates = [
        ("task-001", 10, "in_progress", "Setting up database connection"),
        ("task-003", 10, "in_progress", "Researching design patterns"),
        ("task-001", 50, "in_progress", "Creating user table schema"),
        ("task-002", 10, "in_progress", "Setting up API routes"),
        ("task-003", 60, "in_progress", "Creating wireframes"),
        ("task-001", 100, "completed", "Database schema complete"),
        ("task-004", 10, "in_progress", "Setting up React components"),
        ("task-002", 40, "in_progress", "Implementing login endpoint"),
        ("task-005", 10, "in_progress", "Configuring JWT library"),
        ("task-003", 100, "completed", "Design mockups complete"),
        ("task-002", 80, "in_progress", "Adding password hashing"),
        ("task-004", 50, "in_progress", "Building form validation"),
        ("task-006", 10, "in_progress", "Writing unit tests"),
        ("task-002", 100, "completed", "API endpoints complete"),
        ("task-005", 60, "in_progress", "Implementing token refresh"),
        ("task-004", 90, "in_progress", "Final styling touches"),
        ("task-007", 30, "in_progress", "Writing API documentation"),
        ("task-005", 100, "completed", "Security implementation complete"),
        ("task-004", 100, "completed", "UI components complete"),
        ("task-006", 70, "in_progress", "Running integration tests"),
        ("task-007", 80, "in_progress", "Adding code examples"),
        ("task-006", 100, "completed", "All tests passing"),
        ("task-007", 100, "completed", "Documentation complete")
    ]
    
    # Show initial status
    tracker.display_progress(detailed=True)
    
    click.echo("\n📊 Live Progress Updates:\n")
    
    for task_id, progress, status, message in progress_updates:
        # Get agent name
        state = tracker._load_state()
        agent = state['tasks'][task_id]['assigned_agent']
        
        # Update progress
        tracker.update_task_status(task_id, status, progress)
        
        # Show update
        agent_emoji = {
            'orchestrator': '🎯',
            'frontend_agent': '🎨',
            'backend_agent': '⚙️',
            'db_agent': '💾',
            'devops_agent': '🚀',
            'qa_agent': '🧪',
            'docs_agent': '📚',
            'security_agent': '🔒',
            'ux_ui_agent': '✨'
        }.get(agent, '🤖')
        
        if status == 'completed':
            click.echo(f"{agent_emoji} {agent}: ✅ {message}")
        else:
            click.echo(f"{agent_emoji} {agent}: {progress}% - {message}")
        
        time.sleep(0.8)  # Simulate work being done
        
        # Show progress bar every few updates
        if progress_updates.index((task_id, progress, status, message)) % 5 == 4:
            click.echo("\n" + "─" * 60)
            tracker.display_progress(detailed=False)
            click.echo("─" * 60 + "\n")
    
    # Final status
    click.echo("\n🎉 Feature Development Complete!\n")
    tracker.display_progress(detailed=True)
    
    # Clean up
    os.remove("demo_state.json")


if __name__ == "__main__":
    try:
        demo_progress()
    except KeyboardInterrupt:
        click.echo("\n\nDemo interrupted")
        # Clean up
        if os.path.exists("demo_state.json"):
            os.remove("demo_state.json")