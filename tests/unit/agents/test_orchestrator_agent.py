#!/usr/bin/env python3
"""
Tests for OrchestratorAgent and EventDrivenOrchestratorAgent
"""
import os
import json
import uuid
from unittest import TestCase, mock
from unittest.mock import Mock, patch, MagicMock, call

from multi_agent_framework.agents.orchestrator_agent import OrchestratorAgent
from multi_agent_framework.agents.event_driven_orchestrator_agent import EventDrivenOrchestratorAgent
from multi_agent_framework.core.event_bus_interface import EventType


class TestOrchestratorAgent(TestCase):
    """Test OrchestratorAgent (polling mode)"""
    
    def setUp(self):
        """Set up test environment"""
        self.temp_dir = '/tmp/test_orchestrator'
        os.makedirs(self.temp_dir, exist_ok=True)
        
        # Mock LLM
        self.llm_patcher = patch('google.generativeai.GenerativeModel')
        self.mock_llm_class = self.llm_patcher.start()
        self.mock_llm = Mock()
        self.mock_llm_class.return_value = self.mock_llm
        
        # Default task breakdown response
        self.mock_task_breakdown = [
            {
                "agent": "frontend_agent",
                "description": "Create user interface components"
            },
            {
                "agent": "backend_agent",
                "description": "Implement API endpoints"
            },
            {
                "agent": "db_agent",
                "description": "Design database schema"
            }
        ]
        
        self.mock_llm.generate_content.return_value.text = json.dumps(self.mock_task_breakdown)
        
        # Mock message bus
        self.message_bus_patcher = patch('multi_agent_framework.core.message_bus_configurable.MessageBus')
        self.mock_message_bus_class = self.message_bus_patcher.start()
        self.mock_message_bus = Mock()
        self.mock_message_bus_class.return_value = self.mock_message_bus
        self.mock_message_bus.send_message = Mock()
        
    def tearDown(self):
        """Clean up"""
        self.llm_patcher.stop()
        self.message_bus_patcher.stop()
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_orchestrator_initialization(self):
        """Test orchestrator initialization"""
        orchestrator = OrchestratorAgent(project_root=self.temp_dir)
        
        self.assertEqual(orchestrator.name, "orchestrator")
        self.assertEqual(orchestrator.project_root, self.temp_dir)
        self.assertIsNotNone(orchestrator.available_agents)
        self.assertIn("frontend_agent", orchestrator.available_agents)
        self.assertIn("backend_agent", orchestrator.available_agents)
    
    def test_process_new_feature_task(self):
        """Test processing new feature request"""
        orchestrator = OrchestratorAgent(project_root=self.temp_dir)
        
        task = {
            "type": "new_feature",
            "content": "Create user authentication system",
            "sender": "cli"
        }
        
        result = orchestrator.process_task(task)
        
        # Check feature was created
        self.assertIn("feature_id", result)
        self.assertEqual(result["status"], "tasks_assigned")
        
        # Check messages were sent to agents
        self.assertGreater(self.mock_message_bus.send_message.call_count, 0)
        
        # Verify task assignment messages
        sent_messages = [
            call[0][1] for call in self.mock_message_bus.send_message.call_args_list
        ]
        
        # Should have sent task to each agent
        self.assertEqual(len(sent_messages), len(self.mock_task_breakdown))
        
        for i, message in enumerate(sent_messages):
            self.assertEqual(message['type'], 'task')
            self.assertIn('task_id', message)
            self.assertEqual(message['description'], self.mock_task_breakdown[i]['description'])
    
    def test_task_breakdown_with_prompt(self):
        """Test LLM prompt for task breakdown"""
        orchestrator = OrchestratorAgent(project_root=self.temp_dir)
        
        feature_description = "Add shopping cart functionality"
        
        # Mock UUID to have predictable IDs
        with patch('uuid.uuid4', return_value='test-feature-id'):
            orchestrator._break_down_feature('test-feature-id', feature_description)
        
        # Check LLM was called with proper prompt
        self.mock_llm.generate_content.assert_called_once()
        prompt = self.mock_llm.generate_content.call_args[0][0]
        
        # Verify prompt contains key elements
        self.assertIn("shopping cart functionality", prompt)
        self.assertIn("JSON", prompt)
        self.assertIn("agent", prompt)
        self.assertIn("description", prompt)
    
    def test_handle_task_result(self):
        """Test handling task results from agents"""
        orchestrator = OrchestratorAgent(project_root=self.temp_dir)
        
        # Set up a feature with tasks
        feature_id = str(uuid.uuid4())
        task_id = str(uuid.uuid4())
        
        orchestrator._features[feature_id] = {
            'id': feature_id,
            'description': 'Test feature',
            'status': 'in_progress',
            'tasks': [task_id]
        }
        
        orchestrator._tasks[task_id] = {
            'id': task_id,
            'feature_id': feature_id,
            'agent': 'frontend_agent',
            'status': 'assigned',
            'description': 'Create UI'
        }
        
        # Process task result
        task_result = {
            'type': 'task_result',
            'task_id': task_id,
            'status': 'completed',
            'result': 'UI components created',
            'sender': 'frontend_agent'
        }
        
        result = orchestrator.process_task(task_result)
        
        # Check task was updated
        self.assertEqual(orchestrator._tasks[task_id]['status'], 'completed')
        self.assertEqual(orchestrator._tasks[task_id]['result'], 'UI components created')
        
        # Check feature status
        self.assertEqual(orchestrator._features[feature_id]['status'], 'completed')
    
    def test_agent_normalization(self):
        """Test agent name normalization"""
        orchestrator = OrchestratorAgent(project_root=self.temp_dir)
        
        # Test various formats
        self.assertEqual(orchestrator._normalize_agent_name("frontend"), "frontend_agent")
        self.assertEqual(orchestrator._normalize_agent_name("frontend_agent"), "frontend_agent")
        self.assertEqual(orchestrator._normalize_agent_name("BACKEND"), "backend_agent")
        self.assertEqual(orchestrator._normalize_agent_name("Frontend Agent"), "frontend_agent")
        self.assertEqual(orchestrator._normalize_agent_name("qa"), "qa_agent")
    
    def test_invalid_task_response_handling(self):
        """Test handling invalid JSON from LLM"""
        orchestrator = OrchestratorAgent(project_root=self.temp_dir)
        
        # Set invalid response
        self.mock_llm.generate_content.return_value.text = "Not valid JSON"
        
        feature_id = str(uuid.uuid4())
        orchestrator._features[feature_id] = {
            'id': feature_id,
            'description': 'Test feature',
            'status': 'pending'
        }
        
        # Should handle gracefully
        orchestrator._break_down_feature(feature_id, "Test feature")
        
        # Feature should be marked as failed
        self.assertEqual(orchestrator._features[feature_id]['status'], 'failed')


