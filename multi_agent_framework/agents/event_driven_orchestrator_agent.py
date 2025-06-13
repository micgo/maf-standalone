"""
Event-Driven Orchestrator Agent

This is the event-driven version of the orchestrator agent that coordinates
all other agents using events instead of polling.
"""

import os
import json
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

from .. import config
from .event_driven_base_agent import EventDrivenBaseAgent
from ..core.event_bus_interface import Event, EventType


class EventDrivenOrchestratorAgent(EventDrivenBaseAgent):
    """
    Event-driven orchestrator that manages feature requests and task distribution
    """
    
    def __init__(self, model_provider="gemini", model_name="gemini-2.5-pro-preview-06-05", project_config=None):
        super().__init__("orchestrator", model_provider, model_name, project_config)
        
        self.available_agents = [
            "frontend_agent", "backend_agent", "db_agent",
            "devops_agent", "qa_agent", "docs_agent", "security_agent",
            "ux_ui_agent"
        ]
        
        # Track feature and task states
        self._features: Dict[str, Dict[str, Any]] = {}
        self._tasks: Dict[str, Dict[str, Any]] = {}
        
        # Recovery tracking
        self._last_health_check = datetime.now()
        self._last_recovery_check = datetime.now()
    
    def _subscribe_to_events(self):
        """Subscribe to orchestrator-specific events"""
        super()._subscribe_to_events()
        
        # Feature management
        self.event_bus.subscribe(EventType.FEATURE_CREATED, self._handle_feature_created)
        
        # Task lifecycle
        self.event_bus.subscribe(EventType.TASK_COMPLETED, self._handle_task_completed)
        self.event_bus.subscribe(EventType.TASK_FAILED, self._handle_task_failed)
        
        # Agent status
        self.event_bus.subscribe(EventType.AGENT_ERROR, self._handle_agent_error)
        
        # Custom events for feature requests
        self.event_bus.subscribe(EventType.CUSTOM, self._handle_custom_event)
    
    def _handle_feature_created(self, event: Event):
        """Handle new feature creation event"""
        print(f"Orchestrator: Received FEATURE_CREATED event")
        try:
            feature_data = event.data
            feature_id = feature_data.get('feature_id', str(uuid.uuid4()))
            description = feature_data.get('description', '')
            
            # Store feature info
            self._features[feature_id] = {
                'id': feature_id,
                'description': description,
                'status': 'created',
                'created_at': event.timestamp,
                'tasks': []
            }
            
            print(f"Orchestrator: Processing new feature '{description}' (ID: {feature_id})")
            
            # Break down feature into tasks
            self._break_down_feature(feature_id, description)
        except Exception as e:
            print(f"Orchestrator: ERROR in _handle_feature_created: {e}")
            import traceback
            traceback.print_exc()
    
    def _break_down_feature(self, feature_id: str, description: str):
        """Break down a feature into tasks and assign to agents"""
        prompt = f"""You are the Orchestrator for a web application development team.
        Your goal is to break down a new feature request into actionable development tasks.
        The feature is: "{description}"

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
        
        print(f"Orchestrator: Calling LLM to break down feature...")
        response = self._generate_response(prompt)
        print(f"Orchestrator: LLM response received: {response[:100] if response else 'None'}...")
        if response:
            try:
                # Clean response
                cleaned_response = response.strip()
                if cleaned_response.startswith("```json"):
                    cleaned_response = cleaned_response[len("```json"):].strip()
                if cleaned_response.endswith("```"):
                    cleaned_response = cleaned_response[:-len("```")].strip()
                
                tasks = json.loads(cleaned_response)
                
                # Update feature status
                self._features[feature_id]['status'] = 'in_progress'
                
                # Create and assign tasks
                for task_data in tasks:
                    task_id = str(uuid.uuid4())
                    agent = self._normalize_agent_name(task_data["agent"])
                    description = task_data["description"]
                    
                    if agent in self.available_agents:
                        # Store task info
                        self._tasks[task_id] = {
                            'id': task_id,
                            'feature_id': feature_id,
                            'description': description,
                            'assigned_agent': agent,
                            'status': 'assigned',
                            'created_at': time.time(),
                            'retry_count': 0
                        }
                        
                        self._features[feature_id]['tasks'].append(task_id)
                        
                        # Publish task assignment event
                        self.event_bus.publish(Event(
                            id=f"assign-{task_id}",
                            type=EventType.TASK_ASSIGNED,
                            source=self.name,
                            timestamp=time.time(),
                            data={
                                'task_id': task_id,
                                'feature_id': feature_id,
                                'description': description,
                                'assigned_agent': agent
                            },
                            correlation_id=task_id
                        ))
                        
                        print(f"Orchestrator: Assigned task '{description}' to {agent} (Task ID: {task_id})")
                    else:
                        print(f"Orchestrator: Warning - Agent '{agent}' not recognized for task: {description}")
                        
            except Exception as e:
                print(f"Orchestrator: Failed to parse tasks: {e}")
                print(f"Orchestrator: Raw response: {response}")
                self._features[feature_id]['status'] = 'failed'
        else:
            print("Orchestrator: Failed to generate tasks - no response from LLM")
            self._features[feature_id]['status'] = 'failed'
    
    def _normalize_agent_name(self, agent_name: str) -> str:
        """Normalize agent names to standard format"""
        # Agent Name Mapping
        mappings = {
            "database_architect_agent": "db_agent",
            "Database Architect Agent": "db_agent",
            "frontend_developer_agent": "frontend_agent",
            "Frontend Developer Agent": "frontend_agent",
            "backend_developer_agent": "backend_agent",
            "Backend Developer Agent": "backend_agent",
            "qa_testing_agent": "qa_agent",
            "QA & Testing Agent": "qa_agent",
            "documentation_agent": "docs_agent",
            "Documentation Agent": "docs_agent",
            "Security Agent": "security_agent",
            "devops_infrastructure_agent": "devops_agent",
            "DevOps & Infrastructure Agent": "devops_agent"
        }
        
        return mappings.get(agent_name, agent_name)
    
    def _handle_task_completed(self, event: Event):
        """Handle task completion event"""
        task_id = event.data.get('task_id')
        if not task_id or task_id not in self._tasks:
            return
        
        task = self._tasks[task_id]
        task['status'] = 'completed'
        task['completed_at'] = event.timestamp
        task['result'] = event.data.get('result')
        
        print(f"Orchestrator: Task '{task['description']}' completed by {event.source}")
        
        # Update state manager
        self.state_manager.update_task_status(task_id, "completed", task['result'])
        
        # Check if feature is complete
        self._check_feature_completion(task['feature_id'])
    
    def _handle_task_failed(self, event: Event):
        """Handle task failure event"""
        task_id = event.data.get('task_id')
        if not task_id or task_id not in self._tasks:
            return
        
        task = self._tasks[task_id]
        error = event.data.get('error', 'Unknown error')
        
        print(f"Orchestrator: Task '{task['description']}' failed: {error}")
        
        # Check retry logic
        if task['retry_count'] < config.MAX_RETRY_ATTEMPTS:
            task['retry_count'] += 1
            task['status'] = 'retrying'
            
            print(f"Orchestrator: Retrying task {task_id} (attempt {task['retry_count']}/{config.MAX_RETRY_ATTEMPTS})")
            
            # Publish retry event
            self.event_bus.publish(Event(
                id=f"retry-{task_id}",
                type=EventType.TASK_RETRY,
                source=self.name,
                timestamp=time.time(),
                data={
                    'task_id': task_id,
                    'feature_id': task['feature_id'],
                    'description': task['description'],
                    'assigned_agent': task['assigned_agent'],
                    'retry_count': task['retry_count'],
                    'previous_error': error
                },
                correlation_id=task_id
            ))
        else:
            task['status'] = 'failed_permanently'
            task['final_error'] = error
            
            print(f"Orchestrator: Task {task_id} permanently failed after {config.MAX_RETRY_ATTEMPTS} attempts")
            
            # Update state manager
            self.state_manager.update_task_status(
                task_id, 
                "failed_permanently", 
                f"Failed after {config.MAX_RETRY_ATTEMPTS} retries. Last error: {error}"
            )
            
            # Check if feature should be blocked
            self._check_feature_completion(task['feature_id'])
    
    def _handle_agent_error(self, event: Event):
        """Handle agent error events"""
        error_data = event.data
        agent = event.source
        
        print(f"Orchestrator: Agent error from {agent}: {error_data.get('error', 'Unknown error')}")
        
        # Could implement agent restart logic here
    
    def _handle_custom_event(self, event: Event):
        """Handle custom events like new feature requests"""
        print(f"Orchestrator: Received CUSTOM event with event_name: {event.data.get('event_name')}")
        try:
            if event.data.get('event_name') == 'new_feature_request':
                # Create a new feature
                feature_description = event.data.get('description', '')
                if feature_description:
                    feature_id = str(uuid.uuid4())
                    
                    print(f"Orchestrator: Creating new feature from request: {feature_description}")
                    
                    # Publish feature created event
                    self.event_bus.publish(Event(
                        id=f"feature-{feature_id}",
                        type=EventType.FEATURE_CREATED,
                        source=self.name,
                        timestamp=time.time(),
                        data={
                            'feature_id': feature_id,
                            'description': feature_description
                        }
                    ))
        except Exception as e:
            print(f"Orchestrator: ERROR in _handle_custom_event: {e}")
            import traceback
            traceback.print_exc()
    
    def _check_feature_completion(self, feature_id: str):
        """Check if all tasks for a feature are complete"""
        if feature_id not in self._features:
            return
        
        feature = self._features[feature_id]
        task_ids = feature['tasks']
        
        all_completed = all(
            self._tasks[tid]['status'] == 'completed' 
            for tid in task_ids if tid in self._tasks
        )
        
        any_failed = any(
            self._tasks[tid]['status'] == 'failed_permanently' 
            for tid in task_ids if tid in self._tasks
        )
        
        if all_completed:
            feature['status'] = 'completed'
            print(f"Orchestrator: Feature '{feature['description']}' is COMPLETE!")
            
            # Publish feature completed event
            self.event_bus.publish(Event(
                id=f"feature-complete-{feature_id}",
                type=EventType.FEATURE_COMPLETED,
                source=self.name,
                timestamp=time.time(),
                data={
                    'feature_id': feature_id,
                    'description': feature['description'],
                    'task_count': len(task_ids)
                }
            ))
            
        elif any_failed:
            feature['status'] = 'blocked'
            failed_count = sum(
                1 for tid in task_ids 
                if tid in self._tasks and self._tasks[tid]['status'] == 'failed_permanently'
            )
            
            print(f"Orchestrator: Feature '{feature['description']}' is BLOCKED ({failed_count} failed tasks)")
            
            # Publish feature blocked event
            self.event_bus.publish(Event(
                id=f"feature-blocked-{feature_id}",
                type=EventType.FEATURE_BLOCKED,
                source=self.name,
                timestamp=time.time(),
                data={
                    'feature_id': feature_id,
                    'description': feature['description'],
                    'failed_tasks': failed_count
                }
            ))
    
    def process_task(self, task_id: str, task_data: Dict[str, Any]) -> Any:
        """
        Process orchestrator-specific tasks
        
        The orchestrator mainly responds to events, but this method
        can handle direct task assignments if needed.
        """
        task_type = task_data.get('type', '')
        
        if task_type == 'health_check':
            return self._perform_health_check()
        elif task_type == 'recovery_check':
            return self._perform_recovery_check()
        else:
            return f"Orchestrator processed task: {task_id}"
    
    def _perform_health_check(self) -> Dict[str, Any]:
        """Perform system health check"""
        health_report = {
            'timestamp': datetime.now().isoformat(),
            'features': {
                'total': len(self._features),
                'in_progress': sum(1 for f in self._features.values() if f['status'] == 'in_progress'),
                'completed': sum(1 for f in self._features.values() if f['status'] == 'completed'),
                'blocked': sum(1 for f in self._features.values() if f['status'] == 'blocked')
            },
            'tasks': {
                'total': len(self._tasks),
                'assigned': sum(1 for t in self._tasks.values() if t['status'] == 'assigned'),
                'completed': sum(1 for t in self._tasks.values() if t['status'] == 'completed'),
                'failed': sum(1 for t in self._tasks.values() if t['status'] == 'failed_permanently'),
                'retrying': sum(1 for t in self._tasks.values() if t['status'] == 'retrying')
            },
            'available_agents': self.available_agents
        }
        
        print(f"Orchestrator: Health check - {health_report['tasks']['total']} tasks, "
              f"{health_report['features']['in_progress']} features in progress")
        
        return health_report
    
    def _perform_recovery_check(self) -> Dict[str, Any]:
        """Perform recovery operations"""
        recovery_report = {
            'timestamp': datetime.now().isoformat(),
            'recovered_tasks': 0,
            'retried_tasks': 0
        }
        
        # Check for stalled tasks (assigned but not started/completed after timeout)
        timeout = timedelta(minutes=config.TASK_TIMEOUT_MINUTES)
        current_time = time.time()
        
        for task_id, task in self._tasks.items():
            if task['status'] == 'assigned':
                task_age = current_time - task['created_at']
                if task_age > timeout.total_seconds():
                    # Re-publish assignment
                    self.event_bus.publish(Event(
                        id=f"recover-{task_id}",
                        type=EventType.TASK_ASSIGNED,
                        source=self.name,
                        timestamp=time.time(),
                        data={
                            'task_id': task_id,
                            'feature_id': task['feature_id'],
                            'description': task['description'],
                            'assigned_agent': task['assigned_agent'],
                            'recovery': True
                        },
                        correlation_id=task_id
                    ))
                    recovery_report['recovered_tasks'] += 1
        
        if recovery_report['recovered_tasks'] > 0:
            print(f"Orchestrator: Recovered {recovery_report['recovered_tasks']} stalled tasks")
        
        return recovery_report
    
    def start(self):
        """Start the orchestrator with periodic health checks"""
        super().start()
        
        # Schedule periodic health checks
        import threading
        
        def periodic_checks():
            while self._running:
                current_time = datetime.now()
                
                # Health check every 5 minutes
                if current_time - self._last_health_check > timedelta(minutes=5):
                    self._perform_health_check()
                    self._last_health_check = current_time
                
                # Recovery check every 10 minutes
                if current_time - self._last_recovery_check > timedelta(minutes=10):
                    self._perform_recovery_check()
                    self._last_recovery_check = current_time
                
                time.sleep(60)  # Check every minute
        
        check_thread = threading.Thread(target=periodic_checks, daemon=True)
        check_thread.start()


if __name__ == "__main__":
    # Example usage
    orchestrator = EventDrivenOrchestratorAgent()
    orchestrator.run()