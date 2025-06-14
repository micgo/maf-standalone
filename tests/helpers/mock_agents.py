"""
Mock agents for testing that don't require LLM initialization
"""

import os
import time
import threading
import uuid
from typing import Dict, Any, Optional

from multi_agent_framework.core.event_bus_interface import Event, EventType
from multi_agent_framework.core.shared_state_manager import SharedStateManager


class MockAgent:
    """Base mock agent for testing"""
    
    def __init__(self, name: str, project_config=None):
        self.name = name
        self.project_config = project_config
        self.project_root = project_config.project_root if project_config else os.getcwd()
        self.state_manager = SharedStateManager()
        self.event_bus = None  # Will be set by start()
        self._running = False
        self._active_tasks = {}
        self._task_lock = threading.Lock()
        
    def start(self):
        """Start the agent"""
        # Get the global event bus
        from multi_agent_framework.core.event_bus_factory import get_event_bus
        self.event_bus = get_event_bus()
        
        self._running = True
        self._subscribe_to_events()
        print(f"{self.name}: Started in test mode")
        
    def stop(self):
        """Stop the agent"""
        self._running = False
        
        # Publish agent stopped event
        if self.event_bus:
            self.event_bus.publish(Event(
                id=f"{self.name}-stopped-{time.time()}",
                type=EventType.AGENT_STOPPED,
                source=self.name,
                timestamp=time.time(),
                data={"agent_name": self.name}
            ))
        
        print(f"{self.name}: Stopped")
        
    def _subscribe_to_events(self):
        """Subscribe to relevant events"""
        self.event_bus.subscribe(EventType.SYSTEM_SHUTDOWN, self._handle_shutdown)
        self.event_bus.subscribe(EventType.TASK_ASSIGNED, self._handle_task_assigned)
        self.event_bus.subscribe(EventType.SYSTEM_HEALTH_CHECK, self._handle_health_check)
        
    def _handle_shutdown(self, event: Event):
        """Handle shutdown event"""
        print(f"{self.name}: Received shutdown event")
        self.stop()
        
    def _handle_task_assigned(self, event: Event):
        """Handle task assignment"""
        data = event.data
        
        # Check if task is for this agent
        if data.get("assigned_agent") != self.name:
            return
            
        task_id = data.get("task_id")
        if not task_id:
            return
            
        print(f"{self.name}: Received task assignment: {task_id}")
        
        # Process task in separate thread
        threading.Thread(
            target=self._process_task_safe,
            args=(task_id, data),
            daemon=True
        ).start()
        
    def _process_task_safe(self, task_id: str, task_data: Dict[str, Any]):
        """Process task safely"""
        try:
            # Store task
            with self._task_lock:
                self._active_tasks[task_id] = task_data
                
            # Publish task started
            self.event_bus.publish(Event(
                id=f"{self.name}-started-{task_id}",
                type=EventType.TASK_STARTED,
                source=self.name,
                timestamp=time.time(),
                data={"task_id": task_id}
            ))
            
            # Process the task
            result = self.process_task(task_id, task_data)
            
            # Publish task completed
            self.event_bus.publish(Event(
                id=f"{self.name}-completed-{task_id}",
                type=EventType.TASK_COMPLETED,
                source=self.name,
                timestamp=time.time(),
                data={
                    "task_id": task_id,
                    "result": result,
                    "success": True
                }
            ))
            
        except Exception as e:
            # Publish task failed
            self.event_bus.publish(Event(
                id=f"{self.name}-failed-{task_id}",
                type=EventType.TASK_FAILED,
                source=self.name,
                timestamp=time.time(),
                data={
                    "task_id": task_id,
                    "error": str(e),
                    "success": False
                }
            ))
            
        finally:
            # Remove from active tasks
            with self._task_lock:
                self._active_tasks.pop(task_id, None)
                
    def _handle_health_check(self, event: Event):
        """Handle health check"""
        self.event_bus.publish(Event(
            id=f"{self.name}-health-{time.time()}",
            type=EventType.AGENT_HEARTBEAT,
            source=self.name,
            timestamp=time.time(),
            data={
                "agent": self.name,
                "active_tasks": len(self._active_tasks),
                "status": "healthy"
            }
        ))
        
    def process_task(self, task_id: str, task_data: Dict[str, Any]) -> Any:
        """Process task - to be overridden by specific agents"""
        # Default implementation
        time.sleep(0.1)  # Simulate work
        return {"message": f"Task {task_id} completed by {self.name}"}


class MockBackendAgent(MockAgent):
    """Mock backend agent"""
    
    def __init__(self, project_config=None):
        super().__init__("backend_agent", project_config)
        self._apis_created = 0
        
    def process_task(self, task_id: str, task_data: Dict[str, Any]) -> Any:
        """Process backend task"""
        description = task_data.get('description', '')
        print(f"{self.name}: Processing task - {description}")
        
        time.sleep(0.1)  # Simulate work
        
        if 'api' in description.lower() or 'endpoint' in description.lower():
            self._apis_created += 1
            return {
                'type': 'api_route',
                'files_created': [f'/api/test_{task_id}.py'],
                'api_endpoint': f'/api/{task_id}'
            }
        else:
            return {'type': 'generic', 'message': f'Completed: {description}'}


