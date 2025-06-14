#!/usr/bin/env python3
"""
Tests for agent-to-agent communication and message flows
"""
import os
import sys
import time
import json
import tempfile
import shutil
from typing import Dict, Any, List, Optional
from unittest import TestCase, main
from unittest.mock import Mock, patch

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from multi_agent_framework.core.event_bus_factory import get_event_bus, reset_event_bus
from multi_agent_framework.core.event_bus_interface import Event, EventType
from multi_agent_framework.core.project_config import ProjectConfig
from multi_agent_framework.core.agent_factory import create_agent
from multi_agent_framework.core.message_bus_configurable import MessageBus
from ..helpers.mock_agents import create_mock_agent


class AgentCommunicationTest(TestCase):
    """Test agent-to-agent communication patterns"""
    
    def _create_event(self, event_type: EventType, data: Dict[str, Any], source: str = 'test') -> Event:
        """Helper to create events with required fields"""
        return Event(
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
        
        # Initialize components
        self.event_bus = get_event_bus({'type': 'inmemory'})
        self.message_bus = MessageBus(self.test_dir)
        
        # Track communications
        self.agent_messages = {}
        self.task_handoffs = []
        
    def tearDown(self):
        """Clean up test environment"""
        # Stop event bus
        self.event_bus.stop()
        
        # Reset global event bus
        reset_event_bus()
        
        # Clean up temp directory
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
            
    def test_orchestrator_task_distribution(self):
        """Test orchestrator distributing tasks to specialized agents"""
        # Create orchestrator and specialized agents
        orchestrator = create_mock_agent('orchestrator', project_config=self.project_config)
        frontend = create_mock_agent('frontend', project_config=self.project_config)
        backend = create_mock_agent('backend', project_config=self.project_config)
        
        # Track task assignments
        assignments = []
        
        def track_assignment(event: Event):
            if event.type == EventType.TASK_ASSIGNED:
                assignments.append(event.data)
                
        self.event_bus.subscribe(EventType.TASK_ASSIGNED, track_assignment)
        
        # Start agents
        orchestrator.start()
        frontend.start()
        backend.start()
        
        try:
            # Create a high-level feature
            main_feature = {
                'feature_id': 'main_001',
                'description': 'Build a user authentication system with login page and API',
                'priority': 'high'
            }
            
            # Send to orchestrator
            self.event_bus.publish(self._create_event(
                EventType.FEATURE_CREATED,
                main_feature
            ))
            
            # Wait for orchestrator to break down and assign tasks
            timeout = 10
            start_time = time.time()
            while len(assignments) < 2 and time.time() - start_time < timeout:
                time.sleep(0.1)
                
            # Should have created subtasks for frontend and backend
            self.assertGreaterEqual(len(assignments), 2)
            
            # Check assignments
            agent_names = {a['assigned_agent'] for a in assignments}
            self.assertIn('frontend_agent', agent_names)
            self.assertIn('backend_agent', agent_names)
            
        finally:
            orchestrator.stop()
            frontend.stop()
            backend.stop()
            
    def test_agent_result_sharing(self):
        """Test agents sharing results with each other"""
        # Create backend and frontend agents
        backend = create_mock_agent('backend', project_config=self.project_config)
        frontend = create_mock_agent('frontend', project_config=self.project_config)
        
        # Track completed tasks
        completed_tasks = {}
        
        def track_completion(event: Event):
            if event.type == EventType.TASK_COMPLETED:
                task_id = event.data.get('task_id')
                if task_id:
                    completed_tasks[task_id] = event.data
                
        self.event_bus.subscribe(EventType.TASK_COMPLETED, track_completion)
        
        backend.start()
        frontend.start()
        
        try:
            # Backend creates an API
            backend_task_id = 'api_001'
            self.event_bus.publish(self._create_event(
                EventType.TASK_ASSIGNED,
                {
                    'task_id': backend_task_id,
                    'assigned_agent': 'backend_agent',
                    'task_description': 'Create REST API endpoint /api/products',
                    'priority': 'high'
                }
            ))
            
            # Wait for backend to complete
            timeout = 10
            start_time = time.time()
            while backend_task_id not in completed_tasks and time.time() - start_time < timeout:
                time.sleep(0.1)
                
            # Frontend creates UI that uses the API
            frontend_task_id = 'ui_001'
            self.event_bus.publish(self._create_event(
                EventType.TASK_ASSIGNED,
                {
                    'task_id': frontend_task_id,
                    'assigned_agent': 'frontend_agent',
                    'task_description': 'Create product list component using /api/products',
                    'priority': 'high',
                    'dependencies': [backend_task_id]
                }
            ))
            
            # Wait for frontend to complete
            start_time = time.time()
            while frontend_task_id not in completed_tasks and time.time() - start_time < timeout:
                time.sleep(0.1)
                
            # Both tasks should complete
            self.assertIn(backend_task_id, completed_tasks)
            self.assertIn(frontend_task_id, completed_tasks)
            
            # Frontend should reference the API
            frontend_result = completed_tasks[frontend_task_id]
            self.assertTrue(frontend_result.get('success', False))
            
        finally:
            backend.stop()
            frontend.stop()
            
    def test_qa_agent_validation_flow(self):
        """Test QA agent validating other agents' work"""
        # Create agents
        backend = create_mock_agent('backend', project_config=self.project_config)
        qa = create_mock_agent('qa', project_config=self.project_config)
        
        # Track events
        completed_tasks = {}
        validation_requests = []
        
        def track_events(event: Event):
            if event.type == EventType.TASK_COMPLETED:
                completed_tasks[event.data['task_id']] = event.data
            elif event.type == EventType.TASK_CREATED and 'validate' in event.data.get('description', '').lower():
                validation_requests.append(event.data)
                
        self.event_bus.subscribe(EventType.TASK_COMPLETED, track_events)
        self.event_bus.subscribe(EventType.TASK_CREATED, track_events)
        
        backend.start()
        qa.start()
        
        try:
            # Backend creates code
            backend_task_id = 'backend_func_001'
            self.event_bus.publish(self._create_event(
                EventType.TASK_ASSIGNED,
                {
                    'task_id': backend_task_id,
                    'assigned_agent': 'backend_agent',
                    'task_description': 'Create user authentication service',
                    'priority': 'high'
                }
            ))
            
            # Wait for backend to complete
            timeout = 10
            start_time = time.time()
            while backend_task_id not in completed_tasks and time.time() - start_time < timeout:
                time.sleep(0.1)
                
            # QA validates the backend work
            qa_task_id = 'qa_validate_001'
            self.event_bus.publish(self._create_event(
                EventType.TASK_ASSIGNED,
                {
                    'task_id': qa_task_id,
                    'assigned_agent': 'qa_agent',
                    'task_description': f'Validate and test the user authentication service from task {backend_task_id}',
                    'priority': 'high',
                    'target_task': backend_task_id
                }
            ))
            
            # Wait for QA to complete
            start_time = time.time()
            while qa_task_id not in completed_tasks and time.time() - start_time < timeout:
                time.sleep(0.1)
                
            # Both tasks should complete
            self.assertIn(backend_task_id, completed_tasks)
            self.assertIn(qa_task_id, completed_tasks)
            
            # QA task should reference the backend task
            qa_result = completed_tasks[qa_task_id]
            self.assertTrue(qa_result.get('success', False))
            
        finally:
            backend.stop()
            qa.stop()
            
    def test_security_agent_review_flow(self):
        """Test security agent reviewing code from other agents"""
        # Create agents
        backend = create_mock_agent('backend', project_config=self.project_config)
        security = create_mock_agent('security', project_config=self.project_config)
        
        # Track events
        completed_tasks = {}
        security_alerts = []
        
        def track_events(event: Event):
            if event.type == EventType.TASK_COMPLETED:
                completed_tasks[event.data['task_id']] = event.data
                # Check if security found issues
                if event.data.get('agent_name') == 'security_agent':
                    result = event.data.get('result', {})
                    if 'vulnerabilities' in str(result).lower() or 'security' in str(result).lower():
                        security_alerts.append(event.data)
                        
        self.event_bus.subscribe(EventType.TASK_COMPLETED, track_events)
        
        backend.start()
        security.start()
        
        try:
            # Backend creates potentially insecure code
            backend_task_id = 'backend_auth_001'
            self.event_bus.publish(self._create_event(
                EventType.TASK_ASSIGNED,
                {
                    'task_id': backend_task_id,
                    'assigned_agent': 'backend_agent',
                    'task_description': 'Create user login endpoint with password handling',
                    'priority': 'high'
                }
            ))
            
            # Wait for backend
            timeout = 10
            start_time = time.time()
            while backend_task_id not in completed_tasks and time.time() - start_time < timeout:
                time.sleep(0.1)
                
            # Security reviews the code
            security_task_id = 'security_review_001'
            self.event_bus.publish(self._create_event(
                EventType.TASK_ASSIGNED,
                {
                    'task_id': security_task_id,
                    'assigned_agent': 'security_agent',
                    'task_description': f'Review security of login endpoint from task {backend_task_id}',
                    'priority': 'high',
                    'target_task': backend_task_id
                }
            ))
            
            # Wait for security review
            start_time = time.time()
            while security_task_id not in completed_tasks and time.time() - start_time < timeout:
                time.sleep(0.1)
                
            # Both tasks should complete
            self.assertIn(backend_task_id, completed_tasks)
            self.assertIn(security_task_id, completed_tasks)
            
            # Security should have completed the review
            security_result = completed_tasks[security_task_id]
            self.assertTrue(security_result.get('success', False))
            
        finally:
            backend.stop()
            security.stop()
            
    def test_frontend_backend_integration(self):
        """Test frontend and backend agents coordinating on features"""
        # Create agents
        frontend = create_mock_agent('frontend', project_config=self.project_config)
        backend = create_mock_agent('backend', project_config=self.project_config)
        
        # Track task completions and API definitions
        completed_tasks = {}
        api_definitions = {}
        
        def track_completion(event: Event):
            if event.type == EventType.TASK_COMPLETED:
                task_id = event.data.get('task_id')
                if task_id:
                    completed_tasks[task_id] = event.data
                # Extract API info if present
                result = event.data.get('result', {})
                if isinstance(result, dict) and 'api_endpoint' in result:
                    api_definitions[event.data['task_id']] = result['api_endpoint']
                    
        self.event_bus.subscribe(EventType.TASK_COMPLETED, track_completion)
        
        frontend.start()
        backend.start()
        
        try:
            # Simulate coordinated feature development
            feature = "user profile management"
            
            # Backend creates API first
            backend_task_id = 'backend_profile_001'
            self.event_bus.publish(self._create_event(
                EventType.TASK_ASSIGNED,
                {
                    'task_id': backend_task_id,
                    'assigned_agent': 'backend_agent',
                    'task_description': f'Create REST API for {feature} with CRUD operations',
                    'priority': 'high'
                }
            ))
            
            # Frontend creates UI components
            frontend_task_id = 'frontend_profile_001'
            self.event_bus.publish(self._create_event(
                EventType.TASK_ASSIGNED,
                {
                    'task_id': frontend_task_id,
                    'assigned_agent': 'frontend_agent',
                    'task_description': f'Create React components for {feature}',
                    'priority': 'high'
                }
            ))
            
            # Wait for both to complete
            timeout = 15
            start_time = time.time()
            while len(completed_tasks) < 2 and time.time() - start_time < timeout:
                time.sleep(0.1)
                
            # Both should complete
            self.assertEqual(len(completed_tasks), 2)
            self.assertIn(backend_task_id, completed_tasks)
            self.assertIn(frontend_task_id, completed_tasks)
            
            # Both should succeed
            self.assertTrue(completed_tasks[backend_task_id].get('success', False))
            self.assertTrue(completed_tasks[frontend_task_id].get('success', False))
            
        finally:
            frontend.stop()
            backend.stop()
            
    def test_database_agent_schema_sharing(self):
        """Test database agent sharing schema with other agents"""
        # Create agents
        database = create_mock_agent('database', project_config=self.project_config)
        backend = create_mock_agent('backend', project_config=self.project_config)
        
        # Track completions and schemas
        completed_tasks = {}
        database_schemas = {}
        
        def track_events(event: Event):
            if event.type == EventType.TASK_COMPLETED:
                completed_tasks[event.data['task_id']] = event.data
                # Extract schema info
                if event.data.get('agent_name') == 'database_agent':
                    result = event.data.get('result', {})
                    if isinstance(result, dict) and 'schema' in result:
                        database_schemas[event.data['task_id']] = result['schema']
                        
        self.event_bus.subscribe(EventType.TASK_COMPLETED, track_events)
        
        database.start()
        backend.start()
        
        try:
            # Database creates schema
            db_task_id = 'db_schema_001'
            self.event_bus.publish(self._create_event(
                EventType.TASK_ASSIGNED,
                {
                    'task_id': db_task_id,
                    'assigned_agent': 'database_agent',
                    'task_description': 'Create database schema for e-commerce products',
                    'priority': 'high'
                }
            ))
            
            # Wait for database
            timeout = 10
            start_time = time.time()
            while db_task_id not in completed_tasks and time.time() - start_time < timeout:
                time.sleep(0.1)
                
            # Backend creates models based on schema
            backend_task_id = 'backend_models_001'
            self.event_bus.publish(self._create_event(
                EventType.TASK_ASSIGNED,
                {
                    'task_id': backend_task_id,
                    'assigned_agent': 'backend_agent',
                    'task_description': f'Create data models based on database schema from task {db_task_id}',
                    'priority': 'high',
                    'dependencies': [db_task_id]
                }
            ))
            
            # Wait for backend
            start_time = time.time()
            while backend_task_id not in completed_tasks and time.time() - start_time < timeout:
                time.sleep(0.1)
                
            # Both should complete
            self.assertIn(db_task_id, completed_tasks)
            self.assertIn(backend_task_id, completed_tasks)
            
            # Both should succeed
            self.assertTrue(completed_tasks[db_task_id].get('success', False))
            self.assertTrue(completed_tasks[backend_task_id].get('success', False))
            
        finally:
            database.stop()
            backend.stop()
            
    def test_devops_deployment_coordination(self):
        """Test DevOps agent coordinating deployment after other agents complete"""
        # Create agents
        frontend = create_mock_agent('frontend', project_config=self.project_config)
        backend = create_mock_agent('backend', project_config=self.project_config)
        devops = create_mock_agent('devops', project_config=self.project_config)
        
        # Track completions
        completed_tasks = {}
        deployment_tasks = []
        
        def track_events(event: Event):
            if event.type == EventType.TASK_COMPLETED:
                completed_tasks[event.data['task_id']] = event.data
                if event.source == 'devops_agent':
                    deployment_tasks.append(event.data)
                    
        self.event_bus.subscribe(EventType.TASK_COMPLETED, track_events)
        
        frontend.start()
        backend.start()
        devops.start()
        
        try:
            # Frontend and backend complete features
            frontend_task_id = 'frontend_feature_001'
            backend_task_id = 'backend_feature_001'
            
            self.event_bus.publish(self._create_event(
                EventType.TASK_ASSIGNED,
                {
                    'task_id': frontend_task_id,
                    'assigned_agent': 'frontend_agent',
                    'task_description': 'Complete checkout flow UI',
                    'priority': 'high'
                }
            ))
            
            self.event_bus.publish(self._create_event(
                EventType.TASK_ASSIGNED,
                {
                    'task_id': backend_task_id,
                    'assigned_agent': 'backend_agent',
                    'task_description': 'Complete checkout API endpoints',
                    'priority': 'high'
                }
            ))
            
            # Wait for both to complete
            timeout = 15
            start_time = time.time()
            while len(completed_tasks) < 2 and time.time() - start_time < timeout:
                time.sleep(0.1)
                
            # DevOps prepares deployment
            devops_task_id = 'deploy_001'
            self.event_bus.publish(self._create_event(
                EventType.TASK_ASSIGNED,
                {
                    'task_id': devops_task_id,
                    'assigned_agent': 'devops_agent',
                    'task_description': 'Prepare deployment configuration for checkout feature',
                    'priority': 'high',
                    'dependencies': [frontend_task_id, backend_task_id]
                }
            ))
            
            # Wait for deployment task
            start_time = time.time()
            while devops_task_id not in completed_tasks and time.time() - start_time < timeout:
                time.sleep(0.1)
                
            # All should complete
            self.assertEqual(len(completed_tasks), 3)
            self.assertTrue(all(t.get('success', False) for t in completed_tasks.values()))
            
            # DevOps should have created deployment config
            self.assertEqual(len(deployment_tasks), 1)
            
        finally:
            frontend.stop()
            backend.stop()
            devops.stop()


if __name__ == '__main__':
    main()