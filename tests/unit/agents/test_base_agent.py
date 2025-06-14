#!/usr/bin/env python3
"""
Tests for BaseAgent class (polling mode)
"""
import os
import time
import json
from unittest import TestCase, mock
from unittest.mock import Mock, patch, MagicMock

from multi_agent_framework.agents.base_agent import BaseAgent
from multi_agent_framework.core.project_config import ProjectConfig


class TestAgentImpl(BaseAgent):
    """Test implementation of BaseAgent"""
    
    def process_task(self, task):
        """Simple task processing for testing"""
        return {
            "status": "completed",
            "result": f"Processed task: {task.get('description', 'Unknown')}"
        }


class TestBaseAgent(TestCase):
    """Test BaseAgent functionality"""
    
    def setUp(self):
        """Set up test environment"""
        # Create temp directory
        self.temp_dir = '/tmp/test_agent'
        os.makedirs(self.temp_dir, exist_ok=True)
        
        # Create project config
        self.project_config = ProjectConfig(self.temp_dir)
        
        # Mock LLM
        self.llm_patcher = patch('google.generativeai.GenerativeModel')
        self.mock_llm_class = self.llm_patcher.start()
        self.mock_llm = Mock()
        self.mock_llm_class.return_value = self.mock_llm
        
        # Default LLM response
        self.mock_llm.generate_content.return_value.text = '{"result": "test"}'
        
    def tearDown(self):
        """Clean up"""
        self.llm_patcher.stop()
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_agent_initialization(self):
        """Test agent initialization"""
        agent = TestAgentImpl(
            name="test_agent",
            project_root=self.temp_dir,
            message_queue_dir=os.path.join(self.temp_dir, 'messages')
        )
        
        self.assertEqual(agent.name, "test_agent")
        self.assertEqual(agent.project_root, self.temp_dir)
        self.assertIsNotNone(agent.llm)
        self.assertFalse(agent.running)
    
    def test_generate_response(self):
        """Test LLM response generation"""
        agent = TestAgentImpl("test_agent", self.temp_dir)
        
        # Set up mock response
        self.mock_llm.generate_content.return_value.text = "Test response from LLM"
        
        response = agent._generate_response("Test prompt")
        
        self.assertEqual(response, "Test response from LLM")
        self.mock_llm.generate_content.assert_called_once_with("Test prompt")
    
    def test_parse_json_response(self):
        """Test JSON parsing from LLM responses"""
        agent = TestAgentImpl("test_agent", self.temp_dir)
        
        # Test valid JSON
        json_str = '{"key": "value", "number": 42}'
        result = agent._parse_json_response(json_str)
        self.assertEqual(result, {"key": "value", "number": 42})
        
        # Test JSON with markdown blocks
        json_with_markdown = '```json\n{"wrapped": true}\n```'
        result = agent._parse_json_response(json_with_markdown)
        self.assertEqual(result, {"wrapped": True})
        
        # Test invalid JSON
        result = agent._parse_json_response("not json")
        self.assertIsNone(result)
    
    def test_check_messages(self):
        """Test message checking"""
        agent = TestAgentImpl("test_agent", self.temp_dir)
        
        # Mock message bus
        with patch.object(agent.message_bus, 'receive_messages') as mock_receive:
            # No messages
            mock_receive.return_value = []
            agent._check_messages()
            
            # With messages
            test_messages = [
                {
                    "type": "task",
                    "task_id": "123",
                    "description": "Test task",
                    "sender": "orchestrator"
                }
            ]
            mock_receive.return_value = test_messages
            
            with patch.object(agent, '_handle_message') as mock_handle:
                agent._check_messages()
                mock_handle.assert_called_once_with(test_messages[0])
    
    def test_handle_task_message(self):
        """Test handling task messages"""
        agent = TestAgentImpl("test_agent", self.temp_dir)
        
        task_message = {
            "type": "task",
            "task_id": "task-123",
            "description": "Implement feature X",
            "sender": "orchestrator"
        }
        
        with patch.object(agent, 'process_task') as mock_process:
            mock_process.return_value = {"status": "completed", "result": "Done"}
            
            with patch.object(agent.message_bus, 'send_message') as mock_send:
                agent._handle_message(task_message)
                
                # Check task was processed
                mock_process.assert_called_once()
                
                # Check response was sent
                mock_send.assert_called_once()
                sent_message = mock_send.call_args[0][1]
                self.assertEqual(sent_message['type'], 'task_result')
                self.assertEqual(sent_message['task_id'], 'task-123')
                self.assertEqual(sent_message['status'], 'completed')
    
    def test_handle_non_task_message(self):
        """Test handling non-task messages"""
        agent = TestAgentImpl("test_agent", self.temp_dir)
        
        # Status message
        status_message = {
            "type": "status",
            "sender": "orchestrator"
        }
        
        with patch.object(agent.message_bus, 'send_message') as mock_send:
            agent._handle_message(status_message)
            
            # Should send alive response
            mock_send.assert_called_once()
            sent_message = mock_send.call_args[0][1]
            self.assertEqual(sent_message['type'], 'status')
            self.assertEqual(sent_message['status'], 'alive')
    
    def test_run_loop(self):
        """Test the main run loop"""
        agent = TestAgentImpl("test_agent", self.temp_dir)
        
        # Mock check_messages to stop after 2 iterations
        check_count = 0
        def mock_check():
            nonlocal check_count
            check_count += 1
            if check_count >= 2:
                agent.stop()
        
        with patch.object(agent, '_check_messages', side_effect=mock_check):
            with patch('time.sleep'):  # Speed up test
                agent.run()
        
        self.assertEqual(check_count, 2)
        self.assertFalse(agent.running)
    
    def test_stop_agent(self):
        """Test stopping the agent"""
        agent = TestAgentImpl("test_agent", self.temp_dir)
        
        # Start in thread
        import threading
        agent.running = True
        thread = threading.Thread(target=agent.run, daemon=True)
        thread.start()
        
        # Stop agent
        agent.stop()
        thread.join(timeout=1)
        
        self.assertFalse(agent.running)
    
    def test_error_handling_in_task_processing(self):
        """Test error handling during task processing"""
        agent = TestAgentImpl("test_agent", self.temp_dir)
        
        task_message = {
            "type": "task",
            "task_id": "task-456",
            "description": "Failing task",
            "sender": "orchestrator"
        }
        
        # Make process_task raise an exception
        with patch.object(agent, 'process_task', side_effect=Exception("Test error")):
            with patch.object(agent.message_bus, 'send_message') as mock_send:
                agent._handle_message(task_message)
                
                # Should send error response
                mock_send.assert_called_once()
                sent_message = mock_send.call_args[0][1]
                self.assertEqual(sent_message['type'], 'task_result')
                self.assertEqual(sent_message['status'], 'error')
                self.assertIn('Test error', sent_message['error'])
    
    def test_model_selection(self):
        """Test different model providers"""
        # Test with OpenAI
        with patch('openai.ChatCompletion') as mock_openai:
            agent = TestAgentImpl(
                name="test_agent",
                project_root=self.temp_dir,
                model_provider="openai"
            )
            # Agent should initialize without error
            self.assertEqual(agent.model_provider, "openai")
        
        # Test with Anthropic
        with patch('anthropic.Client') as mock_anthropic:
            agent = TestAgentImpl(
                name="test_agent",
                project_root=self.temp_dir,
                model_provider="anthropic"
            )
            self.assertEqual(agent.model_provider, "anthropic")
    
    def test_project_state_integration(self):
        """Test integration with project state manager"""
        agent = TestAgentImpl("test_agent", self.temp_dir)
        
        # Mock project state manager
        with patch('multi_agent_framework.core.project_state_manager.ProjectStateManager') as mock_psm:
            mock_state_manager = Mock()
            mock_psm.return_value = mock_state_manager
            
            # Create new agent to use mocked state manager
            agent2 = TestAgentImpl("test_agent", self.temp_dir)
            
            # Process a task
            task = {"task_id": "123", "description": "Test"}
            with patch.object(agent2.message_bus, 'send_message'):
                agent2._handle_message({
                    "type": "task",
                    "task_id": "123",
                    "description": "Test",
                    "sender": "orchestrator"
                })
            
            # State manager should be notified
            mock_state_manager.start_task.assert_called()
            mock_state_manager.complete_task.assert_called()
    
    def test_code_block_extraction(self):
        """Test extracting code blocks from LLM responses"""
        agent = TestAgentImpl("test_agent", self.temp_dir)
        
        # Python code block
        response = '''Here's the code:
```python
def hello():
    print("Hello, World!")
```
That's the function.'''
        
        code = agent._extract_code_block(response, "python")
        self.assertEqual(code.strip(), 'def hello():\n    print("Hello, World!")')
        
        # No code block
        response = "Just text, no code"
        code = agent._extract_code_block(response, "python")
        self.assertEqual(code, response)
    
    def test_multiple_task_handling(self):
        """Test handling multiple tasks in sequence"""
        agent = TestAgentImpl("test_agent", self.temp_dir)
        
        tasks = [
            {"type": "task", "task_id": f"task-{i}", "description": f"Task {i}", "sender": "orchestrator"}
            for i in range(3)
        ]
        
        with patch.object(agent.message_bus, 'receive_messages', side_effect=[tasks, []]):
            with patch.object(agent.message_bus, 'send_message') as mock_send:
                agent._check_messages()
                
                # Should process all tasks
                self.assertEqual(mock_send.call_count, 3)
                
                # Check each response
                for i, call in enumerate(mock_send.call_args_list):
                    sent_message = call[0][1]
                    self.assertEqual(sent_message['task_id'], f'task-{i}')
                    self.assertEqual(sent_message['status'], 'completed')


if __name__ == '__main__':
    import unittest
    unittest.main()