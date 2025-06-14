#!/usr/bin/env python3
"""
Test better default configuration
"""
import os
import sys
import tempfile
import shutil
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from multi_agent_framework.core.project_config import ProjectConfig


def test_default_mode():
    """Test that default mode is polling"""
    with tempfile.TemporaryDirectory() as temp_dir:
        config = ProjectConfig(temp_dir)
        assert config.get_default_mode() == "polling"
        print("✓ Default mode is polling")


def test_event_bus_type():
    """Test default event bus type"""
    with tempfile.TemporaryDirectory() as temp_dir:
        config = ProjectConfig(temp_dir)
        assert config.get_event_bus_type() == "in_memory"
        print("✓ Default event bus is in_memory")


def test_recommended_agents():
    """Test recommended agents function"""
    from multi_agent_framework.cli import _get_recommended_agents
    
    # Test different project types
    assert 'orchestrator' in _get_recommended_agents('nextjs')
    assert 'frontend_agent' in _get_recommended_agents('nextjs')
    assert 'backend_agent' in _get_recommended_agents('django')
    assert 'db_agent' in _get_recommended_agents('django')
    
    print("✓ Recommended agents work correctly")


def test_config_persistence():
    """Test that configuration persists correctly"""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create config
        config = ProjectConfig(temp_dir)
        config.update_config({
            "framework_config": {
                "default_mode": "event"
            }
        })
        
        # Load again
        config2 = ProjectConfig(temp_dir)
        assert config2.get_default_mode() == "event"
        print("✓ Configuration persists correctly")


if __name__ == "__main__":
    print("Testing better default configuration...")
    test_default_mode()
    test_event_bus_type()
    test_recommended_agents()
    test_config_persistence()
    print("\n✅ All tests passed!")