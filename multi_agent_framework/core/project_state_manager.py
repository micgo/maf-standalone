import json
import os
import sys # Import sys to access sys.path for debugging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

# --- START of new/modified lines in core/project_state_manager.py ---

# Diagnostic print to show where the module is being imported from


PROJECT_STATE_FILE = ".maf/state.json"
# Construct the absolute path to the project state file for clarity
# The state file is now stored in the .maf directory in the project root
# os.path.dirname(__file__) is the 'core' directory
# We need to go up two levels to get to the project root
PROJECT_ROOT_FOR_STATE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
FULL_PROJECT_STATE_PATH = os.path.join(PROJECT_ROOT_FOR_STATE, PROJECT_STATE_FILE)

class ProjectStateManager:
    def __init__(self):
        # Diagnostic print for instance creation

        if not os.path.exists(FULL_PROJECT_STATE_PATH):
            try:
                # Use the full path for saving the initial state
                self._save_state({"features": {}, "tasks": {}}, full_path=True)
            except IOError as e:
                print(f"ERROR: Could not create {FULL_PROJECT_STATE_PATH}: {e}")
                # It's critical if we can't save state, so consider exiting or raising
                sys.exit(1) # Exit if cannot initialize state
        
        try:
            self.state = self._load_state(full_path=True)
        except (IOError, json.JSONDecodeError) as e:
            print(f"ERROR: Could not load {FULL_PROJECT_STATE_PATH}, possibly corrupted or empty: {e}")
            self.state = {"features": {}, "tasks": {}} # Reinitialize state to avoid further errors
            # Attempt to save a clean state if loading failed
            try:
                self._save_state(self.state, full_path=True)
            except IOError as save_err:
                print(f"CRITICAL ERROR: Failed to reset and save clean state to {FULL_PROJECT_STATE_PATH}: {save_err}")
                sys.exit(1) # Exit if cannot save clean state

    def _load_state(self, full_path=False):
        path_to_use = FULL_PROJECT_STATE_PATH if full_path else PROJECT_STATE_FILE
        with open(path_to_use, 'r') as f:
            return json.load(f)

    def _save_state(self, state, full_path=False):
        path_to_use = FULL_PROJECT_STATE_PATH if full_path else PROJECT_STATE_FILE
        try:
            with open(path_to_use, 'w') as f:
                json.dump(state, f, indent=2)
        except IOError as e:
            print(f"ERROR: Could not save {path_to_use}: {e}")
            # Consider raising or logging this error more prominently, or re-raising
            raise # Re-raise the exception to be caught by the __init__ or calling method
