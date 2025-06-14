#!/usr/bin/env python3
"""
Safe CLI tests that don't involve threading or agent launching
"""
import os
import sys
import json
import tempfile
import shutil
from unittest import TestCase
from click.testing import CliRunner

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from multi_agent_framework.cli import cli


class TestCLISafe(TestCase):
    """Safe CLI tests without threading issues"""
    
    def setUp(self):
        """Set up test environment"""
        self.runner = CliRunner()
        self.temp_dir = tempfile.mkdtemp()
        
    def tearDown(self):
        """Clean up test environment"""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
            
    def test_cli_version(self):
        """Test version command"""
        result = self.runner.invoke(cli, ['--version'])
        self.assertEqual(result.exit_code, 0)
        self.assertIn('version', result.output.lower())
        
    def test_cli_help(self):
        """Test help command"""
        result = self.runner.invoke(cli, ['--help'])
        self.assertEqual(result.exit_code, 0)
        self.assertIn('Multi-Agent Framework', result.output)
        
    def test_init_command(self):
        """Test init command"""
        with self.runner.isolated_filesystem(temp_dir=self.temp_dir):
            result = self.runner.invoke(cli, ['init'])
            self.assertEqual(result.exit_code, 0)
            self.assertIn('Initialized', result.output)
            self.assertTrue(os.path.exists('.maf-config.json'))
            
    def test_modes_command(self):
        """Test modes command"""
        result = self.runner.invoke(cli, ['modes'])
        self.assertEqual(result.exit_code, 0)
        self.assertIn('Polling Mode', result.output)
        self.assertIn('Event-Driven Mode', result.output)
        
    def test_status_command(self):
        """Test status command"""
        with self.runner.isolated_filesystem(temp_dir=self.temp_dir):
            self.runner.invoke(cli, ['init'])
            result = self.runner.invoke(cli, ['status'])
            self.assertEqual(result.exit_code, 0)
            self.assertIn('Framework Status', result.output)
            
    def test_trigger_command(self):
        """Test trigger command"""
        with self.runner.isolated_filesystem(temp_dir=self.temp_dir):
            self.runner.invoke(cli, ['init'])
            result = self.runner.invoke(cli, ['trigger', 'Create a test feature'])
            self.assertIn('Feature request', result.output)
            
    def test_reset_command(self):
        """Test reset command"""
        with self.runner.isolated_filesystem(temp_dir=self.temp_dir):
            self.runner.invoke(cli, ['init'])
            os.makedirs('.maf/message_queues', exist_ok=True)
            
            result = self.runner.invoke(cli, ['reset'], input='y\n')
            self.assertEqual(result.exit_code, 0)
            self.assertIn('reset', result.output.lower())


if __name__ == '__main__':
    import unittest
    unittest.main()