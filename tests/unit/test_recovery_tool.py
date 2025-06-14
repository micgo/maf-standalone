#!/usr/bin/env python3
"""
Tests for recovery tool functionality
"""
import os
import json
import sys
from unittest import TestCase, mock
from unittest.mock import Mock, patch, MagicMock
from io import StringIO

import multi_agent_framework.recovery_tool as recovery_tool


class TestRecoveryTool(TestCase):
    """Test recovery tool functions"""
    
    def setUp(self):
        """Set up test environment"""
        self.mock_state_manager = Mock()
        
    def test_print_header(self):
        """Test header printing"""
        with patch('sys.stdout', new=StringIO()) as fake_out:
            recovery_tool.print_header("TEST HEADER")
            output = fake_out.getvalue()
            
            self.assertIn("TEST HEADER", output)
            self.assertIn("="*60, output)
    
    def test_health_check_healthy_system(self):
        """Test health check with healthy system"""
        # Mock healthy system
        self.mock_state_manager.task_health_check.return_value = {
            'healthy': True,
            'total_tasks': 10,
            'status_counts': {
                'completed': 8,
                'in_progress': 2,
                'pending': 0,
                'failed': 0
            },
            'stalled_tasks': [],
            'failed_tasks': [],
            'long_running_tasks': []
        }
        
        self.mock_state_manager.get_task_statistics.return_value = {
            'total_tasks': 10,
            'by_status': {'completed': 8, 'in_progress': 2},
            'completion_rate': 0.8,
            'average_retry_count': 0.2,
            'tasks_with_errors': 0
        }
        
        with patch('sys.stdout', new=StringIO()) as fake_out:
            recovery_tool.health_check(self.mock_state_manager)
            output = fake_out.getvalue()
            
            self.assertIn("🟢 HEALTHY", output)
            self.assertIn("Total Tasks: 10", output)
            self.assertIn("✅", output)  # completed emoji
    
    def test_health_check_unhealthy_system(self):
        """Test health check with issues"""
        # Mock unhealthy system
        self.mock_state_manager.task_health_check.return_value = {
            'healthy': False,
            'total_tasks': 10,
            'status_counts': {
                'completed': 5,
                'in_progress': 2,
                'failed': 3
            },
            'stalled_tasks': [
                {
                    'task_id': 'task-1234-5678-9abc',
                    'agent': 'frontend_agent',
                    'description': 'Create user authentication flow with OAuth support',
                    'started_at': '2024-01-01 10:00:00'
                }
            ],
            'failed_tasks': [
                {
                    'task_id': 'task-2345-6789-0def',
                    'description': 'Setup database connection pool',
                    'error': 'Connection timeout',
                    'retry_count': 2
                }
            ],
            'long_running_tasks': []
        }
        
        self.mock_state_manager.get_task_statistics.return_value = {
            'total_tasks': 10,
            'by_status': {'completed': 5, 'failed': 3, 'in_progress': 2},
            'completion_rate': 0.5,
            'average_retry_count': 1.5,
            'tasks_with_errors': 3
        }
        
        with patch('sys.stdout', new=StringIO()) as fake_out:
            recovery_tool.health_check(self.mock_state_manager)
            output = fake_out.getvalue()
            
            self.assertIn("🔴 ISSUES DETECTED", output)
            self.assertIn("failed", output.lower())
    
    def test_show_agent_status(self):
        """Test showing agent status"""
        self.mock_state_manager.get_task_statistics.return_value = {
            'by_agent': {
                'frontend_agent': 5,
                'backend_agent': 3,
                'db_agent': 0
            }
        }
        self.mock_state_manager.get_pending_tasks_by_agent.side_effect = lambda agent: {
            'frontend_agent': [{'description': 'Task 1'}, {'description': 'Task 2'}],
            'backend_agent': [{'description': 'Task 3'}],
            'db_agent': []
        }.get(agent, [])
        
        with patch('sys.stdout', new=StringIO()) as fake_out:
            recovery_tool.show_agent_status(self.mock_state_manager)
            output = fake_out.getvalue()
            
            self.assertIn("frontend_agent", output)
            self.assertIn("5 total tasks", output)
            self.assertIn("2 pending", output)
    
    def test_retry_failed(self):
        """Test retrying failed tasks"""
        self.mock_state_manager.retry_failed_tasks.return_value = [
            'task-3456-7890-1abc'
        ]
        self.mock_state_manager.get_task.side_effect = lambda task_id: {
            'task-3456-7890-1abc': {
                'description': 'Initialize database migrations for user table',
                'agent': 'db_agent'
            }
        }.get(task_id)
        
        with patch('sys.stdout', new=StringIO()) as fake_out:
            recovery_tool.retry_failed(self.mock_state_manager, max_retries=3)
            output = fake_out.getvalue()
            
            self.assertIn("Successfully retried 1 failed tasks", output)
            self.assertIn("task-345", output)  # Only first 8 chars shown
            self.assertIn("Initialize database", output)
    
    def test_recover_stalled(self):
        """Test recovering stalled tasks"""
        self.mock_state_manager.recover_stalled_tasks.return_value = [
            'task-1234-5678-9abc',
            'task-2345-6789-0def'
        ]
        self.mock_state_manager.get_task.side_effect = lambda task_id: {
            'task-1234-5678-9abc': {
                'description': 'Create user authentication flow with OAuth support',
                'agent': 'frontend_agent'
            },
            'task-2345-6789-0def': {
                'description': 'Setup database connection pool for high availability',
                'agent': 'backend_agent'
            }
        }.get(task_id)
        
        with patch('sys.stdout', new=StringIO()) as fake_out:
            recovery_tool.recover_stalled(self.mock_state_manager, timeout_minutes=30)
            output = fake_out.getvalue()
                
            self.assertIn("Successfully recovered 2 stalled tasks", output)
            self.assertIn("task-123", output)  # Only first 8 chars shown
            self.assertIn("task-234", output)  # Only first 8 chars shown
            self.assertIn("Create user authentication", output)
    
    def test_full_recovery(self):
        """Test full recovery process"""
        # Mock various recovery operations
        self.mock_state_manager.task_health_check.return_value = {
            'healthy': False,
            'total_tasks': 10,
            'status_counts': {'failed': 2, 'stalled': 3}
        }
        self.mock_state_manager.recover_stalled_tasks.return_value = [
            {'id': 'task-1', 'agent': 'frontend_agent'},
            {'id': 'task-2', 'agent': 'backend_agent'}
        ]
        self.mock_state_manager.retry_failed_tasks.return_value = [
            {'id': 'task-3', 'agent': 'db_agent'}
        ]
        self.mock_state_manager.cleanup_completed_tasks.return_value = 5
        
        with patch('sys.stdout', new=StringIO()) as fake_out:
            recovery_tool.full_recovery(self.mock_state_manager)
            output = fake_out.getvalue()
                
            self.assertIn("FULL SYSTEM RECOVERY", output)
            self.assertIn("Stalled tasks recovered: 2", output)
            self.assertIn("Failed tasks retried: 1", output)
            self.assertIn("Old tasks cleaned: 5", output)
            self.assertIn("8 total actions performed", output)
    
    def test_full_recovery_healthy_system(self):
        """Test full recovery when system is healthy"""
        self.mock_state_manager.task_health_check.return_value = {
            'healthy': True,
            'total_tasks': 10,
            'status_counts': {'completed': 10}
        }
        
        with patch('sys.stdout', new=StringIO()) as fake_out:
            recovery_tool.full_recovery(self.mock_state_manager)
            output = fake_out.getvalue()
            
            self.assertIn("System is healthy", output)
            # Should not call recovery methods
            self.mock_state_manager.recover_stalled_tasks.assert_not_called()
            self.mock_state_manager.retry_failed_tasks.assert_not_called()
    
    def test_cleanup_old_tasks(self):
        """Test cleaning up old completed tasks"""
        self.mock_state_manager.cleanup_completed_tasks.return_value = 25
        
        with patch('sys.stdout', new=StringIO()) as fake_out:
            recovery_tool.cleanup_old_tasks(self.mock_state_manager, keep_days=7)
            output = fake_out.getvalue()
                
            self.assertIn("cleaned up 25 old tasks", output)
            self.mock_state_manager.cleanup_completed_tasks.assert_called_with(7)
    
    def test_main_function_with_args(self):
        """Test main function with command line arguments"""
        # Test retry command
        test_args = ['recovery_tool.py', 'retry']
        
        with patch('sys.argv', test_args):
            with patch('multi_agent_framework.recovery_tool.ProjectStateManager') as mock_psm:
                mock_psm.return_value = self.mock_state_manager
                self.mock_state_manager.retry_failed_tasks.return_value = []
                
                with patch('sys.stdout', new=StringIO()):
                    recovery_tool.main()
                    
                    # Verify retry was attempted
                    self.mock_state_manager.retry_failed_tasks.assert_called()
    
    def test_main_function_health_command(self):
        """Test main function with health command"""
        test_args = ['recovery_tool.py', 'health']
        
        with patch('sys.argv', test_args):
            with patch('multi_agent_framework.recovery_tool.ProjectStateManager') as mock_psm:
                mock_psm.return_value = self.mock_state_manager
                self.mock_state_manager.task_health_check.return_value = {
                    'healthy': True,
                    'total_tasks': 0,
                    'status_counts': {},
                    'stalled_tasks': [],
                    'failed_tasks': [],
                    'long_running_tasks': []
                }
                self.mock_state_manager.get_task_statistics.return_value = {
                    'total_tasks': 0,
                    'completion_rate': 0,
                    'average_retry_count': 0,
                    'tasks_with_errors': 0
                }
                
                with patch('sys.stdout', new=StringIO()):
                    # Should not raise exception
                    recovery_tool.main()
                    
                    # Verify health check was called
                    self.mock_state_manager.task_health_check.assert_called()
    
    def test_main_function_recover_command(self):
        """Test main function with recover command"""
        test_args = ['recovery_tool.py', 'recover']
        
        with patch('sys.argv', test_args):
            with patch('multi_agent_framework.recovery_tool.ProjectStateManager') as mock_psm:
                mock_psm.return_value = self.mock_state_manager
                self.mock_state_manager.recover_stalled_tasks.return_value = []
                
                with patch('sys.stdout', new=StringIO()) as fake_out:
                    recovery_tool.main()
                    output = fake_out.getvalue()
                    
                    self.assertIn("No stalled tasks", output)
    
    def test_cleanup_old_tasks_empty(self):
        """Test cleanup when no old tasks exist"""
        self.mock_state_manager.cleanup_completed_tasks.return_value = 0
        
        with patch('sys.stdout', new=StringIO()) as fake_out:
            recovery_tool.cleanup_old_tasks(self.mock_state_manager, keep_days=30)
            output = fake_out.getvalue()
            
            self.assertIn("No old tasks to clean up", output)
    
    def test_stalled_task_recovery_with_errors(self):
        """Test recovery handling when some tasks fail to recover"""
        # Return one recovered task
        self.mock_state_manager.recover_stalled_tasks.return_value = [
            'task-1234-5678-9abc'
        ]
        self.mock_state_manager.get_task.return_value = {
            'description': 'Create user authentication flow',
            'agent': 'frontend_agent'
        }
        
        with patch('sys.stdout', new=StringIO()) as fake_out:
            recovery_tool.recover_stalled(self.mock_state_manager)
            output = fake_out.getvalue()
            
            self.assertIn("Successfully recovered 1 stalled tasks", output)
    
    def test_agent_status_no_agents(self):
        """Test showing agent status when no agents exist"""
        self.mock_state_manager.get_task_statistics.return_value = {
            'by_agent': {}
        }
        self.mock_state_manager.get_pending_tasks_by_agent.return_value = []
        
        with patch('sys.stdout', new=StringIO()) as fake_out:
            recovery_tool.show_agent_status(self.mock_state_manager)
            output = fake_out.getvalue()
            
            self.assertIn("No agent data", output)


if __name__ == '__main__':
    import unittest
    unittest.main()