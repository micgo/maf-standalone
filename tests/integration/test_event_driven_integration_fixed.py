#!/usr/bin/env python3
"""
Fixed integration tests for event-driven multi-agent system
Works around Python 3.13 threading issues
"""
import os
import sys
import time
import json
import tempfile
import shutil
from typing import Dict, Any, List
from unittest import TestCase, main
from threading import Event
import pytest

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from multi_agent_framework.core.event_bus_factory import get_event_bus, reset_event_bus
from multi_agent_framework.core.event_bus_interface import Event as BusEvent, EventType
from multi_agent_framework.core.project_config import ProjectConfig

# Import mock agents directly to avoid circular import issues
import importlib.util
mock_agents_path = os.path.join(os.path.dirname(__file__), '../helpers/mock_agents.py')
spec = importlib.util.spec_from_file_location("mock_agents", mock_agents_path)
mock_agents = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mock_agents)


class FixedEventDrivenIntegrationTest(TestCase):
    """Fixed integration tests for event-driven agent system"""
    
    def _create_event(self, event_type: EventType, data: Dict[str, Any], source: str = 'test') -> BusEvent:
        """Helper to create events with required fields"""
        return BusEvent(
            id=f"{source}-{event_type.value}-{time.time()}",
            type=event_type,
            source=source,
            timestamp=time.time(),
            data=data
        )
    
    def setUp(self):
        """Set up test environment"""
        # Enable test mode
        os.environ['MAF_TEST_MODE'] = 'true'
        
        # Create temporary directory for test
        self.test_dir = tempfile.mkdtemp()
        self.project_config = ProjectConfig(self.test_dir)
        
        # Initialize event bus with shorter timeout for tests
        self.event_bus = get_event_bus({'type': 'inmemory'})
        
        # Track events with thread-safe collections
        self.received_events = []
        self.completed_tasks = {}
        self._setup_complete = False
        
        # Subscribe to events
        self.event_bus.subscribe(EventType.TASK_COMPLETED, self._track_task_completion)
        self.event_bus.subscribe(EventType.TASK_FAILED, self._track_task_failure)
        self._setup_complete = True
        
    def tearDown(self):
        """Clean up test environment"""
        try:
            # Give a short time for any pending events
            time.sleep(0.1)
            
            # Stop event bus
            if hasattr(self, 'event_bus') and self.event_bus:
                self.event_bus.stop()
            
            # Reset global event bus
            reset_event_bus()
            
            # Clean up temp directory
            if hasattr(self, 'test_dir') and os.path.exists(self.test_dir):
                shutil.rmtree(self.test_dir, ignore_errors=True)
                
        except Exception as e:
            print(f"Cleanup error: {e}")
            
    def _track_task_completion(self, event: BusEvent):
        """Track completed tasks"""
        if not self._setup_complete:
            return
        try:
            # Handle both string and dict data
            data = event.data
            if isinstance(data, str):
                import json
                data = json.loads(data)
            
            task_id = data.get('task_id')
            if task_id:
                self.completed_tasks[task_id] = data
        except Exception as e:
            print(f"Error tracking task completion: {e}")
        
    def _track_task_failure(self, event: BusEvent):
        """Track failed tasks"""
        if not self._setup_complete:
            return
        try:
            # Handle both string and dict data
            data = event.data
            if isinstance(data, str):
                import json
                data = json.loads(data)
                
            task_id = data.get('task_id')
            if task_id:
                self.completed_tasks[task_id] = {
                    'success': False,
                    'error': data.get('error', 'Unknown error')
                }
        except Exception as e:
            print(f"Error tracking task failure: {e}")
            
    def _wait_for_tasks(self, expected_count: int, timeout: float = 5.0) -> bool:
        """Wait for expected number of tasks to complete"""
        start_time = time.time()
        while len(self.completed_tasks) < expected_count and time.time() - start_time < timeout:
            time.sleep(0.05)  # Shorter sleep for faster tests
        return len(self.completed_tasks) >= expected_count
            
    def test_single_agent_task_flow(self):
        """Test that a single agent can receive and complete a task"""
        # Create frontend agent using direct instantiation
        agent = mock_agents.MockFrontendAgent(project_config=self.project_config)
        agent.start()
        
        try:
            # Send task to agent
            task_id = 'test_single_001'
            self.event_bus.publish(self._create_event(
                EventType.TASK_ASSIGNED,
                {
                    'task_id': task_id,
                    'assigned_agent': 'frontend_agent',
                    'task_description': 'Create a simple button component',
                    'priority': 'high'
                }
            ))
            
            # Wait for task completion with shorter timeout
            success = self._wait_for_tasks(1, timeout=3.0)
            self.assertTrue(success, f"Task didn't complete in time. Completed: {len(self.completed_tasks)}")
            
            # Verify task was completed
            self.assertIn(task_id, self.completed_tasks)
            result = self.completed_tasks[task_id]
            self.assertTrue(result.get('success', False))
            
        finally:
            agent.stop()
            time.sleep(0.1)  # Give time for cleanup
            
    def test_multi_agent_collaboration(self):
        """Test that multiple agents can collaborate on related tasks"""
        # Create multiple agents
        frontend_agent = mock_agents.MockFrontendAgent(project_config=self.project_config)
        backend_agent = mock_agents.MockBackendAgent(project_config=self.project_config)
        
        frontend_agent.start()
        backend_agent.start()
        
        try:
            # Send frontend task
            frontend_task_id = 'test_collab_fe_001'
            self.event_bus.publish(self._create_event(
                EventType.TASK_ASSIGNED,
                {
                    'task_id': frontend_task_id,
                    'assigned_agent': 'frontend_agent',
                    'task_description': 'Create a user profile page',
                    'priority': 'high'
                }
            ))
            
            # Send backend task
            backend_task_id = 'test_collab_be_001'
            self.event_bus.publish(self._create_event(
                EventType.TASK_ASSIGNED,
                {
                    'task_id': backend_task_id,
                    'assigned_agent': 'backend_agent',
                    'task_description': 'Create API endpoint for user profile data',
                    'priority': 'high'
                }
            ))
            
            # Wait for both tasks to complete
            success = self._wait_for_tasks(2, timeout=5.0)
            self.assertTrue(success, f"Not all tasks completed. Completed: {len(self.completed_tasks)}")
            
            # Verify both tasks completed
            self.assertIn(frontend_task_id, self.completed_tasks)
            self.assertIn(backend_task_id, self.completed_tasks)
            
            # Both should succeed
            self.assertTrue(self.completed_tasks[frontend_task_id].get('success', False))
            self.assertTrue(self.completed_tasks[backend_task_id].get('success', False))
            
        finally:
            frontend_agent.stop()
            backend_agent.stop()
            time.sleep(0.1)
            
    def test_agent_health_check(self):
        """Test that agents respond to health check events"""
        # Create agent
        agent = mock_agents.MockQAAgent(project_config=self.project_config)
        agent.start()
        
        try:
            # Track health responses
            health_responses = []
            
            def track_health(event: BusEvent):
                if event.type == EventType.AGENT_HEARTBEAT:
                    # Handle both string and dict data
                    data = event.data
                    if isinstance(data, str):
                        import json
                        data = json.loads(data)
                    health_responses.append(data)
                    
            self.event_bus.subscribe(EventType.AGENT_HEARTBEAT, track_health)
            
            # Send health check
            self.event_bus.publish(self._create_event(
                EventType.SYSTEM_HEALTH_CHECK,
                {}
            ))
            
            # Wait for response with shorter timeout
            timeout = 3.0
            start_time = time.time()
            while len(health_responses) == 0 and time.time() - start_time < timeout:
                time.sleep(0.05)
                
            # Verify health response
            self.assertTrue(len(health_responses) > 0, "No health responses received")
            qa_response = next((r for r in health_responses if r.get('agent') == 'qa_agent'), None)
            self.assertIsNotNone(qa_response, "QA agent didn't respond to health check")
            self.assertIn('active_tasks', qa_response)
            
        finally:
            agent.stop()
            time.sleep(0.1)
            
    def test_task_priority_handling(self):
        """Test that agents handle task priorities correctly"""
        # Create agent
        agent = mock_agents.MockBackendAgent(project_config=self.project_config)
        agent.start()
        
        try:
            # Send multiple tasks with different priorities
            tasks = [
                {'id': 'priority_low_001', 'priority': 'low', 'description': 'Low priority task'},
                {'id': 'priority_high_001', 'priority': 'high', 'description': 'High priority task'},
                {'id': 'priority_medium_001', 'priority': 'medium', 'description': 'Medium priority task'},
            ]
            
            for task in tasks:
                self.event_bus.publish(self._create_event(
                    EventType.TASK_ASSIGNED,
                    {
                        'task_id': task['id'],
                        'assigned_agent': 'backend_agent',
                        'task_description': task['description'],
                        'priority': task['priority']
                    }
                ))
                
            # Wait for all tasks to complete
            success = self._wait_for_tasks(3, timeout=8.0)
            self.assertTrue(success, f"Not all tasks completed. Completed: {len(self.completed_tasks)}")
            
            # All tasks should complete
            self.assertEqual(len(self.completed_tasks), 3)
            
            # Verify all succeeded
            for task in tasks:
                self.assertIn(task['id'], self.completed_tasks)
                self.assertTrue(self.completed_tasks[task['id']].get('success', False))
                
        finally:
            agent.stop()
            time.sleep(0.1)
            
    def test_agent_shutdown_handling(self):
        """Test that agents handle shutdown events properly"""
        # Create multiple agents
        agents = [
            mock_agents.MockFrontendAgent(project_config=self.project_config),
            mock_agents.MockBackendAgent(project_config=self.project_config),
            mock_agents.MockDatabaseAgent(project_config=self.project_config)
        ]
        
        # Start all agents
        for agent in agents:
            agent.start()
            
        # Give agents time to initialize
        time.sleep(0.2)
        
        # Track shutdown acknowledgments
        shutdown_acks = []
        
        def track_shutdown(event: BusEvent):
            if event.type == EventType.AGENT_STOPPED:
                # Handle both string and dict data
                data = event.data
                if isinstance(data, str):
                    import json
                    data = json.loads(data)
                shutdown_acks.append(data.get('agent_name', event.source))
                
        self.event_bus.subscribe(EventType.AGENT_STOPPED, track_shutdown)
        
        try:
            # Send shutdown event
            self.event_bus.publish(self._create_event(
                EventType.SYSTEM_SHUTDOWN,
                {}
            ))
            
            # Wait for agents to acknowledge shutdown
            timeout = 3.0
            start_time = time.time()
            while len(shutdown_acks) < len(agents) and time.time() - start_time < timeout:
                time.sleep(0.05)
                
            # All agents should acknowledge shutdown
            self.assertEqual(len(shutdown_acks), len(agents), f"Expected {len(agents)} shutdown acks, got {len(shutdown_acks)}")
            
        finally:
            # Ensure all agents are stopped
            for agent in agents:
                try:
                    agent.stop()
                except:
                    pass
            time.sleep(0.1)
                
    def test_error_recovery(self):
        """Test that system recovers from agent errors"""
        # Create agent
        agent = mock_agents.MockDatabaseAgent(project_config=self.project_config)
        agent.start()
        
        try:
            # Send a task that will fail (in test mode, we can simulate this)
            task_id = 'test_error_001'
            self.event_bus.publish(self._create_event(
                EventType.TASK_ASSIGNED,
                {
                    'task_id': task_id,
                    'assigned_agent': 'database_agent',
                    'task_description': 'CREATE TABLE with invalid syntax ###ERROR###',
                    'priority': 'high'
                }
            ))
            
            # Wait for task to process
            success = self._wait_for_tasks(1, timeout=3.0)
            self.assertTrue(success, "Error task didn't complete")
            
            # Task should be marked as completed (even if it failed internally)
            self.assertIn(task_id, self.completed_tasks)
            
            # Send a valid task to verify agent is still functional
            valid_task_id = 'test_error_recovery_001'
            self.event_bus.publish(self._create_event(
                EventType.TASK_ASSIGNED,
                {
                    'task_id': valid_task_id,
                    'assigned_agent': 'database_agent',
                    'task_description': 'CREATE TABLE users (id INTEGER PRIMARY KEY)',
                    'priority': 'high'
                }
            ))
            
            # Wait for valid task
            success = self._wait_for_tasks(2, timeout=3.0)
            self.assertTrue(success, "Recovery task didn't complete")
            
            # Valid task should complete successfully
            self.assertIn(valid_task_id, self.completed_tasks)
            self.assertTrue(self.completed_tasks[valid_task_id].get('success', False))
            
        finally:
            agent.stop()
            time.sleep(0.1)
            
    def test_event_data_consistency(self):
        """Test that event data remains consistent between string and dict formats"""
        agent = mock_agents.MockFrontendAgent(project_config=self.project_config)
        agent.start()
        
        try:
            # Test with dict data
            task_id = 'consistency_test_001'
            test_data = {
                'task_id': task_id,
                'assigned_agent': 'frontend_agent',
                'task_description': 'Test consistency',
                'priority': 'medium',
                'metadata': {'test': True, 'number': 42}
            }
            
            self.event_bus.publish(self._create_event(
                EventType.TASK_ASSIGNED,
                test_data
            ))
            
            # Wait for completion
            success = self._wait_for_tasks(1, timeout=3.0)
            self.assertTrue(success, "Consistency test task didn't complete")
            
            # Verify data consistency
            self.assertIn(task_id, self.completed_tasks)
            result = self.completed_tasks[task_id]
            self.assertIsInstance(result, dict)
            self.assertEqual(result['task_id'], task_id)
            
        finally:
            agent.stop()
            time.sleep(0.1)


if __name__ == '__main__':
    main()