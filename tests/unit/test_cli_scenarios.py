#!/usr/bin/env python3
"""
Scenario-based tests for CLI commands
"""
import os
import sys
import json
import tempfile
import shutil
from unittest import TestCase, mock
from click.testing import CliRunner

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from multi_agent_framework.cli import cli


class TestCLIScenarios(TestCase):
    """Test real-world CLI usage scenarios"""
    
    def setUp(self):
        """Set up test environment"""
        self.runner = CliRunner()
        self.temp_dir = tempfile.mkdtemp()
        os.environ['MAF_TEST_MODE'] = '1'
        
    def tearDown(self):
        """Clean up test environment"""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
        os.environ.pop('MAF_TEST_MODE', None)
            
    def test_full_workflow(self):
        """Test complete workflow from init to trigger"""
        with self.runner.isolated_filesystem(temp_dir=self.temp_dir):
            # 1. Initialize project
            result = self.runner.invoke(cli, ['init', '--name', 'TestProject', '--type', 'nextjs'])
            self.assertEqual(result.exit_code, 0)
            
            # 2. Check status (should show not running)
            result = self.runner.invoke(cli, ['status'])
            self.assertEqual(result.exit_code, 0)
            
            # 3. Configure specific agents
            result = self.runner.invoke(cli, ['config', 'set', 'agent_config.enabled_agents', '["orchestrator", "frontend_agent"]'])
            self.assertEqual(result.exit_code, 0)
            
            # 4. Get configuration to verify
            result = self.runner.invoke(cli, ['config', 'get', 'agent_config.enabled_agents'])
            self.assertEqual(result.exit_code, 0)
            self.assertIn('orchestrator', result.output)
            
    def test_multiple_projects(self):
        """Test managing multiple projects"""
        with self.runner.isolated_filesystem(temp_dir=self.temp_dir):
            # Create two projects
            os.makedirs('project1')
            os.makedirs('project2')
            
            # Initialize both
            result = self.runner.invoke(cli, ['init', 'project1', '--name', 'Project1'])
            self.assertEqual(result.exit_code, 0)
            
            result = self.runner.invoke(cli, ['init', 'project2', '--name', 'Project2'])
            self.assertEqual(result.exit_code, 0)
            
            # Verify separate configs
            with open('project1/.maf-config.json') as f:
                config1 = json.load(f)
                self.assertEqual(config1['project_name'], 'Project1')
                
            with open('project2/.maf-config.json') as f:
                config2 = json.load(f)
                self.assertEqual(config2['project_name'], 'Project2')
                
    def test_reinit_existing_project(self):
        """Test reinitializing an existing project"""
        with self.runner.isolated_filesystem(temp_dir=self.temp_dir):
            # First init
            result = self.runner.invoke(cli, ['init', '--name', 'Original'])
            self.assertEqual(result.exit_code, 0)
            
            # Try to reinit (should fail without force)
            result = self.runner.invoke(cli, ['init', '--name', 'New'])
            self.assertNotEqual(result.exit_code, 0)
            self.assertIn('already initialized', result.output.lower())
            
    def test_config_nested_operations(self):
        """Test complex config operations"""
        with self.runner.isolated_filesystem(temp_dir=self.temp_dir):
            self.runner.invoke(cli, ['init'])
            
            # Set nested value
            result = self.runner.invoke(cli, ['config', 'set', 'agent_models.frontend_agent.provider', 'openai'])
            self.assertEqual(result.exit_code, 0)
            
            # Set another nested value
            result = self.runner.invoke(cli, ['config', 'set', 'agent_models.frontend_agent.name', 'gpt-4'])
            self.assertEqual(result.exit_code, 0)
            
            # Get parent object
            result = self.runner.invoke(cli, ['config', 'get', 'agent_models.frontend_agent'])
            self.assertEqual(result.exit_code, 0)
            self.assertIn('openai', result.output)
            self.assertIn('gpt-4', result.output)
            
    def test_invalid_json_handling(self):
        """Test handling of invalid JSON in config set"""
        with self.runner.isolated_filesystem(temp_dir=self.temp_dir):
            self.runner.invoke(cli, ['init'])
            
            # Invalid JSON
            result = self.runner.invoke(cli, ['config', 'set', 'test_array', '[1,2,3'])  # Missing closing bracket
            self.assertNotEqual(result.exit_code, 0)
            self.assertIn('invalid', result.output.lower())
            
    def test_environment_variables(self):
        """Test CLI with environment variables"""
        with self.runner.isolated_filesystem(temp_dir=self.temp_dir):
            # Set env vars
            os.environ['MAF_DEFAULT_PROVIDER'] = 'anthropic'
            os.environ['MAF_LOG_LEVEL'] = 'DEBUG'
            
            try:
                result = self.runner.invoke(cli, ['init'])
                self.assertEqual(result.exit_code, 0)
                
                # Check if env vars affected config
                with open('.maf-config.json') as f:
                    config = json.load(f)
                    # Env vars should be considered during agent operations
                    
            finally:
                os.environ.pop('MAF_DEFAULT_PROVIDER', None)
                os.environ.pop('MAF_LOG_LEVEL', None)
                
    def test_help_consistency(self):
        """Test that help messages are consistent"""
        # Main help
        main_help = self.runner.invoke(cli, ['--help'])
        
        # Check all commands are listed
        for cmd in ['init', 'launch', 'trigger', 'status', 'reset', 'config']:
            self.assertIn(cmd, main_help.output)
            
        # Check each command's help has required sections
        for cmd in ['init', 'launch', 'trigger', 'status', 'reset']:
            result = self.runner.invoke(cli, [cmd, '--help'])
            self.assertIn('Usage:', result.output)
            if cmd != 'status':  # Status might not have options
                self.assertIn('Options:', result.output)
                
    def test_json_output_formats(self):
        """Test JSON output is valid"""
        with self.runner.isolated_filesystem(temp_dir=self.temp_dir):
            self.runner.invoke(cli, ['init'])
            
            # Status JSON
            result = self.runner.invoke(cli, ['status', '--json'])
            if result.exit_code == 0 and result.output.strip():
                # Should be valid JSON
                data = json.loads(result.output)
                self.assertIsInstance(data, dict)
                
    def test_error_recovery(self):
        """Test recovery from various error states"""
        with self.runner.isolated_filesystem(temp_dir=self.temp_dir):
            # Create corrupted config
            self.runner.invoke(cli, ['init'])
            
            # Corrupt the config file
            with open('.maf-config.json', 'w') as f:
                f.write('{"invalid": json}')  # Invalid JSON
                
            # Commands should handle gracefully
            result = self.runner.invoke(cli, ['status'])
            # Should show error but not crash
            self.assertIn('error', result.output.lower())
            
    def test_path_handling(self):
        """Test various path formats"""
        with self.runner.isolated_filesystem(temp_dir=self.temp_dir):
            # Relative paths
            os.makedirs('sub/dir/project')
            result = self.runner.invoke(cli, ['init', 'sub/dir/project'])
            self.assertEqual(result.exit_code, 0)
            
            # Path with trailing slash
            os.makedirs('another')
            result = self.runner.invoke(cli, ['init', 'another/'])
            self.assertEqual(result.exit_code, 0)
            
            # Current directory with dot
            os.makedirs('dotproject')
            os.chdir('dotproject')
            result = self.runner.invoke(cli, ['init', '.'])
            self.assertEqual(result.exit_code, 0)


if __name__ == '__main__':
    import unittest
    unittest.main()