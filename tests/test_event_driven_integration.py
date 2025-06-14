#!/usr/bin/env python3
"""
Integration tests for event-driven multi-agent system
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

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from multi_agent_framework.core.event_bus_factory import get_event_bus
from multi_agent_framework.core.event_bus_interface import Event as BusEvent, EventType
from multi_agent_framework.core.project_config import ProjectConfig
from multi_agent_framework.core.agent_factory import create_agent
from multi_agent_framework.core.task_manager import TaskManager


class EventDrivenIntegrationTest(TestCase):
    """Integration tests for event-driven agent system"""
    
    def setUp(self):
        """Set up test environment"""
        # Enable test mode
        os.environ['MAF_TEST_MODE'] = 'true'
        
        # Create temporary directory for test
        self.test_dir = tempfile.mkdtemp()
        self.project_config = ProjectConfig(self.test_dir)
        
        # Initialize event bus
        self.event_bus = get_event_bus('inmemory')
        
        # Track events
        self.received_events = []
        self.completed_tasks = {}
        
        # Subscribe to events
        self.event_bus.subscribe(EventType.TASK_COMPLETED, self._track_task_completion)
        self.event_bus.subscribe(EventType.TASK_FAILED, self._track_task_failure)
        
    def tearDown(self):
        """Clean up test environment"""
        # Stop event bus
        self.event_bus.stop()
        
        # Clean up temp directory
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
            
    def _track_task_completion(self, event: BusEvent):
        """Track completed tasks"""
        self.completed_tasks[event.data['task_id']] = event.data
        
    def _track_task_failure(self, event: BusEvent):
        """Track failed tasks"""
        self.completed_tasks[event.data['task_id']] = {
            'success': False,
            'error': event.data.get('error', 'Unknown error')
        }
        
    def test_single_agent_task_flow(self):
        """Test that a single agent can receive and complete a task"""
        # Create frontend agent
        agent = create_agent('frontend', mode='event_driven', project_config=self.project_config)
        agent.start()
        
        try:
            # Send task to agent
            task_id = 'test_single_001'
            self.event_bus.publish(BusEvent(
                type=EventType.TASK_ASSIGNED,
                data={
                    'task_id': task_id,
                    'agent_name': 'frontend_agent',
                    'task_description': 'Create a simple button component',
                    'priority': 'high'
                }
            ))
            
            # Wait for task completion
            timeout = 10
            start_time = time.time()
            while task_id not in self.completed_tasks and time.time() - start_time < timeout:
                time.sleep(0.1)
                
            # Verify task was completed
            self.assertIn(task_id, self.completed_tasks)
            result = self.completed_tasks[task_id]
            self.assertTrue(result.get('success', False))
            
        finally:
            agent.stop()
            
    def test_multi_agent_collaboration(self):
        """Test that multiple agents can collaborate on related tasks"""
        # Create multiple agents
        frontend_agent = create_agent('frontend', mode='event_driven', project_config=self.project_config)
        backend_agent = create_agent('backend', mode='event_driven', project_config=self.project_config)
        
        frontend_agent.start()
        backend_agent.start()
        
        try:
            # Send frontend task
            frontend_task_id = 'test_collab_fe_001'
            self.event_bus.publish(BusEvent(
                type=EventType.TASK_ASSIGNED,
                data={
                    'task_id': frontend_task_id,
                    'agent_name': 'frontend_agent',
                    'task_description': 'Create a user profile page',
                    'priority': 'high'
                }
            ))
            
            # Send backend task
            backend_task_id = 'test_collab_be_001'
            self.event_bus.publish(BusEvent(
                type=EventType.TASK_ASSIGNED,
                data={
                    'task_id': backend_task_id,
                    'agent_name': 'backend_agent',
                    'task_description': 'Create API endpoint for user profile data',
                    'priority': 'high'
                }
            ))
            
            # Wait for both tasks to complete
            timeout = 15
            start_time = time.time()
            while (len(self.completed_tasks) < 2 and time.time() - start_time < timeout):
                time.sleep(0.1)
                
            # Verify both tasks completed
            self.assertIn(frontend_task_id, self.completed_tasks)
            self.assertIn(backend_task_id, self.completed_tasks)
            
            # Both should succeed
            self.assertTrue(self.completed_tasks[frontend_task_id].get('success', False))
            self.assertTrue(self.completed_tasks[backend_task_id].get('success', False))
            
        finally:
            frontend_agent.stop()
            backend_agent.stop()
            
    def test_agent_health_check(self):
        """Test that agents respond to health check events"""
        # Create agent
        agent = create_agent('qa', mode='event_driven', project_config=self.project_config)
        agent.start()
        
        try:
            # Track health responses
            health_responses = []
            
            def track_health(event: BusEvent):
                if event.type == EventType.AGENT_STATUS:
                    health_responses.append(event.data)
                    
            self.event_bus.subscribe(EventType.AGENT_STATUS, track_health)
            
            # Send health check
            self.event_bus.publish(BusEvent(
                type=EventType.SYSTEM_HEALTH_CHECK,
                data={}
            ))
            
            # Wait for response
            timeout = 5
            start_time = time.time()
            while len(health_responses) == 0 and time.time() - start_time < timeout:
                time.sleep(0.1)
                
            # Verify health response
            self.assertTrue(len(health_responses) > 0)
            qa_response = next((r for r in health_responses if r['agent_name'] == 'qa_agent'), None)
            self.assertIsNotNone(qa_response)
            self.assertEqual(qa_response['status'], 'running')
            
        finally:
            agent.stop()
            
    def test_task_priority_handling(self):
        """Test that agents handle task priorities correctly"""
        # Create agent
        agent = create_agent('backend', mode='event_driven', project_config=self.project_config)
        agent.start()
        
        try:
            # Send multiple tasks with different priorities
            tasks = [
                {'id': 'priority_low_001', 'priority': 'low', 'description': 'Low priority task'},
                {'id': 'priority_high_001', 'priority': 'high', 'description': 'High priority task'},
                {'id': 'priority_medium_001', 'priority': 'medium', 'description': 'Medium priority task'},
            ]
            
            for task in tasks:
                self.event_bus.publish(BusEvent(
                    type=EventType.TASK_ASSIGNED,
                    data={
                        'task_id': task['id'],
                        'agent_name': 'backend_agent',
                        'task_description': task['description'],
                        'priority': task['priority']
                    }
                ))
                
            # Wait for all tasks to complete
            timeout = 20
            start_time = time.time()
            while len(self.completed_tasks) < 3 and time.time() - start_time < timeout:
                time.sleep(0.1)
                
            # All tasks should complete
            self.assertEqual(len(self.completed_tasks), 3)
            
            # Verify all succeeded
            for task in tasks:
                self.assertIn(task['id'], self.completed_tasks)
                self.assertTrue(self.completed_tasks[task['id']].get('success', False))
                
        finally:
            agent.stop()
            
    def test_agent_shutdown_handling(self):
        """Test that agents handle shutdown events properly"""
        # Create multiple agents
        agents = [
            create_agent('frontend', mode='event_driven', project_config=self.project_config),
            create_agent('backend', mode='event_driven', project_config=self.project_config),
            create_agent('database', mode='event_driven', project_config=self.project_config)
        ]
        
        # Start all agents
        for agent in agents:
            agent.start()
            
        # Give agents time to initialize
        time.sleep(1)
        
        # Track shutdown acknowledgments
        shutdown_acks = []
        
        def track_shutdown(event: BusEvent):
            if event.type == EventType.AGENT_STATUS and event.data.get('status') == 'stopped':
                shutdown_acks.append(event.data['agent_name'])
                
        self.event_bus.subscribe(EventType.AGENT_STATUS, track_shutdown)
        
        try:
            # Send shutdown event
            self.event_bus.publish(BusEvent(
                type=EventType.SYSTEM_SHUTDOWN,
                data={}
            ))
            
            # Wait for agents to acknowledge shutdown
            timeout = 5
            start_time = time.time()
            while len(shutdown_acks) < len(agents) and time.time() - start_time < timeout:
                time.sleep(0.1)
                
            # All agents should acknowledge shutdown
            self.assertEqual(len(shutdown_acks), len(agents))
            
        finally:
            # Ensure all agents are stopped
            for agent in agents:
                agent.stop()
                
    def test_error_recovery(self):
        """Test that system recovers from agent errors"""
        # Create agent
        agent = create_agent('database', mode='event_driven', project_config=self.project_config)
        agent.start()
        
        try:
            # Send a task that will fail (in test mode, we can simulate this)
            task_id = 'test_error_001'
            self.event_bus.publish(BusEvent(
                type=EventType.TASK_ASSIGNED,
                data={
                    'task_id': task_id,
                    'agent_name': 'database_agent',
                    'task_description': 'CREATE TABLE with invalid syntax ###ERROR###',
                    'priority': 'high'
                }
            ))
            
            # Wait for task to process
            timeout = 10
            start_time = time.time()
            while task_id not in self.completed_tasks and time.time() - start_time < timeout:
                time.sleep(0.1)
                
            # Task should be marked as completed (even if it failed internally)
            self.assertIn(task_id, self.completed_tasks)
            
            # Send a valid task to verify agent is still functional
            valid_task_id = 'test_error_recovery_001'
            self.event_bus.publish(BusEvent(
                type=EventType.TASK_ASSIGNED,
                data={
                    'task_id': valid_task_id,
                    'agent_name': 'database_agent',
                    'task_description': 'CREATE TABLE users (id INTEGER PRIMARY KEY)',
                    'priority': 'high'
                }
            ))
            
            # Wait for valid task
            start_time = time.time()
            while valid_task_id not in self.completed_tasks and time.time() - start_time < timeout:
                time.sleep(0.1)
                
            # Valid task should complete successfully
            self.assertIn(valid_task_id, self.completed_tasks)
            self.assertTrue(self.completed_tasks[valid_task_id].get('success', False))
            
        finally:
            agent.stop()
            
    def test_concurrent_task_handling(self):
        """Test that agents can handle multiple concurrent tasks"""
        # Create agent
        agent = create_agent('devops', mode='event_driven', project_config=self.project_config)
        agent.start()
        
        try:
            # Send multiple tasks rapidly
            task_ids = []
            for i in range(5):
                task_id = f'concurrent_test_{i:03d}'
                task_ids.append(task_id)
                self.event_bus.publish(BusEvent(
                    type=EventType.TASK_ASSIGNED,
                    data={
                        'task_id': task_id,
                        'agent_name': 'devops_agent',
                        'task_description': f'Create Dockerfile for service {i}',
                        'priority': 'medium'
                    }
                ))
                
            # Wait for all tasks to complete
            timeout = 30
            start_time = time.time()
            while len(self.completed_tasks) < len(task_ids) and time.time() - start_time < timeout:
                time.sleep(0.1)
                
            # All tasks should complete
            self.assertEqual(len(self.completed_tasks), len(task_ids))
            
            # Verify all succeeded
            for task_id in task_ids:
                self.assertIn(task_id, self.completed_tasks)
                self.assertTrue(self.completed_tasks[task_id].get('success', False))
                
        finally:
            agent.stop()
            
    def test_cross_agent_validation(self):
        """Test cross-agent validation functionality"""
        # Create frontend and backend agents
        frontend_agent = create_agent('frontend', mode='event_driven', project_config=self.project_config)
        backend_agent = create_agent('backend', mode='event_driven', project_config=self.project_config)
        
        frontend_agent.start()
        backend_agent.start()
        
        try:
            # Create API endpoint task for backend
            backend_task_id = 'api_endpoint_001'
            self.event_bus.publish(BusEvent(
                type=EventType.TASK_ASSIGNED,
                data={
                    'task_id': backend_task_id,
                    'agent_name': 'backend_agent',
                    'task_description': 'Create /api/users endpoint returning user data',
                    'priority': 'high'
                }
            ))
            
            # Wait for backend task
            timeout = 10
            start_time = time.time()
            while backend_task_id not in self.completed_tasks and time.time() - start_time < timeout:
                time.sleep(0.1)
                
            # Create frontend task that uses the API
            frontend_task_id = 'frontend_api_001'
            self.event_bus.publish(BusEvent(
                type=EventType.TASK_ASSIGNED,
                data={
                    'task_id': frontend_task_id,
                    'agent_name': 'frontend_agent',
                    'task_description': 'Create component that fetches data from /api/users',
                    'priority': 'high'
                }
            ))
            
            # Wait for frontend task
            start_time = time.time()
            while frontend_task_id not in self.completed_tasks and time.time() - start_time < timeout:
                time.sleep(0.1)
                
            # Both tasks should complete successfully
            self.assertIn(backend_task_id, self.completed_tasks)
            self.assertIn(frontend_task_id, self.completed_tasks)
            self.assertTrue(self.completed_tasks[backend_task_id].get('success', False))
            self.assertTrue(self.completed_tasks[frontend_task_id].get('success', False))
            
        finally:
            frontend_agent.stop()
            backend_agent.stop()


if __name__ == '__main__':
    main()