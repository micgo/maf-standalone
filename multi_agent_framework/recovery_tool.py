#!/usr/bin/env python3
"""
Multi-Agent Framework Recovery Tool

A utility script for manually triggering recovery operations and monitoring system health.
"""

import os
import sys
import argparse
import json
from datetime import datetime

# Add framework path
framework_root = os.path.abspath(os.path.dirname(__file__))
project_root = os.path.abspath(os.path.join(framework_root, '..'))

if project_root not in sys.path:
    sys.path.insert(0, project_root)
if framework_root not in sys.path:
    sys.path.insert(0, framework_root)

from core.project_state_manager import ProjectStateManager


def print_header(title):
    """Print a formatted header."""
    print("\n" + "="*60)
    print(f" {title}")
    print("="*60)


def health_check(state_manager):
    """Perform and display health check."""
    print_header("SYSTEM HEALTH CHECK")
    
    health_report = state_manager.task_health_check()
    stats = state_manager.get_task_statistics()
    
    # Overall health
    status = "🟢 HEALTHY" if health_report['healthy'] else "🔴 ISSUES DETECTED"
    print(f"System Status: {status}")
    print(f"Total Tasks: {health_report['total_tasks']}")
    
    # Task status breakdown
    print("\nTask Status Breakdown:")
    for status, count in health_report['status_counts'].items():
        emoji = {
            'completed': '✅',
            'in_progress': '🔄', 
            'pending': '⏳',
            'failed': '❌',
            'permanently_failed': '💀'
        }.get(status, '📋')
        print(f"  {emoji} {status}: {count}")
    
    # Performance metrics
    if stats['total_tasks'] > 0:
        print(f"\nPerformance Metrics:")
        print(f"  📊 Completion Rate: {stats['completion_rate']:.1%}")
        print(f"  🔄 Average Retries: {stats['average_retry_count']:.1f}")
        print(f"  ⚠️  Tasks with Errors: {stats['tasks_with_errors']}")
    
    # Issues
    if not health_report['healthy']:
        print("\n🚨 ISSUES DETECTED:")
        
        if health_report['stalled_tasks']:
            print(f"\n🔴 Stalled Tasks ({len(health_report['stalled_tasks'])}):")
            for task in health_report['stalled_tasks']:
                print(f"  - {task['task_id'][:8]}...: {task['description'][:60]}...")
                print(f"    Agent: {task['agent']}, Started: {task['started_at']}")
        
        if health_report['failed_tasks']:
            print(f"\n❌ Failed Tasks ({len(health_report['failed_tasks'])}):")
            for task in health_report['failed_tasks']:
                print(f"  - {task['task_id'][:8]}...: {task['description'][:60]}...")
                print(f"    Error: {task['error']}, Retries: {task['retry_count']}")
        
        if health_report['long_running_tasks']:
            print(f"\n⏳ Long-Running Tasks ({len(health_report['long_running_tasks'])}):")
            for task in health_report['long_running_tasks']:
                print(f"  - {task['task_id'][:8]}...: {task['description'][:60]}...")
                print(f"    Agent: {task['agent']}, Started: {task['started_at']}")


def recover_stalled(state_manager, timeout_minutes=30):
    """Recover stalled tasks."""
    print_header(f"RECOVERING STALLED TASKS (>{timeout_minutes}min)")
    
    recovered = state_manager.recover_stalled_tasks(timeout_minutes)
    
    if recovered:
        print(f"✅ Successfully recovered {len(recovered)} stalled tasks:")
        for task_id in recovered:
            task = state_manager.get_task(task_id)
            if task:
                print(f"  - {task_id[:8]}...: {task['description'][:60]}...")
    else:
        print("✅ No stalled tasks found")


def retry_failed(state_manager, max_retries=3):
    """Retry failed tasks."""
    print_header(f"RETRYING FAILED TASKS (max {max_retries} retries)")
    
    retried = state_manager.retry_failed_tasks(max_retries)
    
    if retried:
        print(f"✅ Successfully retried {len(retried)} failed tasks:")
        for task_id in retried:
            task = state_manager.get_task(task_id)
            if task:
                print(f"  - {task_id[:8]}...: {task['description'][:60]}...")
    else:
        print("✅ No failed tasks to retry")


