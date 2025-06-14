#!/usr/bin/env python3
"""
Enhanced CLI tests to improve coverage
"""
import os
import json
from unittest import TestCase
from unittest.mock import patch, Mock, MagicMock
from click.testing import CliRunner

from multi_agent_framework.cli import cli, _get_recommended_agents


class TestCLIEnhanced(TestCase):
    """Enhanced CLI tests for better coverage"""
    
    def setUp(self):
        """Set up test environment"""
        self.runner = CliRunner()
        self.temp_dir = None
    
    def tearDown(self):
        """Clean up"""
        if self.temp_dir and os.path.exists(self.temp_dir):
            import shutil
            shutil.rmtree(self.temp_dir)
    
    def test_get_recommended_agents(self):
        """Test agent recommendation logic"""
        # Test different project types
        self.assertIn('frontend_agent', _get_recommended_agents('react'))
        self.assertIn('backend_agent', _get_recommended_agents('django'))
        self.assertIn('frontend_agent', _get_recommended_agents('nextjs'))
        self.assertIn('db_agent', _get_recommended_agents('flask'))
        
        # Test default/unknown project type
        default_agents = _get_recommended_agents('unknown')
        self.assertIn('frontend_agent', default_agents)
        self.assertIn('backend_agent', default_agents)
    
    @patch('multi_agent_framework.core.project_config.ProjectConfig')
    def test_launch_with_missing_orchestrator_confirm_yes(self, mock_config_class):
        """Test launch with missing orchestrator and user confirms"""
        with self.runner.isolated_filesystem() as temp_dir:
            self.temp_dir = temp_dir
            
            # Mock config
            mock_config = Mock()
            mock_config.get_project_root.return_value = temp_dir
            mock_config.get_agents.return_value = ['frontend_agent', 'backend_agent']
            mock_config.save.return_value = None
            mock_config_class.return_value = mock_config
            
            # Run with user confirming to add orchestrator
            result = self.runner.invoke(
                cli, 
                ['launch', '--agents', 'frontend_agent,backend_agent'],
                input='y\n'
            )
            
            self.assertIn('Critical agents missing', result.output)
            self.assertIn('Add orchestrator', result.output)
    
    @patch('multi_agent_framework.core.project_config.ProjectConfig')
    def test_launch_with_missing_orchestrator_confirm_no(self, mock_config_class):
        """Test launch with missing orchestrator and user declines"""
        with self.runner.isolated_filesystem() as temp_dir:
            self.temp_dir = temp_dir
            
            # Mock config
            mock_config = Mock()
            mock_config.get_project_root.return_value = temp_dir
            mock_config.get_agents.return_value = ['frontend_agent', 'backend_agent']
            mock_config_class.return_value = mock_config
            
            # Run with user declining to add orchestrator
            result = self.runner.invoke(
                cli,
                ['launch', '--agents', 'frontend_agent,backend_agent'],
                input='n\n'
            )
            
            self.assertIn('Critical agents missing', result.output)
    
    def test_config_commands(self):
        """Test config get/set/list commands"""
        with self.runner.isolated_filesystem() as temp_dir:
            self.temp_dir = temp_dir
            
            # Initialize project first
            self.runner.invoke(cli, ['init', temp_dir])
            
            # Test config set
            result = self.runner.invoke(cli, ['config', 'set', 'test_key', 'test_value'])
            self.assertEqual(result.exit_code, 0)
            
            # Test config get
            result = self.runner.invoke(cli, ['config', 'get', 'test_key'])
            self.assertEqual(result.exit_code, 0)
            self.assertIn('test_value', result.output)
            
            # Test config list
            result = self.runner.invoke(cli, ['config', 'list'])
            self.assertEqual(result.exit_code, 0)
            self.assertIn('test_key', result.output)
    
    def test_config_set_json_complex(self):
        """Test setting complex JSON config values"""
        with self.runner.isolated_filesystem() as temp_dir:
            self.temp_dir = temp_dir
            
            # Initialize project
            self.runner.invoke(cli, ['init', temp_dir])
            
            # Set complex JSON
            json_value = '{"nested": {"key": "value", "array": [1, 2, 3]}}'
            result = self.runner.invoke(
                cli,
                ['config', 'set', '--json', 'complex_key', json_value]
            )
            self.assertEqual(result.exit_code, 0)
            
            # Verify it was set correctly
            result = self.runner.invoke(cli, ['config', 'get', 'complex_key'])
            self.assertIn('nested', result.output)
    
    def test_config_delete(self):
        """Test config delete command"""
        with self.runner.isolated_filesystem() as temp_dir:
            self.temp_dir = temp_dir
            
            # Initialize and set a value
            self.runner.invoke(cli, ['init', temp_dir])
            self.runner.invoke(cli, ['config', 'set', 'delete_me', 'value'])
            
            # Delete the config
            result = self.runner.invoke(cli, ['config', 'delete', 'delete_me'])
            self.assertEqual(result.exit_code, 0)
            
            # Verify it's gone
            result = self.runner.invoke(cli, ['config', 'get', 'delete_me'])
            self.assertNotEqual(result.exit_code, 0)
    
    @patch('multi_agent_framework.core.agent_factory.AgentFactory')
    @patch('subprocess.Popen')
    def test_launch_with_all_options(self, mock_popen, mock_factory):
        """Test launch command with all options"""
        with self.runner.isolated_filesystem() as temp_dir:
            self.temp_dir = temp_dir
            
            # Initialize project
            self.runner.invoke(cli, ['init', temp_dir])
            
            # Mock subprocess
            mock_process = Mock()
            mock_process.poll.return_value = None
            mock_popen.return_value = mock_process
            
            # Run launch with all options
            result = self.runner.invoke(
                cli,
                ['launch', '--mode', 'event-driven', '--verbose', '--agents', 'all']
            )
            
            self.assertEqual(result.exit_code, 0)
            self.assertIn('event-driven', result.output)
    
    def test_modes_command(self):
        """Test modes listing command"""
        result = self.runner.invoke(cli, ['modes'])
        
        self.assertEqual(result.exit_code, 0)
        self.assertIn('polling', result.output)
        self.assertIn('event-driven', result.output)
        self.assertIn('distributed', result.output)
    
    def test_verbose_logging(self):
        """Test verbose flag enables detailed logging"""
        with self.runner.isolated_filesystem() as temp_dir:
            self.temp_dir = temp_dir
            
            # Run with verbose flag
            result = self.runner.invoke(cli, ['--verbose', 'init', temp_dir])
            
            # Should see debug-level output
            self.assertIn('Project root:', result.output)
    
    def test_status_with_all_formats(self):
        """Test status command with different output formats"""
        with self.runner.isolated_filesystem() as temp_dir:
            self.temp_dir = temp_dir
            
            # Initialize project
            self.runner.invoke(cli, ['init', temp_dir])
            
            # Test JSON format
            result = self.runner.invoke(cli, ['status', '--format', 'json'])
            self.assertEqual(result.exit_code, 0)
            data = json.loads(result.output)
            self.assertIn('agents', data)
            
            # Test detailed format
            result = self.runner.invoke(cli, ['status', '--detailed'])
            self.assertEqual(result.exit_code, 0)
            self.assertIn('Configuration', result.output)
    
    def test_error_handling_with_context(self):
        """Test error handling shows helpful context"""
        # Test with non-existent project
        result = self.runner.invoke(cli, ['status'], cwd='/nonexistent')
        
        self.assertNotEqual(result.exit_code, 0)
        self.assertIn('not initialized', result.output.lower())
    
    @patch('multi_agent_framework.recovery_tool.RecoveryManager')
    def test_recover_command(self, mock_recovery_class):
        """Test recover command"""
        with self.runner.isolated_filesystem() as temp_dir:
            self.temp_dir = temp_dir
            
            # Initialize project
            self.runner.invoke(cli, ['init', temp_dir])
            
            # Mock recovery manager
            mock_recovery = Mock()
            mock_recovery.recover_tasks.return_value = {
                'recovered': 2,
                'failed': 0
            }
            mock_recovery_class.return_value = mock_recovery
            
            # Run recover
            result = self.runner.invoke(cli, ['recover'])
            
            self.assertEqual(result.exit_code, 0)
            mock_recovery.recover_tasks.assert_called_once()
    
    def test_init_with_env_var_override(self):
        """Test init uses environment variables"""
        with self.runner.isolated_filesystem() as temp_dir:
            self.temp_dir = temp_dir
            
            # Set environment variables
            env = {
                'MAF_DEFAULT_MODE': 'event-driven',
                'MAF_DEFAULT_MODEL': 'gpt-4'
            }
            
            result = self.runner.invoke(cli, ['init', temp_dir], env=env)
            
            self.assertEqual(result.exit_code, 0)
            
            # Check config was created with env values
            config_path = os.path.join(temp_dir, '.maf-config.json')
            with open(config_path) as f:
                config = json.load(f)
                self.assertEqual(config['default_mode'], 'event-driven')
    
    def test_trigger_with_priority(self):
        """Test trigger command with priority levels"""
        with self.runner.isolated_filesystem() as temp_dir:
            self.temp_dir = temp_dir
            
            # Initialize project
            self.runner.invoke(cli, ['init', temp_dir])
            
            # Test high priority trigger
            result = self.runner.invoke(
                cli,
                ['trigger', '--priority', 'high', 'Critical feature']
            )
            
            self.assertEqual(result.exit_code, 0)
            self.assertIn('high', result.output.lower())
    
    def test_help_for_all_commands(self):
        """Test help text for all commands"""
        commands = ['init', 'launch', 'status', 'trigger', 'reset', 'config', 'modes']
        
        for cmd in commands:
            result = self.runner.invoke(cli, [cmd, '--help'])
            self.assertEqual(result.exit_code, 0)
            self.assertIn('Usage:', result.output)
            self.assertIn('Options:', result.output)
    
    def test_project_type_detection_override(self):
        """Test project type can be overridden"""
        with self.runner.isolated_filesystem() as temp_dir:
            self.temp_dir = temp_dir
            
            # Create package.json to trigger React detection
            with open('package.json', 'w') as f:
                json.dump({'dependencies': {'react': '^18.0.0'}}, f)
            
            # But override to Django
            result = self.runner.invoke(
                cli,
                ['init', '--project-type', 'django', temp_dir]
            )
            
            self.assertEqual(result.exit_code, 0)
            
            # Verify Django agents were recommended
            self.assertIn('backend_agent', result.output)
    
    def test_reset_with_backup(self):
        """Test reset command with backup option"""
        with self.runner.isolated_filesystem() as temp_dir:
            self.temp_dir = temp_dir
            
            # Initialize and create some data
            self.runner.invoke(cli, ['init', temp_dir])
            
            # Create a state file
            state_dir = os.path.join(temp_dir, '.maf-state')
            os.makedirs(state_dir, exist_ok=True)
            with open(os.path.join(state_dir, 'test.json'), 'w') as f:
                json.dump({'data': 'important'}, f)
            
            # Reset with backup
            result = self.runner.invoke(
                cli,
                ['reset', '--backup', '--yes']
            )
            
            self.assertEqual(result.exit_code, 0)
            self.assertIn('backup', result.output.lower())


if __name__ == '__main__':
    import unittest
    unittest.main()