class TestEventDrivenOrchestratorAgent(TestCase):
    """Test EventDrivenOrchestratorAgent"""
    
    def setUp(self):
        """Set up test environment"""
        self.temp_dir = '/tmp/test_event_orchestrator'
        os.makedirs(self.temp_dir, exist_ok=True)
        
        # Mock event bus
        self.mock_event_bus = Mock()
        self.published_events = []
        
        def capture_publish(event):
            self.published_events.append(event)
        
        self.mock_event_bus.publish.side_effect = capture_publish
        self.mock_event_bus.subscribe = Mock()
        
        # Mock event bus factory
        self.event_bus_patcher = patch('multi_agent_framework.core.event_bus_factory.get_event_bus')
        self.mock_get_event_bus = self.event_bus_patcher.start()
        self.mock_get_event_bus.return_value = self.mock_event_bus
        
        # Mock LLM
        self.llm_patcher = patch('google.generativeai.GenerativeModel')
        self.mock_llm_class = self.llm_patcher.start()
        self.mock_llm = Mock()
        self.mock_llm_class.return_value = self.mock_llm
        
        # Default task breakdown
        self.mock_task_breakdown = [
            {"agent": "frontend_agent", "description": "Build UI"},
            {"agent": "backend_agent", "description": "Create API"}
        ]
        self.mock_llm.generate_content.return_value.text = json.dumps(self.mock_task_breakdown)
        
        # Mock message bus
        self.message_bus_patcher = patch('multi_agent_framework.core.message_bus_configurable.MessageBus')
        self.mock_message_bus_class = self.message_bus_patcher.start()
        self.mock_message_bus = Mock()
        self.mock_message_bus_class.return_value = self.mock_message_bus
        
    def tearDown(self):
        """Clean up"""
        self.event_bus_patcher.stop()
        self.llm_patcher.stop()
        self.message_bus_patcher.stop()
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_event_driven_initialization(self):
        """Test event-driven orchestrator initialization"""
        orchestrator = EventDrivenOrchestratorAgent(project_root=self.temp_dir)
        
        # Check event subscriptions
        expected_events = [
            EventType.FEATURE_REQUESTED,
            EventType.TASK_COMPLETED,
            EventType.TASK_FAILED,
            EventType.TASK_PROGRESS
        ]
        
        # Count TASK_CREATED subscriptions (base class)
        task_created_subs = sum(
            1 for call in self.mock_event_bus.subscribe.call_args_list
            if call[0][0] == EventType.TASK_CREATED
        )
        
        # Should have subscribed to orchestrator-specific events
        self.assertGreaterEqual(self.mock_event_bus.subscribe.call_count, len(expected_events))
    
    def test_handle_feature_requested_event(self):
        """Test handling feature request via event"""
        orchestrator = EventDrivenOrchestratorAgent(project_root=self.temp_dir)
        
        # Create feature request event
        feature_event = {
            'type': EventType.FEATURE_REQUESTED,
            'feature_id': 'feat-123',
            'description': 'Build dashboard',
            'requested_by': 'user'
        }
        
        # Get the handler
        handler = None
        for call in self.mock_event_bus.subscribe.call_args_list:
            if call[0][0] == EventType.FEATURE_REQUESTED:
                handler = call[0][1]
                break
        
        self.assertIsNotNone(handler)
        handler(feature_event)
        
        # Check feature was created
        self.assertIn('feat-123', orchestrator._features)
        
        # Check TASK_CREATED events were published
        task_events = [e for e in self.published_events if e['type'] == EventType.TASK_CREATED]
        self.assertEqual(len(task_events), len(self.mock_task_breakdown))
        
        # Verify task details
        for i, event in enumerate(task_events):
            self.assertEqual(event['feature_id'], 'feat-123')
            self.assertEqual(event['assigned_agent'], self.mock_task_breakdown[i]['agent'])
            self.assertEqual(event['description'], self.mock_task_breakdown[i]['description'])
    
    def test_handle_task_completed_event(self):
        """Test handling task completion events"""
        orchestrator = EventDrivenOrchestratorAgent(project_root=self.temp_dir)
        
        # Set up feature and task
        feature_id = 'feat-456'
        task_id = 'task-789'
        
        orchestrator._features[feature_id] = {
            'id': feature_id,
            'status': 'in_progress',
            'tasks': [task_id]
        }
        
        orchestrator._tasks[task_id] = {
            'id': task_id,
            'feature_id': feature_id,
            'status': 'in_progress'
        }
        
        # Create completion event
        completion_event = {
            'type': EventType.TASK_COMPLETED,
            'task_id': task_id,
            'agent_id': 'frontend_agent',
            'result': 'UI completed'
        }
        
        # Get handler
        handler = None
        for call in self.mock_event_bus.subscribe.call_args_list:
            if call[0][0] == EventType.TASK_COMPLETED:
                handler = call[0][1]
                break
        
        handler(completion_event)
        
        # Check task updated
        self.assertEqual(orchestrator._tasks[task_id]['status'], 'completed')
        
        # Check feature completed event
        feature_events = [
            e for e in self.published_events 
            if e.get('type') == EventType.FEATURE_COMPLETED
        ]
        self.assertEqual(len(feature_events), 1)
        self.assertEqual(feature_events[0]['feature_id'], feature_id)
    
    def test_cross_agent_coordination(self):
        """Test coordinating dependent tasks between agents"""
        orchestrator = EventDrivenOrchestratorAgent(project_root=self.temp_dir)
        
        # Mock LLM to return dependent tasks
        dependent_tasks = [
            {"agent": "db_agent", "description": "Create user table"},
            {"agent": "backend_agent", "description": "Implement user API", "depends_on": ["db_agent"]},
            {"agent": "frontend_agent", "description": "Build user UI", "depends_on": ["backend_agent"]}
        ]
        self.mock_llm.generate_content.return_value.text = json.dumps(dependent_tasks)
        
        # Request feature
        orchestrator._break_down_feature('feat-999', 'User management system')
        
        # Only first task should be created immediately
        immediate_tasks = [
            e for e in self.published_events 
            if e['type'] == EventType.TASK_CREATED
        ]
        self.assertEqual(len(immediate_tasks), 1)
        self.assertEqual(immediate_tasks[0]['assigned_agent'], 'db_agent')
    
    def test_progress_tracking(self):
        """Test tracking task progress updates"""
        orchestrator = EventDrivenOrchestratorAgent(project_root=self.temp_dir)
        
        # Set up task
        task_id = 'task-progress-1'
        orchestrator._tasks[task_id] = {
            'id': task_id,
            'status': 'in_progress',
            'progress': 0
        }
        
        # Progress event
        progress_event = {
            'type': EventType.TASK_PROGRESS,
            'task_id': task_id,
            'progress': 75,
            'message': 'Almost done'
        }
        
        # Get handler
        handler = None
        for call in self.mock_event_bus.subscribe.call_args_list:
            if call[0][0] == EventType.TASK_PROGRESS:
                handler = call[0][1]
                break
        
        handler(progress_event)
        
        # Check progress updated
        self.assertEqual(orchestrator._tasks[task_id]['progress'], 75)
    
    def test_error_recovery(self):
        """Test handling task failures and retries"""
        orchestrator = EventDrivenOrchestratorAgent(project_root=self.temp_dir)
        
        # Set up failed task
        task_id = 'task-fail-1'
        orchestrator._tasks[task_id] = {
            'id': task_id,
            'feature_id': 'feat-fail',
            'assigned_agent': 'backend_agent',
            'status': 'in_progress',
            'retry_count': 0,
            'description': 'Failing task'
        }
        
        # Failure event
        failure_event = {
            'type': EventType.TASK_FAILED,
            'task_id': task_id,
            'error': 'Connection timeout',
            'agent_id': 'backend_agent'
        }
        
        # Get handler
        handler = None
        for call in self.mock_event_bus.subscribe.call_args_list:
            if call[0][0] == EventType.TASK_FAILED:
                handler = call[0][1]
                break
        
        handler(failure_event)
        
        # Should retry task
        retry_events = [
            e for e in self.published_events
            if e['type'] == EventType.TASK_CREATED and e.get('retry', False)
        ]
        self.assertEqual(len(retry_events), 1)
        self.assertEqual(retry_events[0]['task_id'], task_id)
        self.assertEqual(orchestrator._tasks[task_id]['retry_count'], 1)


if __name__ == '__main__':
    import unittest
    unittest.main()