def cleanup_old_tasks(state_manager, keep_days=7):
    """Clean up old completed tasks."""
    print_header(f"CLEANING UP TASKS OLDER THAN {keep_days} DAYS")
    
    cleaned = state_manager.cleanup_completed_tasks(keep_days)
    
    if cleaned > 0:
        print(f"🧹 Successfully cleaned up {cleaned} old tasks")
    else:
        print("✅ No old tasks to clean up")


def show_agent_status(state_manager):
    """Show status by agent."""
    print_header("AGENT STATUS BREAKDOWN")
    
    stats = state_manager.get_task_statistics()
    
    if 'by_agent' in stats and stats['by_agent']:
        for agent, count in stats['by_agent'].items():
            # Get pending tasks for this agent
            pending_tasks = state_manager.get_pending_tasks_by_agent(agent)
            pending_count = len(pending_tasks)
            
            emoji = "🤖" if agent != "unassigned" else "❓"
            print(f"{emoji} {agent}: {count} total tasks, {pending_count} pending")
            
            # Show first few pending tasks
            if pending_tasks:
                for task in pending_tasks[:3]:
                    print(f"    ⏳ {task['description'][:50]}...")
                if len(pending_tasks) > 3:
                    print(f"    ... and {len(pending_tasks) - 3} more")
    else:
        print("No agent data available")


def full_recovery(state_manager):
    """Perform comprehensive recovery operations."""
    print_header("FULL SYSTEM RECOVERY")
    
    print("🔍 Step 1: Health Check")
    health_report = state_manager.task_health_check()
    
    if health_report['healthy']:
        print("✅ System is healthy - no recovery needed")
        return
    
    print("🔧 Step 2: Recovering Stalled Tasks")
    recovered_stalled = state_manager.recover_stalled_tasks(30)
    
    print("🔧 Step 3: Retrying Failed Tasks") 
    retried_failed = state_manager.retry_failed_tasks(3)
    
    print("🧹 Step 4: Cleaning Up Old Tasks")
    cleaned = state_manager.cleanup_completed_tasks(7)
    
    print("\n📊 RECOVERY SUMMARY:")
    print(f"  🔄 Stalled tasks recovered: {len(recovered_stalled)}")
    print(f"  🔄 Failed tasks retried: {len(retried_failed)}")
    print(f"  🧹 Old tasks cleaned: {cleaned}")
    
    total_actions = len(recovered_stalled) + len(retried_failed) + cleaned
    if total_actions > 0:
        print(f"\n✅ Recovery complete! {total_actions} total actions performed")
    else:
        print("\n✅ No recovery actions needed")


def main():
    parser = argparse.ArgumentParser(description="Multi-Agent Framework Recovery Tool")
    parser.add_argument("command", choices=[
        "health", "recover", "retry", "cleanup", "agents", "full"
    ], help="Recovery command to execute")
    parser.add_argument("--timeout", type=int, default=30, 
                       help="Timeout in minutes for stalled task recovery (default: 30)")
    parser.add_argument("--retries", type=int, default=3,
                       help="Maximum retries for failed tasks (default: 3)")
    parser.add_argument("--days", type=int, default=7,
                       help="Days to keep completed tasks (default: 7)")
    
    args = parser.parse_args()
    
    # Initialize state manager
    try:
        state_manager = ProjectStateManager()
    except Exception as e:
        print(f"❌ Failed to initialize state manager: {e}")
        sys.exit(1)
    
    # Execute command
    try:
        if args.command == "health":
            health_check(state_manager)
        elif args.command == "recover":
            recover_stalled(state_manager, args.timeout)
        elif args.command == "retry":
            retry_failed(state_manager, args.retries)
        elif args.command == "cleanup":
            cleanup_old_tasks(state_manager, args.days)
        elif args.command == "agents":
            show_agent_status(state_manager)
        elif args.command == "full":
            full_recovery(state_manager)
    except Exception as e:
        print(f"❌ Command failed: {e}")
        sys.exit(1)
    
    print(f"\n⏰ Recovery tool completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    main()