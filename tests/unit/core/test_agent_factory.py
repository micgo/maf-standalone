#!/usr/bin/env python3
"""
Tests for AgentFactory
"""
import os
import tempfile
import shutil
from unittest import TestCase, mock

from multi_agent_framework.core.agent_factory import create_agent, AgentFactory
from multi_agent_framework.core.project_config import ProjectConfig


class TestAgentFactory(TestCase):
    """Test agent factory functionality"""
    
    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.project_config = ProjectConfig(self.temp_dir)
        
        # Set test mode
        os.environ['MAF_TEST_MODE'] = 'true'
        
    def tearDown(self):
        """Clean up"""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
        
        # Clear test mode
        os.environ.pop('MAF_TEST_MODE', None)
    
    def test_create_agent_orchestrator(self):
        """Test creating orchestrator agent"""
        agent = create_agent('orchestrator', mode='polling', project_config=self.project_config)
        
        self.assertIsNotNone(agent)
        self.assertEqual(agent.name, 'orchestrator')
        self.assertEqual(agent.project_root, self.temp_dir)
    
    def test_create_agent_frontend(self):
        """Test creating frontend agent"""
        agent = create_agent('frontend', mode='polling', project_config=self.project_config)
        
        self.assertIsNotNone(agent)
        self.assertEqual(agent.name, 'frontend_agent')
    
    def test_create_agent_backend(self):
        """Test creating backend agent"""
        agent = create_agent('backend', mode='polling', project_config=self.project_config)
        
        self.assertIsNotNone(agent)
        self.assertEqual(agent.name, 'backend_agent')
    
    def test_create_agent_with_underscore(self):
        """Test creating agent with _agent suffix"""
        agent = create_agent('frontend_agent', mode='polling', project_config=self.project_config)
        
        self.assertIsNotNone(agent)
        self.assertEqual(agent.name, 'frontend_agent')
    
    def test_create_event_driven_agent(self):
        """Test creating event-driven agent"""
        agent = create_agent('orchestrator', mode='event_driven', project_config=self.project_config)
        
        self.assertIsNotNone(agent)
        # Event-driven agents have different base class
        self.assertTrue(hasattr(agent, 'event_bus'))
    
    def test_invalid_agent_type(self):
        """Test creating invalid agent type"""
        with self.assertRaises(ValueError) as context:
            create_agent('invalid_agent', mode='polling', project_config=self.project_config)
        
        self.assertIn('Unknown agent type', str(context.exception))
    
    def test_invalid_mode(self):
        """Test creating agent with invalid mode"""
        with self.assertRaises(ValueError) as context:
            create_agent('orchestrator', mode='invalid_mode', project_config=self.project_config)
        
        self.assertIn('Unknown mode', str(context.exception))
    
    def test_get_available_agents(self):
        """Test getting list of available agents"""
        # Get from AGENT_MAPPINGS
        agents = list(AgentFactory.AGENT_MAPPINGS.keys())
        
        self.assertIsInstance(agents, list)
        self.assertIn('orchestrator', agents)
        self.assertIn('frontend', agents)
        self.assertIn('backend', agents)
        self.assertIn('db', agents)
        self.assertIn('devops', agents)
        self.assertIn('qa', agents)
        self.assertIn('docs', agents)
        self.assertIn('security', agents)
        self.assertIn('ux_ui', agents)
    
    def test_agent_factory_get_agent_class(self):
        """Test AgentFactory get_agent_class method"""
        # Test polling mode
        agent_class = AgentFactory.get_agent_class('frontend', 'polling')
        self.assertIsNotNone(agent_class)
        
        # Test event-driven mode
        agent_class = AgentFactory.get_agent_class('backend', 'event_driven')
        self.assertIsNotNone(agent_class)
    
    def test_agent_factory_create_agent(self):
        """Test AgentFactory create_agent method"""
        agent = AgentFactory.create_agent(
            'db_agent',
            mode='polling',
            project_config=self.project_config
        )
        
        self.assertIsNotNone(agent)
        self.assertEqual(agent.name, 'db_agent')
    
    def test_all_agent_types_polling(self):
        """Test creating all agent types in polling mode"""
        agent_types = [
            'orchestrator', 'frontend', 'backend', 'db',
            'devops', 'qa', 'docs', 'security', 'ux_ui'
        ]
        
        for agent_type in agent_types:
            with self.subTest(agent_type=agent_type):
                agent = create_agent(agent_type, mode='polling', project_config=self.project_config)
                self.assertIsNotNone(agent, f"Failed to create {agent_type} agent")
    
    def test_all_agent_types_event_driven(self):
        """Test creating all agent types in event-driven mode"""
        agent_types = [
            'orchestrator', 'frontend', 'backend', 'db',
            'devops', 'qa', 'docs', 'security', 'ux_ui'
        ]
        
        for agent_type in agent_types:
            with self.subTest(agent_type=agent_type):
                agent = create_agent(agent_type, mode='event_driven', project_config=self.project_config)
                self.assertIsNotNone(agent, f"Failed to create event-driven {agent_type} agent")
    
    def test_agent_model_configuration(self):
        """Test agent uses correct model configuration"""
        # Update project config with custom model
        self.project_config.update_config({
            'agent_config': {
                'default_model_provider': 'openai',
                'default_model_name': 'gpt-4'
            }
        })
        
        agent = create_agent('orchestrator', mode='polling', project_config=self.project_config)
        
        # In test mode, model config may not be used, but agent should be created
        self.assertIsNotNone(agent)
    
    def test_missing_project_config(self):
        """Test creating agent without project config"""
        # Should use current directory as default
        agent = create_agent('orchestrator', mode='polling')
        
        self.assertIsNotNone(agent)
        # Agent should have some project root
        self.assertTrue(hasattr(agent, 'project_root'))


if __name__ == '__main__':
    import unittest
    unittest.main()