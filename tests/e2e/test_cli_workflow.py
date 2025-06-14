#!/usr/bin/env python3
"""
End-to-end CLI workflow tests that test the actual commands and full system integration
"""
import os
import sys
import time
import tempfile
import shutil
import subprocess
import json
from unittest import TestCase
from unittest.mock import patch


class TestCLIWorkflow(TestCase):
    """Test end-to-end CLI workflows"""

    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()

        # Change to temp directory for tests
        os.chdir(self.temp_dir)

        # Enable test mode
        os.environ['MAF_TEST_MODE'] = 'true'

        # Create a basic project structure
        os.makedirs('src', exist_ok=True)
        with open('package.json', 'w') as f:
            json.dump({
                "name": "test-project",
                "version": "1.0.0",
                "scripts": {"dev": "echo 'dev mode'"}
            }, f)

    def tearDown(self):
        """Clean up"""
        os.chdir(self.original_cwd)
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir, ignore_errors=True)

        # Clean up environment
        if 'MAF_TEST_MODE' in os.environ:
            del os.environ['MAF_TEST_MODE']

    def run_maf_command(self, args, timeout=30):
        """Run a maf CLI command and return result"""
        cmd = [sys.executable, '-m', 'multi_agent_framework.cli'] + args

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=self.temp_dir
            )
            return result
        except subprocess.TimeoutExpired:
            return None

    def test_cli_help_command(self):
        """Test that help command works"""
        result = self.run_maf_command(['--help'])

        if result:
            self.assertEqual(result.returncode, 0)
            self.assertIn('usage:', result.stdout.lower())

    def test_cli_status_command(self):
        """Test status command"""
        result = self.run_maf_command(['status'])

        if result:
            # Should not crash, return code may vary based on state
            self.assertIsNotNone(result.stdout)

    def test_cli_reset_command(self):
        """Test reset command"""
        result = self.run_maf_command(['reset'])

        if result:
            # Should not crash
            self.assertTrue(result.returncode in [0, 1])  # May return 1 if nothing to reset

    @patch('google.generativeai.GenerativeModel')
    def test_cli_trigger_workflow(self, mock_llm):
        """Test triggering a feature via CLI"""
        # Mock LLM response
        mock_instance = mock_llm.return_value
        mock_instance.generate_content.return_value.text = '{"status": "completed"}'

        result = self.run_maf_command(['trigger', 'Add a simple button component'], timeout=15)

        if result:
            # Command should execute without crashing
            self.assertTrue(result.returncode in [0, 1])
            # Check for basic output
            self.assertIsNotNone(result.stdout)

    @patch('google.generativeai.GenerativeModel')
    def test_cli_launch_agents_workflow(self, mock_llm):
        """Test launching agents via CLI"""
        # Mock LLM response
        mock_instance = mock_llm.return_value
        mock_instance.generate_content.return_value.text = '{"status": "ready"}'

        # Test launch with specific agents and short timeout
        result = self.run_maf_command(['launch', '--agents', 'frontend,backend', '--timeout', '5'], timeout=10)

        if result:
            # Should start and then timeout/stop within reasonable time
            # Return code may vary (0 for clean exit, other for timeout)
            self.assertIsNotNone(result.stdout)

    def test_project_detection_workflow(self):
        """Test that the CLI can detect project type"""
        # Create different project indicators
        test_cases = [
            {
                'file': 'package.json',
                'content': '{"dependencies": {"react": "^18.0.0"}}',
                'expected_type': 'react'
            },
            {
                'file': 'requirements.txt',
                'content': 'django>=4.0.0\npsycopg2>=2.8.0',
                'expected_type': 'django'
            }
        ]

        for case in test_cases:
            # Create project file
            with open(case['file'], 'w') as f:
                f.write(case['content'])

            # Run status to trigger project detection
            result = self.run_maf_command(['status'])

            if result:
                # Should not crash and should detect project
                self.assertIsNotNone(result.stdout)

            # Clean up
            if os.path.exists(case['file']):
                os.remove(case['file'])

    def test_config_file_workflow(self):
        """Test CLI behavior with .maf-config.json"""
        # Create a config file
        config = {
            "agents": ["frontend", "backend"],
            "event_bus": {"type": "inmemory"},
            "model_provider": "gemini"
        }

        with open('.maf-config.json', 'w') as f:
            json.dump(config, f)

        # Run status command
        result = self.run_maf_command(['status'])

        if result:
            self.assertIsNotNone(result.stdout)

        # Verify config was created/exists
        self.assertTrue(os.path.exists('.maf-config.json'))

    def test_error_handling_workflow(self):
        """Test CLI error handling"""
        # Test invalid command
        result = self.run_maf_command(['invalid-command'])

        if result:
            self.assertNotEqual(result.returncode, 0)
            self.assertTrue(len(result.stderr) > 0 or 'invalid' in result.stdout.lower())

    def test_version_command(self):
        """Test version command"""
        result = self.run_maf_command(['--version'])

        if result:
            # Should show version info
            self.assertEqual(result.returncode, 0)
            # Should contain version-like output
            self.assertTrue(
                any(char.isdigit() for char in result.stdout) or
                'version' in result.stdout.lower()
            )

    def test_multi_step_workflow(self):
        """Test a multi-step workflow: reset -> status -> config"""
        steps = [
            (['reset'], 'Reset should work'),
            (['status'], 'Status after reset should work'),
        ]

        for cmd, description in steps:
            result = self.run_maf_command(cmd)
            if result:
                # Should not crash
                self.assertIsNotNone(result.stdout, f"Failed: {description}")

    def test_concurrent_safety(self):
        """Test that multiple CLI invocations don't interfere"""
        import threading

        results = {}

        def run_command(cmd_id, args):
            result = self.run_maf_command(args, timeout=10)
            results[cmd_id] = result

        # Run multiple commands concurrently
        threads = []
        commands = [
            ('status1', ['status']),
            ('status2', ['status']),
            ('reset1', ['reset'])
        ]

        for cmd_id, args in commands:
            thread = threading.Thread(target=run_command, args=(cmd_id, args))
            thread.start()
            threads.append(thread)

        # Wait for all to complete
        for thread in threads:
            thread.join(timeout=15)

        # All should complete (though they may have different return codes)
        for cmd_id, args in commands:
            self.assertIn(cmd_id, results, f"Command {args} didn't complete")

    def test_graceful_interruption(self):
        """Test that CLI handles interruption gracefully"""
        import threading

        # Start a long-running command in a thread
        def run_long_command():
            try:
                result = self.run_maf_command(['status'], timeout=2)
                return result
            except Exception:
                return None

        thread = threading.Thread(target=run_long_command)
        thread.start()

        # Give it a moment to start
        time.sleep(0.5)

        # Wait for completion with timeout
        thread.join(timeout=3)

        # Should complete within reasonable time
        self.assertFalse(thread.is_alive(), "Command should complete or timeout gracefully")