class MockFrontendAgent(MockAgent):
    """Mock frontend agent"""
    
    def __init__(self, project_config=None):
        super().__init__("frontend_agent", project_config)
        self._components_created = 0
        
    def process_task(self, task_id: str, task_data: Dict[str, Any]) -> Any:
        """Process frontend task"""
        description = task_data.get('description', '')
        print(f"{self.name}: Processing task - {description}")
        
        time.sleep(0.1)  # Simulate work
        
        if 'component' in description.lower() or 'ui' in description.lower():
            self._components_created += 1
            return {
                'type': 'component',
                'files_created': [f'/components/Test{task_id}.tsx'],
                'component_name': f'Test{task_id}'
            }
        else:
            return {'type': 'generic', 'message': f'Completed: {description}'}


class MockDatabaseAgent(MockAgent):
    """Mock database agent"""
    
    def __init__(self, project_config=None):
        super().__init__("database_agent", project_config)
        
    def process_task(self, task_id: str, task_data: Dict[str, Any]) -> Any:
        """Process database task"""
        description = task_data.get('description', '')
        print(f"{self.name}: Processing task - {description}")
        
        time.sleep(0.1)  # Simulate work
        
        if 'schema' in description.lower() or 'table' in description.lower():
            return {
                'type': 'schema',
                'schema': {'tables': ['users', 'products']},
                'files_created': ['/db/schema.sql']
            }
        else:
            return {'type': 'generic', 'message': f'Completed: {description}'}


class MockQAAgent(MockAgent):
    """Mock QA agent"""
    
    def __init__(self, project_config=None):
        super().__init__("qa_agent", project_config)
        
    def process_task(self, task_id: str, task_data: Dict[str, Any]) -> Any:
        """Process QA task"""
        description = task_data.get('description', '')
        print(f"{self.name}: Processing task - {description}")
        
        time.sleep(0.1)  # Simulate work
        
        return {
            'type': 'validation',
            'tests_passed': True,
            'issues_found': [],
            'message': f'Validated: {description}'
        }


class MockSecurityAgent(MockAgent):
    """Mock security agent"""
    
    def __init__(self, project_config=None):
        super().__init__("security_agent", project_config)
        
    def process_task(self, task_id: str, task_data: Dict[str, Any]) -> Any:
        """Process security task"""
        description = task_data.get('description', '')
        print(f"{self.name}: Processing task - {description}")
        
        time.sleep(0.1)  # Simulate work
        
        return {
            'type': 'security_review',
            'vulnerabilities': [],
            'recommendations': ['Use HTTPS', 'Add input validation'],
            'message': f'Security review completed: {description}'
        }


class MockDevOpsAgent(MockAgent):
    """Mock DevOps agent"""
    
    def __init__(self, project_config=None):
        super().__init__("devops_agent", project_config)
        
    def process_task(self, task_id: str, task_data: Dict[str, Any]) -> Any:
        """Process DevOps task"""
        description = task_data.get('description', '')
        print(f"{self.name}: Processing task - {description}")
        
        time.sleep(0.1)  # Simulate work
        
        if 'deploy' in description.lower() or 'docker' in description.lower():
            return {
                'type': 'deployment',
                'files_created': ['Dockerfile', 'docker-compose.yml'],
                'message': f'Deployment configured: {description}'
            }
        else:
            return {'type': 'generic', 'message': f'Completed: {description}'}


class MockOrchestratorAgent(MockAgent):
    """Mock orchestrator agent"""
    
    def __init__(self, project_config=None):
        super().__init__("orchestrator_agent", project_config)
        
    def _subscribe_to_events(self):
        """Subscribe to orchestrator-specific events"""
        super()._subscribe_to_events()
        self.event_bus.subscribe(EventType.FEATURE_CREATED, self._handle_feature_created)
        
    def _handle_feature_created(self, event: Event):
        """Handle feature creation by breaking it down into tasks"""
        feature_data = event.data
        feature_id = feature_data.get('feature_id', 'test_feature')
        description = feature_data.get('description', '')
        
        print(f"{self.name}: Breaking down feature: {description}")
        
        # Create mock tasks for frontend and backend
        tasks = [
            {
                'task_id': f'{feature_id}_frontend_task',
                'assigned_agent': 'frontend_agent',
                'description': f'Frontend task for {description}',
                'feature_id': feature_id
            },
            {
                'task_id': f'{feature_id}_backend_task',
                'assigned_agent': 'backend_agent',
                'description': f'Backend task for {description}',
                'feature_id': feature_id
            }
        ]
        
        # Publish task assignments
        for task in tasks:
            self.event_bus.publish(Event(
                id=f"{self.name}-assign-{task['task_id']}",
                type=EventType.TASK_ASSIGNED,
                source=self.name,
                timestamp=time.time(),
                data=task
            ))
            
    def process_task(self, task_id: str, task_data: Dict[str, Any]) -> Any:
        """Process orchestrator task"""
        # Orchestrator doesn't usually process tasks directly
        return {'type': 'orchestration', 'message': 'Task orchestrated'}


# Mock agent factory
MOCK_AGENTS = {
    'backend': MockBackendAgent,
    'frontend': MockFrontendAgent,
    'database': MockDatabaseAgent,
    'qa': MockQAAgent,
    'security': MockSecurityAgent,
    'devops': MockDevOpsAgent,
    'orchestrator': MockOrchestratorAgent
}


def create_mock_agent(agent_type: str, project_config=None):
    """Create a mock agent of the specified type"""
    agent_class = MOCK_AGENTS.get(agent_type)
    if not agent_class:
        raise ValueError(f"Unknown mock agent type: {agent_type}")
    
    return agent_class(project_config=project_config)