# --- END of new/modified lines in core/project_state_manager.py ---

    def add_feature(self, feature_id, description):
        self.state["features"][feature_id] = {"description": description, "status": "new"}
        self._save_state(self.state, full_path=True) # Ensure full_path is used here too

    def add_task(self, task_id, feature_id, description, assigned_agent=None, status="pending", output=None):
        current_time = datetime.now().isoformat()
        self.state["tasks"][task_id] = {
            "feature_id": feature_id,
            "description": description,
            "assigned_agent": assigned_agent,
            "status": status,
            "output": output,
            "created_at": current_time,
            "updated_at": current_time,
            "started_at": None,
            "retry_count": 0,
            "last_error": None
        }
        self._save_state(self.state, full_path=True) # Ensure full_path is used here too

    def update_task_status(self, task_id, status, output=None, error=None):
        if task_id in self.state["tasks"]:
            current_time = datetime.now().isoformat()
            task = self.state["tasks"][task_id]
            
            # Track when task was started
            if status == "in_progress" and task["started_at"] is None:
                task["started_at"] = current_time
            
            task["status"] = status
            task["updated_at"] = current_time
            
            if output:
                task["output"] = output
            
            if error:
                task["last_error"] = error
                task["retry_count"] = task.get("retry_count", 0) + 1
            
            self._save_state(self.state, full_path=True) # Ensure full_path is used here too
        else:
            print(f"Task {task_id} not found.")

    def get_task(self, task_id):
        return self.state["tasks"].get(task_id)

    def get_feature_tasks(self, feature_id):
        return {task_id: task for task_id, task in self.state["tasks"].items() if task["feature_id"] == feature_id}

    def get_all_tasks(self):
        return self.state["tasks"]

    def get_all_features(self):
        return self.state["features"]
    
    def increment_retry_count(self, task_id):
        """Increment the retry count for a task"""
        if task_id in self.state["tasks"]:
            self.state["tasks"][task_id]["retry_count"] = self.state["tasks"][task_id].get("retry_count", 0) + 1
            self._save_state(self.state, full_path=True)
            return self.state["tasks"][task_id]["retry_count"]
        return 0
    
    # === Task State Management & Recovery System ===
    
    def recover_stalled_tasks(self, timeout_minutes: int = 30) -> List[str]:
        """
        Detect and recover tasks stuck in progress for too long.
        
        Args:
            timeout_minutes: How long a task can be in_progress before considered stalled
            
        Returns:
            List of task IDs that were recovered
        """
        recovered_tasks = []
        cutoff_time = datetime.now() - timedelta(minutes=timeout_minutes)
        
        for task_id, task in self.state["tasks"].items():
            if task["status"] == "in_progress" and task.get("started_at"):
                try:
                    started_at = datetime.fromisoformat(task["started_at"])
                    if started_at < cutoff_time:
                        print(f"🔄 Recovering stalled task: {task_id}")
                        print(f"   Description: {task['description'][:100]}...")
                        print(f"   Started: {task['started_at']}")
                        print(f"   Agent: {task.get('assigned_agent', 'Unknown')}")
                        
                        # Reset task to pending for retry
                        self.update_task_status(
                            task_id, 
                            "pending", 
                            output=None,
                            error=f"Task stalled after {timeout_minutes} minutes"
                        )
                        recovered_tasks.append(task_id)
                        
                except (ValueError, TypeError) as e:
                    print(f"⚠️  Error parsing date for task {task_id}: {e}")
                    # Reset malformed task
                    self.update_task_status(task_id, "pending", error="Invalid timestamp")
                    recovered_tasks.append(task_id)
        
        if recovered_tasks:
            print(f"✅ Recovered {len(recovered_tasks)} stalled tasks")
        else:
            print("✅ No stalled tasks found")
            
        return recovered_tasks
    
    def retry_failed_tasks(self, max_retries: int = 3) -> List[str]:
        """
        Smart retry mechanism for failed tasks.
        
        Args:
            max_retries: Maximum number of retries before marking task as permanently failed
            
        Returns:
            List of task IDs that were retried
        """
        retried_tasks = []
        
        for task_id, task in self.state["tasks"].items():
            if task["status"] == "failed":
                retry_count = task.get("retry_count", 0)
                
                if retry_count < max_retries:
                    print(f"🔄 Retrying failed task: {task_id} (attempt {retry_count + 1}/{max_retries})")
                    print(f"   Description: {task['description'][:100]}...")
                    print(f"   Last error: {task.get('last_error', 'Unknown error')}")
                    
                    # Reset to pending for retry
                    self.update_task_status(task_id, "pending")
                    retried_tasks.append(task_id)
                    
                else:
                    print(f"❌ Task {task_id} exceeded max retries ({max_retries})")
                    self.update_task_status(task_id, "permanently_failed")
        
        if retried_tasks:
            print(f"✅ Retried {len(retried_tasks)} failed tasks")
        else:
            print("✅ No failed tasks to retry")
            
        return retried_tasks
    
    def task_health_check(self) -> Dict[str, any]:
        """
        Monitor task progress and generate health report.
        
        Returns:
            Dictionary containing health metrics and problematic tasks
        """
        health_report = {
            "total_tasks": len(self.state["tasks"]),
            "status_counts": {},
            "stalled_tasks": [],
            "failed_tasks": [],
            "long_running_tasks": [],
            "healthy": True,
            "issues": []
        }
        
        # Count tasks by status
        for task in self.state["tasks"].values():
            status = task["status"]
            health_report["status_counts"][status] = health_report["status_counts"].get(status, 0) + 1
        
        # Check for problematic tasks
        cutoff_time = datetime.now() - timedelta(minutes=30)
        long_running_cutoff = datetime.now() - timedelta(minutes=15)
        
        for task_id, task in self.state["tasks"].items():
            status = task["status"]
            
            # Check for stalled tasks
            if status == "in_progress" and task.get("started_at"):
                try:
                    started_at = datetime.fromisoformat(task["started_at"])
                    if started_at < cutoff_time:
                        health_report["stalled_tasks"].append({
                            "task_id": task_id,
                            "description": task["description"][:100],
                            "started_at": task["started_at"],
                            "agent": task.get("assigned_agent")
                        })
                    elif started_at < long_running_cutoff:
                        health_report["long_running_tasks"].append({
                            "task_id": task_id,
                            "description": task["description"][:100],
                            "started_at": task["started_at"],
                            "agent": task.get("assigned_agent")
                        })
                except (ValueError, TypeError):
                    health_report["issues"].append(f"Task {task_id} has invalid timestamp")
            
            # Check for failed tasks
            if status == "failed":
                health_report["failed_tasks"].append({
                    "task_id": task_id,
                    "description": task["description"][:100],
                    "error": task.get("last_error"),
                    "retry_count": task.get("retry_count", 0)
                })
        
        # Determine overall health
        if (health_report["stalled_tasks"] or 
            health_report["failed_tasks"] or 
            health_report["issues"]):
            health_report["healthy"] = False
        
        return health_report
    
    def get_pending_tasks_by_agent(self, agent_name: str) -> List[Dict]:
        """
        Get all pending tasks assigned to a specific agent.
        
        Args:
            agent_name: Name of the agent to filter by
            
        Returns:
            List of pending tasks for the agent
        """
        pending_tasks = []
        
        for task_id, task in self.state["tasks"].items():
            if (task["status"] == "pending" and 
                task.get("assigned_agent") == agent_name):
                pending_tasks.append({
                    "task_id": task_id,
                    "feature_id": task["feature_id"],
                    "description": task["description"],
                    "created_at": task.get("created_at"),
                    "retry_count": task.get("retry_count", 0)
                })
        
        # Sort by creation time (oldest first), handle None values
        pending_tasks.sort(key=lambda x: x.get("created_at") or "")
        return pending_tasks
    
    def cleanup_completed_tasks(self, keep_days: int = 7) -> int:
        """
        Archive or remove old completed tasks to keep state file manageable.
        
        Args:
            keep_days: Number of days to keep completed tasks
            
        Returns:
            Number of tasks cleaned up
        """
        cutoff_date = datetime.now() - timedelta(days=keep_days)
        tasks_to_remove = []
        
        for task_id, task in self.state["tasks"].items():
            if task["status"] in ["completed", "permanently_failed"]:
                try:
                    updated_at = datetime.fromisoformat(task.get("updated_at", ""))
                    if updated_at < cutoff_date:
                        tasks_to_remove.append(task_id)
                except (ValueError, TypeError):
                    # Remove tasks with invalid timestamps
                    tasks_to_remove.append(task_id)
        
        # Remove old tasks
        for task_id in tasks_to_remove:
            del self.state["tasks"][task_id]
        
        if tasks_to_remove:
            self._save_state(self.state, full_path=True)
            print(f"🧹 Cleaned up {len(tasks_to_remove)} old completed tasks")
        
        return len(tasks_to_remove)
    
    def get_task_statistics(self) -> Dict[str, any]:
        """
        Get comprehensive statistics about task performance.
        
        Returns:
            Dictionary containing various task metrics
        """
        stats = {
            "total_tasks": len(self.state["tasks"]),
            "by_status": {},
            "by_agent": {},
            "completion_rate": 0.0,
            "average_retry_count": 0.0,
            "tasks_with_errors": 0
        }
        
        total_retries = 0
        completed_tasks = 0
        
        for task in self.state["tasks"].values():
            # Count by status
            status = task["status"]
            stats["by_status"][status] = stats["by_status"].get(status, 0) + 1
            
            # Count by agent
            agent = task.get("assigned_agent", "unassigned")
            stats["by_agent"][agent] = stats["by_agent"].get(agent, 0) + 1
            
            # Track retries and completion
            retry_count = task.get("retry_count", 0)
            total_retries += retry_count
            
            if status == "completed":
                completed_tasks += 1
            
            if task.get("last_error"):
                stats["tasks_with_errors"] += 1
        
        # Calculate rates
        if stats["total_tasks"] > 0:
            stats["completion_rate"] = completed_tasks / stats["total_tasks"]
            stats["average_retry_count"] = total_retries / stats["total_tasks"]
        
        return stats
