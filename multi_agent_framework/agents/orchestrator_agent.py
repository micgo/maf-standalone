import os
import sys
import json
import time
import uuid
from datetime import datetime, timedelta
from .. import config
from .base_agent_configurable import BaseAgent
from ..core.project_config import ProjectConfig
from ..core.project_state_manager import ProjectStateManager


class OrchestratorAgent(BaseAgent):
    def __init__(self, project_config=None, model_provider="gemini", model_name="gemini-2.5-pro-preview-06-05"): # Latest Gemini 2.5 Pro for advanced orchestration
        super().__init__("orchestrator", project_config, model_provider, model_name)
        self.available_agents = [
            "frontend_agent", "backend_agent", "db_agent",
            "devops_agent", "qa_agent", "docs_agent", "security_agent",
            "ux_ui_agent"
        ]

    def run(self):
        print(f"{self.name} started. Waiting for instructions...")
        last_health_check = datetime.now()
        last_recovery_check = datetime.now()
        
        while True:
            messages = self.receive_messages()
            for msg in messages:
                self._process_message(msg)
            self._check_and_assign_new_tasks()
            
            # Perform health checks every 5 minutes
            if datetime.now() - last_health_check > timedelta(minutes=5):
                self._perform_health_check()
                last_health_check = datetime.now()
            
            # Perform recovery checks every 10 minutes
            if datetime.now() - last_recovery_check > timedelta(minutes=10):
                self._perform_recovery_operations()
                last_recovery_check = datetime.now()
            
            time.sleep(5) # Poll every 5 seconds

    def _process_message(self, msg):
        print(f"Orchestrator received message from {msg['sender']}: {msg['type']} for task {msg.get('task_id')}")
        if msg["type"] == "new_feature":
            self._handle_new_feature_request(msg["content"])
        elif msg["type"] == "task_completed":
            self._handle_task_completion(msg["task_id"], msg["sender"], msg["content"])
        elif msg["type"] == "task_failed":
            self._handle_task_failure(msg["task_id"], msg["sender"], msg["content"])
        elif msg["type"] == "status_update":
            print(f"Status update from {msg['sender']} for task {msg['task_id']}: {msg['content']}")
        else:
            print(f"Orchestrator: Unknown message type {msg['type']}")

    def _handle_new_feature_request(self, feature_description):
        feature_id = str(uuid.uuid4())
        self.state_manager.add_feature(feature_id, feature_description)
        print(f"Orchestrator: New feature '{feature_description}' (ID: {feature_id}) added.")

        prompt = f"""You are the Orchestrator for a web application development team.
        Your goal is to break down a new feature request into actionable development tasks.
        The feature is: "{feature_description}"

        Break this down into a list of specific, detailed tasks for the following specialized agents.
        **When specifying the 'agent' field, use ONLY these exact snake_case names:**
        - `frontend_agent`
        - `backend_agent`
        - `db_agent`
        - `devops_agent`
        - `qa_agent`
        - `docs_agent`
        - `security_agent`
        - `ux_ui_agent`

        For each task, provide a concise description.
        Output your response as a JSON array of objects, where each object has 'agent' and 'description' keys.
        Do NOT include any text or formatting outside of the JSON array.
        Example:
        [
            {{"agent": "backend_agent", "description": "Design REST API endpoint for user registration."}},
            {{"agent": "frontend_agent", "description": "Create user registration form UI."}},
            {{"agent": "ux_ui_agent", "description": "Design the user flow for the new registration process."}}
        ]
        """
        response = self._generate_response(prompt)
        if response:

            cleaned_response = response.strip()

            if cleaned_response.startswith("```json"):
                cleaned_response = cleaned_response[len("```json"):].strip()
            if cleaned_response.endswith("```"):
                cleaned_response = cleaned_response[:-len("```")].strip()

            cleaned_response = cleaned_response.replace('\xa0', ' ').strip()


            try:
                tasks = json.loads(cleaned_response)
                for task in tasks:
                    task_id = str(uuid.uuid4())
                    agent = task["agent"]
                    description = task["description"]

                    # Agent Name Mapping
                    if "database_architect_agent" == agent or "Database Architect Agent" == agent:
                        agent = "db_agent"
                    elif "frontend_developer_agent" == agent or "Frontend Developer Agent" == agent:
                        agent = "frontend_agent"
                    elif "backend_developer_agent" == agent or "Backend Developer Agent" == agent:
                        agent = "backend_agent"
                    elif "qa_testing_agent" == agent or "QA & Testing Agent" == agent:
                        agent = "qa_agent"
                    elif "documentation_agent" == agent or "Documentation Agent" == agent:
                        agent = "docs_agent"
                    elif "security_agent" == agent or "Security Agent" == agent:
                        agent = "security_agent"
                    elif "devops_infrastructure_agent" == agent or "DevOps & Infrastructure Agent" == agent:
                        agent = "devops_agent"


                    if agent in self.available_agents:
                        self.state_manager.add_task(task_id, feature_id, description, agent, "pending")
                        self.send_message(agent, task_id, description, "new_task")
                        print(f"Orchestrator: Assigned task '{description}' to {agent} (Task ID: {task_id})")
                    else:
                        print(f"Orchestrator: Warning - Agent '{agent}' not recognized for task: {description}. Task skipped.")
            except json.JSONDecodeError as e:
                print(f"Orchestrator: Failed to parse tasks from LLM response (JSON Decode Error): {e}\nRaw Response: {response}\nCleaned Response: {cleaned_response}")
            except Exception as e:
                print(f"Orchestrator: An unexpected error occurred while processing LLM response: {e}\nRaw Response: {response}\nCleaned Response: {cleaned_response}")
        else:
            print("Orchestrator: Failed to generate tasks for the new feature.")

    def _handle_task_completion(self, task_id, sender_agent, output_content):
        self.state_manager.update_task_status(task_id, "completed", output_content)
        task = self.state_manager.get_task(task_id)
        if task:
            print(f"Orchestrator: Task '{task['description']}' by {sender_agent} COMPLETED.")
            # Trigger any pending tasks for this feature
            self._trigger_pending_tasks(task["feature_id"])
            # Then check if the entire feature is complete
            self._check_feature_completion(task["feature_id"])

    def _handle_task_failure(self, task_id, sender_agent, error_content):
        self.state_manager.update_task_status(task_id, "failed", error_content)
        task = self.state_manager.get_task(task_id)
        if task:
            print(f"Orchestrator: Task '{task['description']}' by {sender_agent} FAILED: {error_content}")
            
            # Check retry count
            retry_count = task.get('retry_count', 0)
            max_retries = config.MAX_RETRY_ATTEMPTS
            
            if retry_count < max_retries:
                # Increment retry count
                self.state_manager.increment_retry_count(task_id)
                print(f"Orchestrator: Retrying task {task_id} (attempt {retry_count + 1}/{max_retries})")
                self.send_message(sender_agent, task_id, f"Please review the error: {error_content}", "review_and_retry")
            else:
                print(f"Orchestrator: Task {task_id} exceeded maximum retries ({max_retries}). Marking as permanently failed.")
                self.state_manager.update_task_status(task_id, "failed_permanently", f"Failed after {max_retries} retries. Last error: {error_content}")
                # Check if feature should be blocked
                self._check_feature_completion(task["feature_id"])

    def _check_and_assign_new_tasks(self):
        """Check for pending tasks in in_progress features and assign them to agents."""
        # Track assigned tasks to prevent duplicate assignments
        if not hasattr(self, '_assigned_tasks'):
            self._assigned_tasks = set()
            
        for feature_id, feature in self.state_manager.state["features"].items():
            if feature["status"] == "in_progress":
                feature_tasks = self.state_manager.get_feature_tasks(feature_id)
                for task_id, task in feature_tasks.items():
                    if task["status"] == "pending" and task_id not in self._assigned_tasks:
                        agent = task["assigned_agent"]
                        if agent in self.available_agents:
                            # Send task to agent
                            self.send_message(agent, task_id, task["description"], "new_task")
                            # Mark as assigned to prevent duplicates
                            self._assigned_tasks.add(task_id)
                            print(f"Orchestrator: Assigned pending task '{task['description']}' to {agent} (Task ID: {task_id})")
                        else:
                            print(f"Orchestrator: Warning - Agent '{agent}' not available for task: {task['description']}")

    def _trigger_pending_tasks(self, feature_id):
        """Trigger any pending tasks for a specific feature after a task completion."""
        # Track triggered tasks to prevent duplicate triggers
        if not hasattr(self, '_triggered_tasks'):
            self._triggered_tasks = set()
            
        feature_tasks = self.state_manager.get_feature_tasks(feature_id)
        pending_count = 0
        
        for task_id, task in feature_tasks.items():
            if task["status"] == "pending" and task_id not in self._triggered_tasks:
                agent = task["assigned_agent"]
                if agent in self.available_agents:
                    # Send task to agent
                    self.send_message(agent, task_id, task["description"], "new_task")
                    # Mark as triggered to prevent duplicates
                    self._triggered_tasks.add(task_id)
                    print(f"Orchestrator: Auto-triggered pending task '{task['description']}' to {agent} (Task ID: {task_id})")
                    pending_count += 1
                else:
                    print(f"Orchestrator: Warning - Agent '{agent}' not available for pending task: {task['description']}")
        
        if pending_count > 0:
            print(f"Orchestrator: Triggered {pending_count} pending task(s) for feature {feature_id}")

    def _check_feature_completion(self, feature_id):
        all_tasks = self.state_manager.get_feature_tasks(feature_id)
        if all(task["status"] == "completed" for task in all_tasks.values()):
            self.state_manager.state["features"][feature_id]["status"] = "completed"
            self.state_manager._save_state(self.state_manager.state)
            print(f"Orchestrator: Feature '{self.state_manager.state['features'][feature_id]['description']}' (ID: {feature_id}) is now COMPLETE!")
        elif any(task["status"] in ["failed", "failed_permanently"] for task in all_tasks.values()):
            # Count permanent failures
            perm_failures = sum(1 for task in all_tasks.values() if task["status"] == "failed_permanently")
            if perm_failures > 0:
                self.state_manager.state["features"][feature_id]["status"] = "blocked"
                self.state_manager._save_state(self.state_manager.state)
                print(f"Orchestrator: Feature '{self.state_manager.state['features'][feature_id]['description']}' (ID: {feature_id}) is BLOCKED due to {perm_failures} permanently failed task(s).")
            else:
                print(f"Orchestrator: Feature '{self.state_manager.state['features'][feature_id]['description']}' (ID: {feature_id}) has failed tasks that may be retried.")
            
    def _perform_health_check(self):
        """Perform comprehensive health check on all tasks."""
        print("🔍 Orchestrator: Performing health check...")
        health_report = self.state_manager.task_health_check()
        
        # Log health summary
        print(f"📊 Health Report: {health_report['total_tasks']} total tasks")
        for status, count in health_report['status_counts'].items():
            print(f"   {status}: {count}")
        
        # Report issues
        if not health_report['healthy']:
            print("⚠️  System health issues detected:")
            
            if health_report['stalled_tasks']:
                print(f"   🔄 {len(health_report['stalled_tasks'])} stalled tasks")
                for task in health_report['stalled_tasks'][:3]:  # Show first 3
                    print(f"      - {task['task_id']}: {task['description'][:50]}...")
            
            if health_report['failed_tasks']:
                print(f"   ❌ {len(health_report['failed_tasks'])} failed tasks")
                for task in health_report['failed_tasks'][:3]:  # Show first 3
                    print(f"      - {task['task_id']}: {task['description'][:50]}...")
            
            if health_report['long_running_tasks']:
                print(f"   ⏳ {len(health_report['long_running_tasks'])} long-running tasks")
            
            if health_report['issues']:
                for issue in health_report['issues']:
                    print(f"   ⚠️  {issue}")
        else:
            print("✅ System health: All systems operational")
        
        # Log statistics
        stats = self.state_manager.get_task_statistics()
        if stats['total_tasks'] > 0:
            print(f"📈 Performance: {stats['completion_rate']:.1%} completion rate, {stats['average_retry_count']:.1f} avg retries")
    
    def _perform_recovery_operations(self):
        """Perform automatic recovery operations."""
        print("🔧 Orchestrator: Performing recovery operations...")
        
        # Recover stalled tasks (tasks stuck in progress for >30 minutes)
        recovered_stalled = self.state_manager.recover_stalled_tasks(timeout_minutes=30)
        
        # Retry failed tasks (up to 3 attempts)
        retried_failed = self.state_manager.retry_failed_tasks(max_retries=3)
        
        # Clean up old completed tasks (older than 7 days)
        cleaned_tasks = self.state_manager.cleanup_completed_tasks(keep_days=7)
        
        # Report recovery summary
        total_actions = len(recovered_stalled) + len(retried_failed) + cleaned_tasks
        if total_actions > 0:
            print(f"🔧 Recovery complete: {len(recovered_stalled)} stalled recovered, {len(retried_failed)} failed retried, {cleaned_tasks} old tasks cleaned")
        else:
            print("✅ Recovery complete: No actions needed")
        
        # Trigger pending tasks for recovered items
        if recovered_stalled or retried_failed:
            print("🔄 Re-triggering recovered tasks...")
            self._trigger_recovered_tasks(recovered_stalled + retried_failed)
    
    def _trigger_recovered_tasks(self, task_ids):
        """Trigger tasks that were recovered from stalled or failed states."""
        for task_id in task_ids:
            task = self.state_manager.get_task(task_id)
            if task and task['status'] == 'pending':
                agent = task['assigned_agent']
                if agent in self.available_agents:
                    self.send_message(agent, task_id, task['description'], "recovered_task")
                    print(f"🔄 Re-triggered recovered task '{task['description'][:50]}...' to {agent}")
    
    def get_system_status(self):
        """Get comprehensive system status for monitoring."""
        health_report = self.state_manager.task_health_check()
        stats = self.state_manager.get_task_statistics()
        
        return {
            'health': health_report,
            'statistics': stats,
            'timestamp': datetime.now().isoformat(),
            'available_agents': self.available_agents
        }

if __name__ == "__main__":
    orchestrator_agent = OrchestratorAgent()  # Use default model from __init__
    orchestrator_agent.run()
