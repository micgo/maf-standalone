#!/usr/bin/env python3
"""
Tests for EventDrivenBaseAgent class
"""
import os
import time
import json
from unittest import TestCase, mock
from unittest.mock import Mock, patch, MagicMock

from multi_agent_framework.agents.event_driven_base_agent import EventDrivenBaseAgent
from multi_agent_framework.core.event_bus_interface import EventType
from multi_agent_framework.core.project_config import ProjectConfig


class TestEventDrivenAgentImpl(EventDrivenBaseAgent):
    """Test implementation of EventDrivenBaseAgent"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.tasks_processed = []
    
    def _process_task_created(self, event):
        """Process task created event"""
        self.tasks_processed.append(event)
        
        # Simulate task completion
        self.event_bus.publish({
            'type': EventType.TASK_COMPLETED,
            'task_id': event.get('task_id'),
            'agent_id': self.agent_id,
            'result': f"Processed: {event.get('description')}"
        })


class TestEventDrivenBaseAgent(TestCase):
    """Test EventDrivenBaseAgent functionality"""
    
    def setUp(self):
        """Set up test environment"""
        # Create temp directory
        self.temp_dir = '/tmp/test_event_agent'
        os.makedirs(self.temp_dir, exist_ok=True)
        
        # Mock event bus
        self.mock_event_bus = Mock()
        self.mock_event_bus.subscribe = Mock()
        self.mock_event_bus.publish = Mock()
        self.mock_event_bus.start = Mock()
        self.mock_event_bus.stop = Mock()
        
        # Mock event bus factory
        self.event_bus_patcher = patch('multi_agent_framework.core.event_bus_factory.get_event_bus')
        self.mock_get_event_bus = self.event_bus_patcher.start()
        self.mock_get_event_bus.return_value = self.mock_event_bus
        
        # Mock LLM
        self.llm_patcher = patch('google.generativeai.GenerativeModel')
        self.mock_llm_class = self.llm_patcher.start()
        self.mock_llm = Mock()
        self.mock_llm_class.return_value = self.mock_llm
        self.mock_llm.generate_content.return_value.text = '{"result": "test"}'
        
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
    
    def test_agent_initialization(self):
        """Test event-driven agent initialization"""
        agent = TestEventDrivenAgentImpl(
            name="test_event_agent",
            project_root=self.temp_dir
        )
        
        self.assertEqual(agent.name, "test_event_agent")
        self.assertEqual(agent.project_root, self.temp_dir)
        self.assertIsNotNone(agent.agent_id)
        self.assertEqual(agent.event_bus, self.mock_event_bus)
        
        # Check event subscriptions
        expected_subscriptions = [
            EventType.TASK_CREATED,
            EventType.TASK_UPDATED,
            EventType.TASK_CANCELLED,
            EventType.AGENT_MESSAGE
        ]
        
        # Verify subscribe was called for each event type
        self.assertEqual(self.mock_event_bus.subscribe.call_count, len(expected_subscriptions))
    
    def test_handle_task_created_event(self):
        """Test handling TASK_CREATED events"""
        agent = TestEventDrivenAgentImpl("test_agent", self.temp_dir)
        
        # Create task event
        task_event = {
            'type': EventType.TASK_CREATED,
            'task_id': 'task-123',
            'assigned_agent': 'test_agent',
            'description': 'Test task',
            'feature_id': 'feature-456'
        }
        
        # Simulate event
        agent._handle_task_created(task_event)
        
        # Check task was processed
        self.assertEqual(len(agent.tasks_processed), 1)
        self.assertEqual(agent.tasks_processed[0]['task_id'], 'task-123')
        
        # Check completion event was published
        self.mock_event_bus.publish.assert_called()
        published_event = self.mock_event_bus.publish.call_args[0][0]
        self.assertEqual(published_event['type'], EventType.TASK_COMPLETED)
        self.assertEqual(published_event['task_id'], 'task-123')
    
    def test_handle_task_for_different_agent(self):
        """Test ignoring tasks for other agents"""
        agent = TestEventDrivenAgentImpl("test_agent", self.temp_dir)
        
        # Task for different agent
        task_event = {
            'type': EventType.TASK_CREATED,
            'task_id': 'task-789',
            'assigned_agent': 'other_agent',
            'description': 'Not for me'
        }
        
        agent._handle_task_created(task_event)
        
        # Should not process
        self.assertEqual(len(agent.tasks_processed), 0)
    
    def test_handle_agent_message(self):
        """Test handling direct agent messages"""
        agent = TestEventDrivenAgentImpl("test_agent", self.temp_dir)
        
        # Mock the handler
        with patch.object(agent, '_handle_agent_message') as mock_handler:
            message_event = {
                'type': EventType.AGENT_MESSAGE,
                'recipient': 'test_agent',
                'sender': 'orchestrator',
                'content': 'Status check'
            }
            
            # Get the handler that was registered
            handler = self.mock_event_bus.subscribe.call_args_list[3][0][1]
            handler(message_event)
            
            mock_handler.assert_called_once_with(message_event)
    
    def test_process_inbox_messages_on_start(self):
        """Test processing existing inbox messages on startup"""
        # Set up inbox messages
        inbox_messages = [
            {
                'type': 'task',
                'task_id': 'inbox-task-1',
                'description': 'Pending task 1'
            },
            {
                'type': 'task', 
                'task_id': 'inbox-task-2',
                'description': 'Pending task 2'
            }
        ]
        
        self.mock_message_bus.receive_messages.return_value = inbox_messages
        
        agent = TestEventDrivenAgentImpl("test_agent", self.temp_dir)
        
        # Start agent (which processes inbox)
        with patch.object(agent, '_run_event_loop'):
            agent.start()
        
        # Check events were published for inbox messages
        self.assertEqual(self.mock_event_bus.publish.call_count, 2)
        
        # Verify correct events published
        published_events = [call[0][0] for call in self.mock_event_bus.publish.call_args_list]
        self.assertEqual(published_events[0]['type'], EventType.TASK_CREATED)
        self.assertEqual(published_events[0]['task_id'], 'inbox-task-1')
        self.assertEqual(published_events[1]['task_id'], 'inbox-task-2')
    
    def test_run_event_loop(self):
        """Test the event loop"""
        agent = TestEventDrivenAgentImpl("test_agent", self.temp_dir)
        
        # Set up to stop after short time
        def stop_after_delay():
            time.sleep(0.1)
            agent.stop()
        
        import threading
        stop_thread = threading.Thread(target=stop_after_delay)
        stop_thread.start()
        
        # Run event loop
        agent._run_event_loop()
        
        stop_thread.join()
        self.assertFalse(agent._running)
    
    def test_health_check_event(self):
        """Test health check response"""
        agent = TestEventDrivenAgentImpl("test_agent", self.temp_dir)
        
        # Simulate health check
        with patch.object(agent, '_send_heartbeat') as mock_heartbeat:
            agent._perform_health_check()
            
            mock_heartbeat.assert_called_once()
            
            # Check heartbeat event
            self.mock_event_bus.publish.assert_called()
            heartbeat = self.mock_event_bus.publish.call_args[0][0]
            self.assertEqual(heartbeat['type'], EventType.HEALTH_CHECK)
            self.assertEqual(heartbeat['agent_id'], agent.agent_id)
            self.assertEqual(heartbeat['status'], 'healthy')
    
    def test_shutdown_sequence(self):
        """Test proper shutdown"""
        agent = TestEventDrivenAgentImpl("test_agent", self.temp_dir)
        
        # Start agent
        agent._running = True
        
        # Mock current task
        agent._current_task = {'task_id': 'active-task'}
        
        # Shutdown
        agent.shutdown()
        
        # Check shutdown event published
        self.mock_event_bus.publish.assert_called()
        shutdown_events = [
            call[0][0] for call in self.mock_event_bus.publish.call_args_list
            if call[0][0].get('type') == EventType.AGENT_STOPPED
        ]
        self.assertEqual(len(shutdown_events), 1)
        self.assertEqual(shutdown_events[0]['agent_id'], agent.agent_id)
        
        # Check event bus stopped
        self.mock_event_bus.stop.assert_called_once()
        
        # Check running flag
        self.assertFalse(agent._running)
    
    def test_task_progress_updates(self):
        """Test sending task progress updates"""
        agent = TestEventDrivenAgentImpl("test_agent", self.temp_dir)
        
        # Update task progress
        agent._update_task_progress('task-999', 50, 'Half way done')
        
        # Check progress event
        self.mock_event_bus.publish.assert_called()
        progress_event = self.mock_event_bus.publish.call_args[0][0]
        self.assertEqual(progress_event['type'], EventType.TASK_PROGRESS)
        self.assertEqual(progress_event['task_id'], 'task-999')
        self.assertEqual(progress_event['progress'], 50)
        self.assertEqual(progress_event['message'], 'Half way done')
    
    def test_error_handling_in_event_handler(self):
        """Test error handling when processing events"""
        agent = TestEventDrivenAgentImpl("test_agent", self.temp_dir)
        
        # Make process method raise exception
        with patch.object(agent, '_process_task_created', side_effect=Exception("Test error")):
            task_event = {
                'type': EventType.TASK_CREATED,
                'task_id': 'error-task',
                'assigned_agent': 'test_agent',
                'description': 'This will fail'
            }
            
            # Should not crash
            agent._handle_task_created(task_event)
            
            # Should publish failure event
            self.mock_event_bus.publish.assert_called()
            failure_event = self.mock_event_bus.publish.call_args[0][0]
            self.assertEqual(failure_event['type'], EventType.TASK_FAILED)
            self.assertEqual(failure_event['task_id'], 'error-task')
            self.assertIn('Test error', failure_event['error'])
    
    def test_concurrent_task_handling(self):
        """Test handling multiple concurrent tasks"""
        agent = TestEventDrivenAgentImpl("test_agent", self.temp_dir)
        
        # Create multiple task events
        tasks = []
        for i in range(5):
            tasks.append({
                'type': EventType.TASK_CREATED,
                'task_id': f'concurrent-{i}',
                'assigned_agent': 'test_agent',
                'description': f'Task {i}'
            })
        
        # Process all tasks
        for task in tasks:
            agent._handle_task_created(task)
        
        # All should be processed
        self.assertEqual(len(agent.tasks_processed), 5)
        
        # All should publish completion
        completion_events = [
            call[0][0] for call in self.mock_event_bus.publish.call_args_list
            if call[0][0].get('type') == EventType.TASK_COMPLETED
        ]
        self.assertEqual(len(completion_events), 5)
    
    def test_model_provider_initialization(self):
        """Test initialization with different model providers"""
        # Test each provider
        providers = ['gemini', 'openai', 'anthropic']
        
        for provider in providers:
            with self.subTest(provider=provider):
                agent = TestEventDrivenAgentImpl(
                    name=f"test_{provider}",
                    project_root=self.temp_dir,
                    model_provider=provider
                )
                
                self.assertEqual(agent.model_provider, provider)
                self.assertIsNotNone(agent.llm)


if __name__ == '__main__':
    import unittest
    unittest.main()