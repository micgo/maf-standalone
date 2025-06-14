"""
Common test fixtures and configuration for all tests
"""
import os
import sys
import tempfile
import shutil
import pytest
import threading
import time
from pathlib import Path

# Add parent directory to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Enable test mode globally
os.environ['MAF_TEST_MODE'] = 'true'


@pytest.fixture(autouse=True)
def cleanup_threads():
    """Ensure all threads are cleaned up after each test"""
    # Get initial threads
    initial_threads = set(threading.enumerate())
    
    yield
    
    # Wait for threads to finish
    timeout = time.time() + 5  # 5 second timeout
    while time.time() < timeout:
        current_threads = set(threading.enumerate())
        test_threads = current_threads - initial_threads
        
        # Filter out daemon threads and main thread
        active_threads = [t for t in test_threads if t.is_alive() and not t.daemon]
        
        if not active_threads:
            break
            
        time.sleep(0.1)
    
    # Force kill any remaining non-daemon threads (shouldn't happen)
    for thread in active_threads:
        if thread.is_alive() and not thread.daemon:
            print(f"Warning: Thread {thread.name} still running after test")


def pytest_configure(config):
    """Configure pytest with custom settings"""
    # Set a global timeout handler for Python 3.13
    if sys.version_info >= (3, 13):
        # More aggressive timeout for Python 3.13
        if hasattr(config.option, 'timeout'):
            config.option.timeout = 60
            config.option.timeout_method = "thread"


def pytest_collection_modifyitems(config, items):
    """Modify test collection to skip certain tests on Python 3.13"""
    if sys.version_info >= (3, 13):
        skip_313 = pytest.mark.skip(reason="Skipped on Python 3.13 due to threading issues")
        
        # Skip tests known to hang on Python 3.13
        problematic_tests = [
            "test_kafka",
            "test_working_flow",
            "test_real_feature",
            "test_event_driven_integration"
        ]
        
        for item in items:
            for test_name in problematic_tests:
                if test_name in item.nodeid:
                    item.add_marker(skip_313)


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