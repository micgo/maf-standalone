#!/usr/bin/env python3
"""
Tests for ProjectConfig class
"""
import os
import json
import tempfile
import shutil
from unittest import TestCase

from multi_agent_framework.core.project_config import ProjectConfig


class TestProjectConfig(TestCase):
    """Test project configuration management"""
    
    def setUp(self):
        """Create temp directory for tests"""
        self.temp_dir = tempfile.mkdtemp()
        
    def tearDown(self):
        """Clean up temp directory"""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_default_config(self):
        """Test default configuration values"""
        config = ProjectConfig(self.temp_dir)
        
        # Check defaults
        self.assertEqual(config.config['project_name'], os.path.basename(self.temp_dir))
        self.assertEqual(config.config['project_type'], 'auto')
        self.assertEqual(config.get_default_mode(), 'polling')
        self.assertEqual(config.get_event_bus_type(), 'in_memory')
        
        # Check default agents
        agents = config.get_enabled_agents()
        self.assertIn('orchestrator', agents)
        self.assertIn('frontend_agent', agents)
        # Check we have more than just 2 agents
        self.assertGreaterEqual(len(agents), 2)  # At least 2 agents
    
    def test_project_type_detection(self):
        """Test automatic project type detection"""
        # Test Next.js detection
        with open(os.path.join(self.temp_dir, 'next.config.js'), 'w') as f:
            f.write('module.exports = {}')
        
        config = ProjectConfig(self.temp_dir)
        self.assertEqual(config.config['project_type'], 'nextjs')
        
    def test_react_project_detection(self):
        """Test React project detection"""
        package_json = {
            "name": "test-app",
            "dependencies": {
                "react": "^18.0.0",
                "react-dom": "^18.0.0"
            }
        }
        
        with open(os.path.join(self.temp_dir, 'package.json'), 'w') as f:
            json.dump(package_json, f)
        
        config = ProjectConfig(self.temp_dir)
        self.assertEqual(config.config['project_type'], 'react')
    
    def test_django_project_detection(self):
        """Test Django project detection"""
        # Create Django files
        with open(os.path.join(self.temp_dir, 'manage.py'), 'w') as f:
            f.write('#!/usr/bin/env python')
        with open(os.path.join(self.temp_dir, 'requirements.txt'), 'w') as f:
            f.write('django==4.2.0')
        
        config = ProjectConfig(self.temp_dir)
        self.assertEqual(config.config['project_type'], 'django')
    
    def test_save_and_load_config(self):
        """Test saving and loading configuration"""
        config = ProjectConfig(self.temp_dir)
        
        # Modify config
        config.update_config({
            'project_name': 'TestProject',
            'project_type': 'nextjs',
            'framework_config': {
                'default_mode': 'event'
            }
        })
        
        # Create new instance to test loading
        config2 = ProjectConfig(self.temp_dir)
        self.assertEqual(config2.config['project_name'], 'TestProject')
        self.assertEqual(config2.config['project_type'], 'nextjs')
        self.assertEqual(config2.get_default_mode(), 'event')
    
    def test_path_methods(self):
        """Test path getter methods"""
        config = ProjectConfig(self.temp_dir)
        
        # Test state file path
        state_path = config.get_state_file_path()
        self.assertEqual(state_path, os.path.join(self.temp_dir, '.maf/state.json'))
        
        # Test message queue dir
        queue_dir = config.get_message_queue_dir()
        self.assertEqual(queue_dir, os.path.join(self.temp_dir, '.maf/message_queues'))
        
        # Test log dir
        log_dir = config.get_log_dir()
        self.assertEqual(log_dir, os.path.join(self.temp_dir, '.maf/logs'))
    
    def test_model_config(self):
        """Test model configuration"""
        config = ProjectConfig(self.temp_dir)
        
        model_config = config.get_model_config()
        # Should use default gemini unless overridden
        self.assertIn(model_config['provider'], ['gemini', 'openai', 'anthropic'])
        self.assertIsNotNone(model_config['name'])
    
    def test_initialize_project(self):
        """Test project initialization"""
        config = ProjectConfig.initialize_project(self.temp_dir)
        
        # Check directories were created
        self.assertTrue(os.path.exists(config.get_message_queue_dir()))
        self.assertTrue(os.path.exists(config.get_log_dir()))
        
        # Check config file was saved
        self.assertTrue(os.path.exists(config.config_path))
    
    def test_deep_update(self):
        """Test deep update functionality"""
        config = ProjectConfig(self.temp_dir)
        
        # Test nested update
        config.update_config({
            'agent_config': {
                'default_model_provider': 'openai',
                'enabled_agents': ['orchestrator', 'frontend_agent']
            }
        })
        
        # Check update worked
        self.assertEqual(config.config['agent_config']['default_model_provider'], 'openai')
        self.assertEqual(len(config.get_enabled_agents()), 2)
        
        # Check other values preserved
        self.assertEqual(config.config['agent_config']['default_model_name'], 'gemini-2.0-flash-exp')
    
    def test_corrupt_config_handling(self):
        """Test handling of corrupt config files"""
        # Create corrupt config
        config_path = os.path.join(self.temp_dir, '.maf-config.json')
        with open(config_path, 'w') as f:
            f.write('{invalid json}')
        
        # Should fall back to defaults
        config = ProjectConfig(self.temp_dir)
        self.assertEqual(config.config['project_type'], 'auto')


if __name__ == '__main__':
    import unittest
    unittest.main()