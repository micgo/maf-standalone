#!/usr/bin/env python3
"""
Tests for the progress tracking system
"""
import os
import sys
import time
import tempfile
import shutil
from unittest import TestCase
from click.testing import CliRunner

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from multi_agent_framework.core.progress_tracker import ProgressTracker


class TestProgressTracker(TestCase):
    """Test progress tracking functionality"""
    
    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.state_file = os.path.join(self.temp_dir, "test_state.json")
        self.tracker = ProgressTracker(self.state_file)
        
    def tearDown(self):
        """Clean up test environment"""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
            
    def test_create_feature(self):
        """Test creating a feature"""
        self.tracker.create_feature("feat-1", "Add user authentication")
        
        # Check state was saved
        state = self.tracker._load_state()
        self.assertIn("feat-1", state['features'])
        
        feature = state['features']['feat-1']
        self.assertEqual(feature['description'], "Add user authentication")
        self.assertEqual(feature['status'], 'pending')
        self.assertEqual(feature['progress'], 0)
        
    def test_create_task(self):
        """Test creating a task"""
        # Create feature first
        self.tracker.create_feature("feat-1", "Add user authentication")
        
        # Create task
        self.tracker.create_task("task-1", "feat-1", "Create login form", "frontend_agent")
        
        # Check state
        state = self.tracker._load_state()
        self.assertIn("task-1", state['tasks'])
        
        task = state['tasks']['task-1']
        self.assertEqual(task['feature_id'], "feat-1")
        self.assertEqual(task['description'], "Create login form")
        self.assertEqual(task['assigned_agent'], "frontend_agent")
        self.assertEqual(task['status'], 'pending')
        
        # Check task was added to feature
        feature = state['features']['feat-1']
        self.assertIn("task-1", feature['tasks'])
        
    def test_update_task_progress(self):
        """Test updating task progress"""
        # Setup
        self.tracker.create_feature("feat-1", "Add user authentication")
        self.tracker.create_task("task-1", "feat-1", "Create login form", "frontend_agent")
        
        # Update progress
        self.tracker.update_task_status("task-1", "in_progress", 50)
        
        # Check
        state = self.tracker._load_state()
        task = state['tasks']['task-1']
        self.assertEqual(task['status'], 'in_progress')
        self.assertEqual(task['progress'], 50)
        
        # Feature should also show progress
        feature = state['features']['feat-1']
        self.assertEqual(feature['progress'], 50)
        self.assertEqual(feature['status'], 'in_progress')
        
    def test_complete_task(self):
        """Test completing a task"""
        # Setup
        self.tracker.create_feature("feat-1", "Add user authentication")
        self.tracker.create_task("task-1", "feat-1", "Create login form", "frontend_agent")
        
        # Complete task
        self.tracker.update_task_status("task-1", "completed", 100)
        
        # Check
        state = self.tracker._load_state()
        task = state['tasks']['task-1']
        self.assertEqual(task['status'], 'completed')
        self.assertEqual(task['progress'], 100)
        
        # Feature should be completed too (only one task)
        feature = state['features']['feat-1']
        self.assertEqual(feature['progress'], 100)
        self.assertEqual(feature['status'], 'completed')
        
    def test_multiple_tasks_progress(self):
        """Test progress calculation with multiple tasks"""
        # Setup
        self.tracker.create_feature("feat-1", "Add user authentication")
        self.tracker.create_task("task-1", "feat-1", "Create login form", "frontend_agent")
        self.tracker.create_task("task-2", "feat-1", "Create API endpoint", "backend_agent")
        self.tracker.create_task("task-3", "feat-1", "Create user model", "db_agent")
        
        # Update tasks
        self.tracker.update_task_status("task-1", "completed", 100)
        self.tracker.update_task_status("task-2", "in_progress", 50)
        self.tracker.update_task_status("task-3", "pending", 0)
        
        # Check feature progress (100 + 50 + 0) / 3 = 50
        state = self.tracker._load_state()
        feature = state['features']['feat-1']
        self.assertEqual(feature['progress'], 50)
        self.assertEqual(feature['status'], 'in_progress')
        
    def test_format_duration(self):
        """Test duration formatting"""
        self.assertEqual(self.tracker._format_duration(45), "45s")
        self.assertEqual(self.tracker._format_duration(90), "1m 30s")
        self.assertEqual(self.tracker._format_duration(3700), "1h 1m")
        
    def test_get_active_features_count(self):
        """Test getting active feature counts"""
        # No features
        active, total = self.tracker.get_active_features_count()
        self.assertEqual(active, 0)
        self.assertEqual(total, 0)
        
        # Add features
        self.tracker.create_feature("feat-1", "Feature 1")
        self.tracker.create_feature("feat-2", "Feature 2")
        self.tracker.create_feature("feat-3", "Feature 3")
        
        # Update some statuses
        state = self.tracker._load_state()
        state['features']['feat-1']['status'] = 'completed'
        state['features']['feat-2']['status'] = 'in_progress'
        self.tracker._save_state(state)
        
        # Check counts
        active, total = self.tracker.get_active_features_count()
        self.assertEqual(active, 2)  # pending + in_progress
        self.assertEqual(total, 3)
        
    def test_display_progress_cli(self):
        """Test progress display output"""
        # Setup some features and tasks
        self.tracker.create_feature("feat-1", "Add user authentication system with email verification")
        self.tracker.create_task("task-1", "feat-1", "Create login form", "frontend_agent")
        self.tracker.create_task("task-2", "feat-1", "Create API endpoint", "backend_agent")
        
        # Update progress
        self.tracker.update_task_status("task-1", "completed", 100)
        self.tracker.update_task_status("task-2", "in_progress", 60)
        
        # Test display (should not raise exceptions)
        runner = CliRunner()
        with runner.isolated_filesystem():
            # Create a test file
            tracker = ProgressTracker("test.json")
            tracker.create_feature("feat-1", "Test feature")
            tracker.create_task("task-1", "feat-1", "Test task", "test_agent")
            tracker.update_task_status("task-1", "in_progress", 50)
            
            # This should work without errors
            tracker.display_progress(detailed=True)


if __name__ == '__main__':
    import unittest
    unittest.main()