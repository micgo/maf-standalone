"""
Common test fixtures and configuration for all tests
"""
import os
import sys
import tempfile
import shutil
import pytest
from pathlib import Path

# Add parent directory to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Enable test mode globally
os.environ['MAF_TEST_MODE'] = 'true'


@pytest.fixture
def temp_project_dir():
    """Create a temporary project directory for testing"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    # Cleanup after test
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def mock_project_config(temp_project_dir):
    """Create a mock project configuration"""
    from multi_agent_framework.core.project_config import ProjectConfig
    return ProjectConfig(temp_project_dir)


@pytest.fixture
def in_memory_event_bus():
    """Create an in-memory event bus for testing"""
    from multi_agent_framework.core.event_bus_factory import get_event_bus, reset_event_bus
    reset_event_bus()
    bus = get_event_bus('inmemory')
    yield bus
    # Stop the bus after test
    bus.stop()
    reset_event_bus()


@pytest.fixture
def test_message_queue_dir(temp_project_dir):
    """Create a test message queue directory"""
    queue_dir = os.path.join(temp_project_dir, 'message_queue')
    os.makedirs(queue_dir, exist_ok=True)
    return queue_dir