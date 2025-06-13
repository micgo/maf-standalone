#!/usr/bin/env python3
"""
Test suite for event-driven agents
"""
import os
import sys
import time
import json
import tempfile
import shutil
from typing import Dict, Any, List
from unittest import TestCase, main

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from multi_agent_framework.core.event_bus_factory import get_event_bus
from multi_agent_framework.core.event_bus_interface import Event, EventType
from multi_agent_framework.core.project_config import ProjectConfig
from multi_agent_framework.core.agent_factory import create_agent


class EventDrivenAgentTestBase(TestCase):
    """Base class for event-driven agent tests"""
    
    def setUp(self):
        """Set up test environment"""
        # Create temporary directory for test
        self.test_dir = tempfile.mkdtemp()
        self.project_config = ProjectConfig(self.test_dir)
        
        # Create event bus
        self.event_bus = get_event_bus()
        
        # Track events
        self.received_events: List[Event] = []
        self.task_results: Dict[str, Any] = {}
        
        # Subscribe to events
        self.event_bus.subscribe(EventType.TASK_COMPLETED, self._track_completion)
        self.event_bus.subscribe(EventType.TASK_FAILED, self._track_failure)
        
    def tearDown(self):
        """Clean up test environment"""
        # Clean up temporary directory
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    def _track_completion(self, event: Event):
        """Track task completion events"""
        task_id = event.data.get('task_id')
        if task_id:
            self.task_results[task_id] = {
                'success': True,
                'result': event.data.get('result', {}),
                'agent': event.source
            }
        self.received_events.append(event)
    
    def _track_failure(self, event: Event):
        """Track task failure events"""
        task_id = event.data.get('task_id')
        if task_id:
            self.task_results[task_id] = {
                'success': False,
                'error': event.data.get('error', 'Unknown error'),
                'agent': event.source
            }
        self.received_events.append(event)
    
    def send_task_to_agent(self, agent_name: str, task_id: str, description: str, **kwargs):
        """Helper to send a task to an agent"""
        task_data = {
            'task_id': task_id,
            'description': description,
            'assigned_agent': agent_name,
            'feature_id': kwargs.get('feature_id', 'test_feature'),
            **kwargs
        }
        
        event = Event(
            id=f"test-task-{task_id}",
            type=EventType.TASK_ASSIGNED,
            source='test_harness',
            timestamp=time.time(),
            data=task_data
        )
        
        self.event_bus.publish(event)
    
    def wait_for_task(self, task_id: str, timeout: int = 10) -> Dict[str, Any]:
        """Wait for a task to complete and return result"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            if task_id in self.task_results:
                return self.task_results[task_id]
            time.sleep(0.1)
        
        self.fail(f"Task {task_id} did not complete within {timeout} seconds")


class TestDevOpsAgent(EventDrivenAgentTestBase):
    """Test cases for DevOps event-driven agent"""
    
    def test_devops_agent_starts(self):
        """Test that DevOps agent can be created and started"""
        agent = create_agent('devops', mode='event_driven', project_config=self.project_config)
        self.assertIsNotNone(agent)
        
        agent.start()
        self.assertTrue(hasattr(agent, '_running'))
        self.assertTrue(agent._running)
        
        agent.stop()
    
    def test_dockerfile_generation(self):
        """Test that DevOps agent can generate a Dockerfile"""
        # Start the agent
        agent = create_agent('devops', mode='event_driven', project_config=self.project_config)
        agent.start()
        
        try:
            # Send a task
            task_id = 'test_docker_001'
            self.send_task_to_agent(
                'devops_agent',
                task_id,
                'Create a Dockerfile for a Python Flask application'
            )
            
            # Wait for result
            result = self.wait_for_task(task_id)
            
            # Verify result
            self.assertTrue(result['success'], f"Task failed: {result.get('error')}")
            self.assertIn('Dockerfile', result['result'].get('message', ''))
            
            # Check if file was created
            output = result['result'].get('output', '')
            self.assertIn('FROM python', output)
            self.assertIn('EXPOSE', output)
            
        finally:
            agent.stop()
    
    def test_ci_pipeline_generation(self):
        """Test that DevOps agent can generate CI/CD pipeline"""
        agent = create_agent('devops', mode='event_driven', project_config=self.project_config)
        agent.start()
        
        try:
            task_id = 'test_ci_001'
            self.send_task_to_agent(
                'devops_agent',
                task_id,
                'Create a GitHub Actions workflow for running tests and deploying to production'
            )
            
            result = self.wait_for_task(task_id)
            
            self.assertTrue(result['success'])
            output = result['result'].get('output', '')
            self.assertIn('name:', output)  # YAML workflow should have name
            self.assertIn('jobs:', output)  # Should define jobs
            
        finally:
            agent.stop()


class TestSecurityAgent(EventDrivenAgentTestBase):
    """Test cases for Security event-driven agent"""
    
    def test_security_agent_starts(self):
        """Test that Security agent can be created and started"""
        agent = create_agent('security', mode='event_driven', project_config=self.project_config)
        self.assertIsNotNone(agent)
        
        agent.start()
        self.assertTrue(agent._running)
        
        agent.stop()
    
    def test_security_audit(self):
        """Test that Security agent can perform security audit"""
        agent = create_agent('security', mode='event_driven', project_config=self.project_config)
        agent.start()
        
        try:
            task_id = 'test_security_001'
            self.send_task_to_agent(
                'security_agent',
                task_id,
                'Review authentication implementation for security vulnerabilities'
            )
            
            result = self.wait_for_task(task_id)
            
            self.assertTrue(result['success'])
            # Security agent should provide recommendations
            self.assertIsNotNone(result['result'].get('output'))
            
        finally:
            agent.stop()


class TestDocsAgent(EventDrivenAgentTestBase):
    """Test cases for Documentation event-driven agent"""
    
    def test_docs_agent_starts(self):
        """Test that Docs agent can be created and started"""
        agent = create_agent('docs', mode='event_driven', project_config=self.project_config)
        self.assertIsNotNone(agent)
        
        agent.start()
        self.assertTrue(agent._running)
        
        agent.stop()
    
    def test_api_documentation_generation(self):
        """Test that Docs agent can generate API documentation"""
        agent = create_agent('docs', mode='event_driven', project_config=self.project_config)
        agent.start()
        
        try:
            task_id = 'test_docs_001'
            self.send_task_to_agent(
                'docs_agent',
                task_id,
                'Create API documentation for user authentication endpoints'
            )
            
            result = self.wait_for_task(task_id)
            
            self.assertTrue(result['success'])
            output = result['result'].get('output', '')
            # Should contain API documentation elements
            self.assertTrue(
                'endpoint' in output.lower() or 
                'api' in output.lower() or 
                'request' in output.lower()
            )
            
        finally:
            agent.stop()


class TestUXUIAgent(EventDrivenAgentTestBase):
    """Test cases for UX/UI event-driven agent"""
    
    def test_ux_ui_agent_starts(self):
        """Test that UX/UI agent can be created and started"""
        agent = create_agent('ux_ui', mode='event_driven', project_config=self.project_config)
        self.assertIsNotNone(agent)
        
        agent.start()
        self.assertTrue(agent._running)
        
        agent.stop()
    
    def test_design_system_generation(self):
        """Test that UX/UI agent can generate design system components"""
        agent = create_agent('ux_ui', mode='event_driven', project_config=self.project_config)
        agent.start()
        
        try:
            task_id = 'test_ux_001'
            self.send_task_to_agent(
                'ux_ui_agent',
                task_id,
                'Create a design system color palette for a professional web application'
            )
            
            result = self.wait_for_task(task_id, timeout=15)
            
            self.assertTrue(result['success'])
            output = result['result'].get('output', '')
            # Should contain CSS or design tokens
            self.assertTrue(
                'color' in output.lower() or 
                '--' in output or  # CSS variables
                '#' in output      # Hex colors
            )
            
        finally:
            agent.stop()


if __name__ == '__main__':
    main()