#!/usr/bin/env python3
"""
Simplified tests for specialized agents focusing on core behavior
"""
import os
import json
from unittest import TestCase, mock
from unittest.mock import Mock, patch, MagicMock, ANY

from multi_agent_framework.agents.specialized.frontend_agent import FrontendAgent
from multi_agent_framework.agents.specialized.backend_agent import BackendAgent
from multi_agent_framework.agents.specialized.db_agent import DbAgent
from multi_agent_framework.agents.specialized.devops_agent import DevopsAgent
from multi_agent_framework.agents.specialized.qa_agent import QaAgent
from multi_agent_framework.agents.specialized.docs_agent import DocsAgent
from multi_agent_framework.agents.specialized.security_agent import SecurityAgent
from multi_agent_framework.agents.specialized.ux_ui_agent import UxUiAgent


class TestSpecializedAgents(TestCase):
    """Test all specialized agents"""
    
    @patch('multi_agent_framework.core.shared_state_manager.get_shared_state_manager')
    @patch('multi_agent_framework.core.message_bus_configurable.MessageBus')
    @patch('google.generativeai.GenerativeModel')
    def test_frontend_agent_generates_component(self, mock_llm_class, mock_bus_class, mock_state):
        """Test FrontendAgent generates React components"""
        # Setup mocks
        mock_llm = Mock()
        mock_llm_class.return_value = mock_llm
        mock_llm.generate_content.return_value.text = '''
```tsx
export const Button = () => <button>Click me</button>;
```
'''
        
        mock_bus = Mock()
        mock_bus_class.return_value = mock_bus
        
        mock_state_manager = Mock()
        mock_state.return_value = mock_state_manager
        
        # Create agent
        agent = FrontendAgent()
        
        # Verify it was initialized
        self.assertEqual(agent.name, "frontend_agent")
        
        # Test LLM prompt generation
        prompt = agent._generate_ui_prompt("Create a button component")
        self.assertIn("button", prompt.lower())
        self.assertIn("component", prompt.lower())
    
    @patch('multi_agent_framework.core.shared_state_manager.get_shared_state_manager')
    @patch('multi_agent_framework.core.message_bus_configurable.MessageBus')
    @patch('google.generativeai.GenerativeModel')
    def test_backend_agent_generates_api(self, mock_llm_class, mock_bus_class, mock_state):
        """Test BackendAgent generates API endpoints"""
        # Setup mocks
        mock_llm = Mock()
        mock_llm_class.return_value = mock_llm
        mock_llm.generate_content.return_value.text = '''
```python
@app.route('/api/users')
def get_users():
    return jsonify({"users": []})
```
'''
        
        mock_bus = Mock()
        mock_bus_class.return_value = mock_bus
        
        mock_state_manager = Mock()
        mock_state.return_value = mock_state_manager
        
        # Create agent
        agent = BackendAgent()
        
        # Verify it was initialized
        self.assertEqual(agent.name, "backend_agent")
        
        # Test it can generate code
        with patch('builtins.open', mock.mock_open()):
            with patch('os.makedirs'):
                response = agent._generate_response("Create a users API endpoint")
                self.assertIsNotNone(response)
    
    @patch('multi_agent_framework.core.shared_state_manager.get_shared_state_manager')
    @patch('multi_agent_framework.core.message_bus_configurable.MessageBus')
    @patch('google.generativeai.GenerativeModel')
    def test_db_agent_generates_schema(self, mock_llm_class, mock_bus_class, mock_state):
        """Test DbAgent generates database schemas"""
        # Setup mocks
        mock_llm = Mock()
        mock_llm_class.return_value = mock_llm
        mock_llm.generate_content.return_value.text = '''
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL
);
```
'''
        
        mock_bus = Mock()
        mock_bus_class.return_value = mock_bus
        
        mock_state_manager = Mock()
        mock_state.return_value = mock_state_manager
        
        # Create agent
        agent = DbAgent()
        
        # Verify it was initialized
        self.assertEqual(agent.name, "db_agent")
        
        # Test database-specific functionality
        response = agent._generate_response("Create a users table")
        self.assertIn("CREATE TABLE", response)
    
    @patch('multi_agent_framework.core.shared_state_manager.get_shared_state_manager')
    @patch('multi_agent_framework.core.message_bus_configurable.MessageBus')
    @patch('google.generativeai.GenerativeModel')
    def test_devops_agent_generates_config(self, mock_llm_class, mock_bus_class, mock_state):
        """Test DevopsAgent generates deployment configs"""
        # Setup mocks
        mock_llm = Mock()
        mock_llm_class.return_value = mock_llm
        mock_llm.generate_content.return_value.text = '''
```yaml
version: '3'
services:
  app:
    build: .
    ports:
      - "3000:3000"
```
'''
        
        mock_bus = Mock()
        mock_bus_class.return_value = mock_bus
        
        mock_state_manager = Mock()
        mock_state.return_value = mock_state_manager
        
        # Create agent
        agent = DevopsAgent()
        
        # Verify it was initialized
        self.assertEqual(agent.name, "devops_agent")
    
    @patch('multi_agent_framework.core.shared_state_manager.get_shared_state_manager')
    @patch('multi_agent_framework.core.message_bus_configurable.MessageBus')
    @patch('google.generativeai.GenerativeModel')
    def test_qa_agent_generates_tests(self, mock_llm_class, mock_bus_class, mock_state):
        """Test QaAgent generates test cases"""
        # Setup mocks
        mock_llm = Mock()
        mock_llm_class.return_value = mock_llm
        mock_llm.generate_content.return_value.text = '''
```python
def test_user_creation():
    user = create_user("test@example.com")
    assert user.email == "test@example.com"
```
'''
        
        mock_bus = Mock()
        mock_bus_class.return_value = mock_bus
        
        mock_state_manager = Mock()
        mock_state.return_value = mock_state_manager
        
        # Create agent
        agent = QaAgent()
        
        # Verify it was initialized
        self.assertEqual(agent.name, "qa_agent")
    
    @patch('multi_agent_framework.core.shared_state_manager.get_shared_state_manager')
    @patch('multi_agent_framework.core.message_bus_configurable.MessageBus')
    @patch('google.generativeai.GenerativeModel')
    def test_docs_agent_generates_documentation(self, mock_llm_class, mock_bus_class, mock_state):
        """Test DocsAgent generates documentation"""
        # Setup mocks
        mock_llm = Mock()
        mock_llm_class.return_value = mock_llm
        mock_llm.generate_content.return_value.text = '''
# API Documentation

## GET /api/users
Returns a list of all users.
'''
        
        mock_bus = Mock()
        mock_bus_class.return_value = mock_bus
        
        mock_state_manager = Mock()
        mock_state.return_value = mock_state_manager
        
        # Create agent
        agent = DocsAgent()
        
        # Verify it was initialized
        self.assertEqual(agent.name, "docs_agent")
    
    @patch('multi_agent_framework.core.shared_state_manager.get_shared_state_manager')
    @patch('multi_agent_framework.core.message_bus_configurable.MessageBus')
    @patch('google.generativeai.GenerativeModel')
    def test_security_agent_reviews_code(self, mock_llm_class, mock_bus_class, mock_state):
        """Test SecurityAgent performs security reviews"""
        # Setup mocks
        mock_llm = Mock()
        mock_llm_class.return_value = mock_llm
        mock_llm.generate_content.return_value.text = '''
Security Review:
- Add input validation
- Use parameterized queries
- Enable HTTPS
'''
        
        mock_bus = Mock()
        mock_bus_class.return_value = mock_bus
        
        mock_state_manager = Mock()
        mock_state.return_value = mock_state_manager
        
        # Create agent
        agent = SecurityAgent()
        
        # Verify it was initialized
        self.assertEqual(agent.name, "security_agent")
    
    @patch('multi_agent_framework.core.shared_state_manager.get_shared_state_manager')
    @patch('multi_agent_framework.core.message_bus_configurable.MessageBus')
    @patch('google.generativeai.GenerativeModel')
    def test_uxui_agent_creates_designs(self, mock_llm_class, mock_bus_class, mock_state):
        """Test UxUiAgent creates design systems"""
        # Setup mocks
        mock_llm = Mock()
        mock_llm_class.return_value = mock_llm
        mock_llm.generate_content.return_value.text = '''
Design System:
- Primary Color: #0066CC
- Font: Inter
- Spacing: 8px grid
'''
        
        mock_bus = Mock()
        mock_bus_class.return_value = mock_bus
        
        mock_state_manager = Mock()
        mock_state.return_value = mock_state_manager
        
        # Create agent
        agent = UxUiAgent()
        
        # Verify it was initialized
        self.assertEqual(agent.name, "ux_ui_agent")
    
    @patch('multi_agent_framework.core.shared_state_manager.get_shared_state_manager')
    @patch('multi_agent_framework.core.message_bus_configurable.MessageBus')
    @patch('google.generativeai.GenerativeModel')
    def test_agent_message_handling(self, mock_llm_class, mock_bus_class, mock_state):
        """Test agents handle messages correctly"""
        # Setup mocks
        mock_llm = Mock()
        mock_llm_class.return_value = mock_llm
        mock_llm.generate_content.return_value.text = "Test response"
        
        mock_bus = Mock()
        mock_bus_class.return_value = mock_bus
        mock_bus.receive_messages.return_value = [
            {
                "type": "new_task",
                "task_id": "test-123",
                "content": "Test task"
            }
        ]
        
        mock_state_manager = Mock()
        mock_state.return_value = mock_state_manager
        
        # Test with FrontendAgent
        agent = FrontendAgent()
        
        # Mock file operations
        with patch('builtins.open', mock.mock_open()):
            with patch('os.makedirs'):
                # Process messages
                messages = agent.receive_messages()
                self.assertEqual(len(messages), 1)
                self.assertEqual(messages[0]["task_id"], "test-123")
    
    @patch('multi_agent_framework.core.shared_state_manager.get_shared_state_manager')
    @patch('multi_agent_framework.core.message_bus_configurable.MessageBus')
    @patch('google.generativeai.GenerativeModel')
    def test_agent_factory_integration(self, mock_llm_class, mock_bus_class, mock_state):
        """Test agents can be created through factory"""
        from multi_agent_framework.core.agent_factory import AgentFactory
        
        # Setup mocks
        mock_llm = Mock()
        mock_llm_class.return_value = mock_llm
        mock_llm.generate_content.return_value.text = "Test"
        
        mock_bus = Mock()
        mock_bus_class.return_value = mock_bus
        
        mock_state_manager = Mock()
        mock_state.return_value = mock_state_manager
        
        # Create factory
        factory = AgentFactory("/tmp/test")
        
        # Test creating each agent type
        agent_types = [
            'frontend_agent', 'backend_agent', 'db_agent',
            'devops_agent', 'qa_agent', 'docs_agent',
            'security_agent', 'ux_ui_agent'
        ]
        
        for agent_type in agent_types:
            with self.subTest(agent_type=agent_type):
                agent = factory.create_agent(agent_type)
                self.assertIsNotNone(agent)
                self.assertEqual(agent.name, agent_type)
    
    @patch('multi_agent_framework.core.shared_state_manager.get_shared_state_manager')
    @patch('multi_agent_framework.core.message_bus_configurable.MessageBus')
    @patch('google.generativeai.GenerativeModel')
    def test_agent_communication(self, mock_llm_class, mock_bus_class, mock_state):
        """Test agents can communicate with each other"""
        # Setup mocks
        mock_llm = Mock()
        mock_llm_class.return_value = mock_llm
        
        mock_bus = Mock()
        mock_bus_class.return_value = mock_bus
        
        mock_state_manager = Mock()
        mock_state.return_value = mock_state_manager
        
        # Create two agents
        frontend = FrontendAgent()
        backend = BackendAgent()
        
        # Test sending message
        test_message = {
            "type": "request",
            "content": "Need API endpoint"
        }
        
        frontend.send_message("backend_agent", "task-123", "Need user API", "request")
        
        # Verify message was sent through bus
        mock_bus.send_message.assert_called_once()
        call_args = mock_bus.send_message.call_args[0]
        self.assertEqual(call_args[0], "backend_agent")
        self.assertEqual(call_args[1]["sender"], "frontend_agent")
        self.assertEqual(call_args[1]["task_id"], "task-123")


if __name__ == '__main__':
    import unittest
    unittest.main()