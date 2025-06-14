#!/usr/bin/env python3
"""
Simplified tests for event-driven specialized agents
"""
import os
from unittest import TestCase, mock
from unittest.mock import Mock, patch, MagicMock

from multi_agent_framework.agents.event_driven_frontend_agent import EventDrivenFrontendAgent
from multi_agent_framework.agents.event_driven_backend_agent import EventDrivenBackendAgent
from multi_agent_framework.agents.event_driven_db_agent import EventDrivenDatabaseAgent
from multi_agent_framework.agents.event_driven_devops_agent import EventDrivenDevOpsAgent
from multi_agent_framework.agents.event_driven_qa_agent import EventDrivenQAAgent
from multi_agent_framework.agents.event_driven_docs_agent import EventDrivenDocsAgent
from multi_agent_framework.agents.event_driven_security_agent import EventDrivenSecurityAgent
from multi_agent_framework.agents.event_driven_ux_ui_agent import EventDrivenUXUIAgent
from multi_agent_framework.core.event_bus_interface import EventType


class TestEventDrivenAgents(TestCase):
    """Test event-driven specialized agents"""
    
    def setUp(self):
        """Common setup for all tests"""
        # Mock event bus
        self.mock_event_bus = Mock()
        self.mock_event_bus.subscribe = Mock()
        self.mock_event_bus.publish = Mock()
        self.mock_event_bus.start = Mock()
        self.mock_event_bus.stop = Mock()
        
        # Mock factories and dependencies
        self.event_bus_patcher = patch('multi_agent_framework.core.event_bus_factory.get_event_bus')
        self.mock_get_event_bus = self.event_bus_patcher.start()
        self.mock_get_event_bus.return_value = self.mock_event_bus
        
        self.llm_patcher = patch('google.generativeai.GenerativeModel')
        self.mock_llm_class = self.llm_patcher.start()
        self.mock_llm = Mock()
        self.mock_llm_class.return_value = self.mock_llm
        self.mock_llm.generate_content.return_value.text = '{"result": "test"}'
        
        self.message_bus_patcher = patch('multi_agent_framework.core.message_bus_configurable.MessageBus')
        self.mock_message_bus_class = self.message_bus_patcher.start()
        self.mock_message_bus = Mock()
        self.mock_message_bus_class.return_value = self.mock_message_bus
        self.mock_message_bus.receive_messages.return_value = []
    
    def tearDown(self):
        """Clean up patches"""
        self.event_bus_patcher.stop()
        self.llm_patcher.stop()
        self.message_bus_patcher.stop()
    
    def test_frontend_agent_initialization(self):
        """Test EventDrivenFrontendAgent initialization"""
        agent = EventDrivenFrontendAgent()
        
        self.assertEqual(agent.name, "frontend_agent")
        self.assertIsNotNone(agent.agent_id)
        
        # Check event subscriptions
        self.assertGreater(self.mock_event_bus.subscribe.call_count, 0)
        subscribed_events = [call[0][0] for call in self.mock_event_bus.subscribe.call_args_list]
        self.assertIn(EventType.TASK_CREATED, subscribed_events)
    
    def test_backend_agent_initialization(self):
        """Test EventDrivenBackendAgent initialization"""
        agent = EventDrivenBackendAgent()
        
        self.assertEqual(agent.name, "backend_agent")
        self.assertIsNotNone(agent.agent_id)
    
    def test_database_agent_initialization(self):
        """Test EventDrivenDatabaseAgent initialization"""
        agent = EventDrivenDatabaseAgent()
        
        self.assertEqual(agent.name, "db_agent")
        self.assertIsNotNone(agent.agent_id)
    
    def test_devops_agent_initialization(self):
        """Test EventDrivenDevOpsAgent initialization"""
        agent = EventDrivenDevOpsAgent()
        
        self.assertEqual(agent.name, "devops_agent")
        self.assertIsNotNone(agent.agent_id)
    
    def test_qa_agent_initialization(self):
        """Test EventDrivenQAAgent initialization"""
        agent = EventDrivenQAAgent()
        
        self.assertEqual(agent.name, "qa_agent")
        self.assertIsNotNone(agent.agent_id)
    
    def test_docs_agent_initialization(self):
        """Test EventDrivenDocsAgent initialization"""
        agent = EventDrivenDocsAgent()
        
        self.assertEqual(agent.name, "docs_agent")
        self.assertIsNotNone(agent.agent_id)
    
    def test_security_agent_initialization(self):
        """Test EventDrivenSecurityAgent initialization"""
        agent = EventDrivenSecurityAgent()
        
        self.assertEqual(agent.name, "security_agent")
        self.assertIsNotNone(agent.agent_id)
    
    def test_uxui_agent_initialization(self):
        """Test EventDrivenUXUIAgent initialization"""
        agent = EventDrivenUXUIAgent()
        
        self.assertEqual(agent.name, "ux_ui_agent")
        self.assertIsNotNone(agent.agent_id)
    
    def test_event_subscription(self):
        """Test agents subscribe to correct events"""
        agents = [
            EventDrivenFrontendAgent(),
            EventDrivenBackendAgent(),
            EventDrivenDatabaseAgent(),
            EventDrivenQAAgent(),
        ]
        
        for agent in agents:
            # Check that each agent subscribed to events
            self.assertGreater(self.mock_event_bus.subscribe.call_count, 0)
            
            # Verify TASK_CREATED subscription
            task_created_subs = [
                call for call in self.mock_event_bus.subscribe.call_args_list
                if call[0][0] == EventType.TASK_CREATED
            ]
            self.assertGreater(len(task_created_subs), 0)
    
    def test_task_event_handling(self):
        """Test agents handle task events"""
        agent = EventDrivenFrontendAgent()
        
        # Mock LLM response
        self.mock_llm.generate_content.return_value.text = '''
```tsx
export const TestComponent = () => <div>Test</div>;
```
'''
        
        # Create task event
        task_event = {
            'type': EventType.TASK_CREATED,
            'task_id': 'test-123',
            'assigned_agent': 'frontend_agent',
            'description': 'Create test component'
        }
        
        # Get the handler
        handler = None
        for call in self.mock_event_bus.subscribe.call_args_list:
            if call[0][0] == EventType.TASK_CREATED:
                handler = call[0][1]
                break
        
        self.assertIsNotNone(handler)
        
        # Mock file operations
        with patch('builtins.open', mock.mock_open()):
            with patch('os.makedirs'):
                # Call handler
                handler(task_event)
                
                # Check completion event was published
                self.mock_event_bus.publish.assert_called()
                published_events = [call[0][0] for call in self.mock_event_bus.publish.call_args_list]
                completion_events = [e for e in published_events if e.get('type') == EventType.TASK_COMPLETED]
                self.assertGreater(len(completion_events), 0)
    
    def test_agent_lifecycle(self):
        """Test agent start and stop"""
        agent = EventDrivenFrontendAgent()
        
        # Test start
        with patch.object(agent, '_run_event_loop'):
            agent.start()
            self.mock_event_bus.start.assert_called_once()
        
        # Test stop
        agent.stop()
        self.assertFalse(agent._running)
        
        # Test shutdown
        agent.shutdown()
        self.mock_event_bus.stop.assert_called_once()
    
    def test_health_check(self):
        """Test agent health check"""
        agent = EventDrivenBackendAgent()
        
        # Perform health check
        agent._perform_health_check()
        
        # Check heartbeat event published
        self.mock_event_bus.publish.assert_called()
        heartbeat_events = [
            call[0][0] for call in self.mock_event_bus.publish.call_args_list
            if call[0][0].get('type') == EventType.HEALTH_CHECK
        ]
        self.assertGreater(len(heartbeat_events), 0)
        self.assertEqual(heartbeat_events[0]['agent_id'], agent.agent_id)
    
    def test_error_handling(self):
        """Test error handling in event processing"""
        agent = EventDrivenDatabaseAgent()
        
        # Create task event
        task_event = {
            'type': EventType.TASK_CREATED,
            'task_id': 'error-test',
            'assigned_agent': 'db_agent',
            'description': 'This will fail'
        }
        
        # Make LLM raise error
        self.mock_llm.generate_content.side_effect = Exception("Test error")
        
        # Get handler
        handler = None
        for call in self.mock_event_bus.subscribe.call_args_list:
            if call[0][0] == EventType.TASK_CREATED:
                handler = call[0][1]
                break
        
        # Call handler - should not crash
        handler(task_event)
        
        # Check failure event published
        failure_events = [
            call[0][0] for call in self.mock_event_bus.publish.call_args_list
            if call[0][0].get('type') == EventType.TASK_FAILED
        ]
        self.assertGreater(len(failure_events), 0)
        self.assertIn('Test error', failure_events[0]['error'])
    
    def test_multiple_agents_different_tasks(self):
        """Test multiple agents handling different task types"""
        frontend = EventDrivenFrontendAgent()
        backend = EventDrivenBackendAgent()
        database = EventDrivenDatabaseAgent()
        
        # Each agent should have subscribed to events
        total_subscriptions = self.mock_event_bus.subscribe.call_count
        self.assertGreaterEqual(total_subscriptions, 3)  # At least one subscription per agent
        
        # Verify each agent has unique ID
        agent_ids = [frontend.agent_id, backend.agent_id, database.agent_id]
        self.assertEqual(len(agent_ids), len(set(agent_ids)))  # All unique


if __name__ == '__main__':
    import unittest
    unittest.main()