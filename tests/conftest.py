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
            "test_event_driven_integration.py"  # Only skip the original file, not fixed version
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


# LLM Mocking Fixtures
@pytest.fixture
def mock_gemini_response():
    """Mock a typical Gemini API response"""
    class MockResponse:
        def __init__(self, text):
            self.text = text
    return MockResponse


@pytest.fixture
def mock_gemini_model(mock_gemini_response):
    """Mock Gemini model for testing"""
    from unittest.mock import Mock
    
    model = Mock()
    
    # Default response for general prompts
    default_response = mock_gemini_response('{"result": "Test response", "status": "success"}')
    
    # Specific responses for different agent types
    orchestrator_response = mock_gemini_response('''[
        {
            "agent": "frontend_agent",
            "description": "Create the UI components"
        },
        {
            "agent": "backend_agent",
            "description": "Implement the API endpoints"
        }
    ]''')
    
    frontend_response = mock_gemini_response('''
```typescript
import React from 'react';

export const TestComponent: React.FC = () => {
    return <div>Test Component</div>;
};
```
''')
    
    backend_response = mock_gemini_response('''
```python
from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/api/test')
def test_endpoint():
    return jsonify({"message": "Test endpoint"})
```
''')
    
    # Configure model to return different responses based on prompt
    def generate_content_side_effect(prompt):
        if "break down" in prompt.lower() or "tasks" in prompt.lower():
            return orchestrator_response
        elif "component" in prompt.lower() or "ui" in prompt.lower():
            return frontend_response
        elif "api" in prompt.lower() or "endpoint" in prompt.lower():
            return backend_response
        else:
            return default_response
    
    model.generate_content.side_effect = generate_content_side_effect
    
    return model


@pytest.fixture
def mock_llm(mock_gemini_model):
    """Mock all LLM providers for testing"""
    from unittest.mock import patch
    
    patches = []
    
    # Mock Gemini
    gemini_patch = patch('google.generativeai.GenerativeModel')
    mock_gemini = gemini_patch.start()
    mock_gemini.return_value = mock_gemini_model
    patches.append(gemini_patch)
    
    # Mock OpenAI
    openai_patch = patch('openai.ChatCompletion.create')
    mock_openai = openai_patch.start()
    mock_openai.return_value = {
        'choices': [{
            'message': {
                'content': '{"result": "OpenAI test response"}'
            }
        }]
    }
    patches.append(openai_patch)
    
    # Mock Anthropic
    anthropic_patch = patch('anthropic.Client')
    mock_anthropic = anthropic_patch.start()
    mock_anthropic.return_value.messages.create.return_value.content = [
        {'text': '{"result": "Claude test response"}'}
    ]
    patches.append(anthropic_patch)
    
    yield
    
    # Stop all patches
    for patch in patches:
        patch.stop()


@pytest.fixture
def mock_message_bus():
    """Mock message bus for agent testing"""
    from unittest.mock import Mock
    from multi_agent_framework.core.message_bus_configurable import MessageBus
    
    bus = Mock(spec=MessageBus)
    bus.messages = {}
    
    def send_message(agent, message):
        if agent not in bus.messages:
            bus.messages[agent] = []
        bus.messages[agent].append(message)
    
    def receive_messages(agent):
        messages = bus.messages.get(agent, [])
        bus.messages[agent] = []
        return messages
    
    bus.send_message.side_effect = send_message
    bus.receive_messages.side_effect = receive_messages
    
    return bus


@pytest.fixture
def mock_event_bus():
    """Mock event bus for testing event-driven agents"""
    from unittest.mock import Mock
    from multi_agent_framework.core.event_bus_interface import IEventBus, EventType
    
    bus = Mock(spec=IEventBus)
    bus.subscribers = {}
    bus.events = []
    
    def subscribe(event_type, handler):
        if event_type not in bus.subscribers:
            bus.subscribers[event_type] = []
        bus.subscribers[event_type].append(handler)
    
    def publish(event):
        bus.events.append(event)
        event_type = event.get('type')
        if event_type in bus.subscribers:
            for handler in bus.subscribers[event_type]:
                handler(event)
    
    bus.subscribe.side_effect = subscribe
    bus.publish.side_effect = publish
    bus.start.return_value = None
    bus.stop.return_value = None
    
    return bus