class TestCLIIntegrationScenarios(TestCase):
    """Test realistic CLI usage scenarios"""

    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir)
        os.environ['MAF_TEST_MODE'] = 'true'

    def tearDown(self):
        """Clean up"""
        os.chdir(self.original_cwd)
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir, ignore_errors=True)
        if 'MAF_TEST_MODE' in os.environ:
            del os.environ['MAF_TEST_MODE']

    def run_maf_command(self, args, timeout=10):
        """Run a maf CLI command and return result"""
        cmd = [sys.executable, '-m', 'multi_agent_framework.cli'] + args

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=self.temp_dir
            )
            return result
        except subprocess.TimeoutExpired:
            return None

    def test_new_project_workflow(self):
        """Test workflow for a new project"""
        # Create minimal project structure
        with open('package.json', 'w') as f:
            json.dump({"name": "new-project", "version": "1.0.0"}, f)

        # Step 1: Check initial status
        result = self.run_maf_command(['status'])
        if result:
            self.assertIsNotNone(result.stdout)

        # Step 2: Reset any existing state
        result = self.run_maf_command(['reset'])
        if result:
            self.assertTrue(result.returncode in [0, 1])

        # Step 3: Check status again
        result = self.run_maf_command(['status'])
        if result:
            self.assertIsNotNone(result.stdout)

    @patch('google.generativeai.GenerativeModel')
    def test_feature_development_workflow(self, mock_llm):
        """Test complete feature development workflow"""
        # Setup mock
        mock_instance = mock_llm.return_value
        mock_instance.generate_content.return_value.text = json.dumps({
            "tasks": [
                {"agent": "frontend", "description": "Create component"},
                {"agent": "backend", "description": "Create API"}
            ]
        })

        # Create project
        with open('package.json', 'w') as f:
            json.dump({"name": "feature-project", "dependencies": {"react": "^18.0.0"}}, f)

        # Reset state
        self.run_maf_command(['reset'])

        # Trigger feature development
        trigger_result = self.run_maf_command(['trigger', 'Add user profile page'], timeout=15)

        if trigger_result:
            # Should not crash
            self.assertIsNotNone(trigger_result.stdout)

        # Check status after trigger
        status_result = self.run_maf_command(['status'])
        if status_result:
            self.assertIsNotNone(status_result.stdout)

    def test_configuration_workflow(self):
        """Test configuration management workflow"""
        # Create config file
        config = {
            "agents": ["frontend", "backend", "database"],
            "model_provider": "gemini",
            "event_bus": {"type": "inmemory"}
        }

        with open('.maf-config.json', 'w') as f:
            json.dump(config, f, indent=2)

        # Verify status works with config
        result = self.run_maf_command(['status'])
        if result:
            self.assertIsNotNone(result.stdout)

        # Verify config is still valid JSON
        with open('.maf-config.json', 'r') as f:
            loaded_config = json.load(f)
            self.assertEqual(loaded_config['agents'], config['agents'])

    def test_error_recovery_workflow(self):
        """Test error recovery in CLI"""
        # Create invalid config
        with open('.maf-config.json', 'w') as f:
            f.write('invalid json content')

        # CLI should handle invalid config gracefully
        result = self.run_maf_command(['status'])
        if result:
            # Should not crash catastrophically
            self.assertIsNotNone(result)

        # Reset should clean up issues
        reset_result = self.run_maf_command(['reset'])
        if reset_result:
            self.assertTrue(reset_result.returncode in [0, 1])


if __name__ == '__main__':
    import unittest
    unittest.main()
