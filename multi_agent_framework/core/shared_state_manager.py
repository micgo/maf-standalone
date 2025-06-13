"""
Shared State Manager for Multi-Agent Framework

This module provides a singleton state manager that ensures all agents share the same state.
It wraps the ProjectStateManager to provide thread-safe access and synchronization.
"""

import threading
from typing import Optional
from .project_state_manager import ProjectStateManager


class SharedStateManager:
    """Singleton wrapper around ProjectStateManager to ensure all agents use the same instance."""
    
    _instance: Optional['SharedStateManager'] = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                # Double-check locking pattern
                if cls._instance is None:
                    cls._instance = super(SharedStateManager, cls).__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        # Ensure initialization only happens once
        if self._initialized:
            return
            
        with self._lock:
            if not self._initialized:
                self._state_manager = ProjectStateManager()
                self._initialized = True
                print("SharedStateManager: Initialized singleton instance")
    
    def get_state_manager(self) -> ProjectStateManager:
        """Get the shared ProjectStateManager instance."""
        return self._state_manager
    
    def synchronize(self):
        """Force reload of state from disk to ensure synchronization."""
        with self._lock:
            self._state_manager.state = self._state_manager._load_state(full_path=True)
            print("SharedStateManager: State synchronized from disk")
    
    def get_task(self, task_id):
        """Thread-safe task retrieval with synchronization."""
        with self._lock:
            # Reload state to ensure we have the latest
            self.synchronize()
            return self._state_manager.get_task(task_id)
    
    def update_task_status(self, task_id, status, output=None, error=None):
        """Thread-safe task status update."""
        with self._lock:
            self._state_manager.update_task_status(task_id, status, output, error)
    
    def add_task(self, task_id, feature_id, description, assigned_agent, status="pending"):
        """Thread-safe task addition."""
        with self._lock:
            self._state_manager.add_task(task_id, feature_id, description, assigned_agent, status)
    
    def increment_retry_count(self, task_id):
        """Thread-safe retry count increment."""
        with self._lock:
            return self._state_manager.increment_retry_count(task_id)
    
    def add_feature(self, feature_id, description, status="new"):
        """Thread-safe feature addition."""
        with self._lock:
            self._state_manager.add_feature(feature_id, description, status)
    
    def get_all_tasks(self):
        """Thread-safe retrieval of all tasks."""
        with self._lock:
            self.synchronize()
            return self._state_manager.get_all_tasks()
    
    def get_all_features(self):
        """Thread-safe retrieval of all features."""
        with self._lock:
            self.synchronize()
            return self._state_manager.get_all_features()


# Global shared state instance
shared_state = SharedStateManager()


def get_shared_state_manager() -> ProjectStateManager:
    """Get the global shared state manager instance."""
    return shared_state.get_state_manager()