# Testing Guide

This guide covers testing practices and procedures for the Multi-Agent Framework.

## Test Organization

Tests are organized into three categories in the `/tests/` directory:

### Unit Tests (`/tests/unit/`)

Unit tests for individual components in isolation:
- `test_agent_communication.py` - Basic message bus and agent communication tests
- `test_error_handling.py` - Error handling and recovery tests
- `test_event_driven_simple.py` - Simple event-driven functionality tests
- `test_kafka_event_bus.py` - Kafka event bus implementation tests
- `test_simple_orchestrator.py` - Orchestrator agent unit tests

### Integration Tests (`/tests/integration/`)

Integration tests for multiple components working together:
- `test_agent_communication_full.py` - Comprehensive agent communication tests
- `test_enhanced_agents.py` - Enhanced agent capabilities tests
- `test_event_driven_agents.py` - Event-driven agent system tests
- `test_event_driven_agents_full.py` - Full event-driven workflow tests
- `test_event_driven_integration.py` - Complete event-driven integration tests
- `test_framework.py` - Framework-wide integration tests
- `test_working_flow.py` - Complete workflow integration tests

### End-to-End Tests (`/tests/e2e/`)

End-to-end tests for complete system workflows:
- `test_feature_with_debug.py` - Feature development with debugging
- `test_real_feature.py` - Real feature implementation tests

## Running Tests

### Basic Commands

```bash
# Run all tests
pytest tests/

# Run only unit tests
pytest tests/unit/

# Run only integration tests
pytest tests/integration/

# Run only e2e tests
pytest tests/e2e/

# Run a specific test file
pytest tests/unit/test_error_handling.py

# Run with coverage
pytest tests/ --cov=multi_agent_framework

# Run with markers
pytest tests/ -m unit
pytest tests/ -m integration
pytest tests/ -m e2e
```

### Test Mode

The framework supports a test mode that mocks LLM calls:

```bash
# Enable test mode
export MAF_TEST_MODE=true
pytest tests/
```

### Coverage Reports

```bash
# Generate HTML coverage report
pytest tests/ --cov=multi_agent_framework --cov-report=html

# View coverage report
open htmlcov/index.html
```

## Writing Tests

### Test Structure

```python
import pytest
from multi_agent_framework.agents.base_agent import BaseAgent

class TestBaseAgent:
    @pytest.fixture
    def agent(self):
        return BaseAgent("test_agent")
    
    def test_agent_initialization(self, agent):
        assert agent.name == "test_agent"
        assert agent.state == "idle"
```

### Mocking LLM Calls

```python
import os
os.environ["MAF_TEST_MODE"] = "true"

# LLM calls will be automatically mocked
```

### Testing Event-Driven Agents

```python
import asyncio
from multi_agent_framework.core.event_bus import InMemoryEventBus
from multi_agent_framework.agents.event_driven_orchestrator_agent import EventDrivenOrchestratorAgent

async def test_event_driven_agent():
    event_bus = InMemoryEventBus()
    agent = EventDrivenOrchestratorAgent(event_bus)
    
    # Publish event
    await event_bus.publish({
        "event_type": "TASK_CREATED",
        "payload": {"task": "test task"}
    })
    
    # Allow processing
    await asyncio.sleep(0.1)
    
    # Assert results
    assert agent.processed_tasks == 1
```

## Test Configuration

### pytest.ini

The `pytest.ini` file contains test configuration:

```ini
[pytest]
addopts = -v --tb=short
testpaths = tests
markers =
    unit: Unit tests
    integration: Integration tests
    e2e: End-to-end tests
    slow: Slow running tests
    requires_kafka: Tests requiring Kafka
```

### conftest.py

Common fixtures and test setup are defined in `tests/conftest.py`.

## Continuous Integration

Tests run automatically on GitHub Actions for:
- Every push to main
- Every pull request
- Python versions: 3.10, 3.11, 3.12, 3.13

## Best Practices

1. **Test Isolation**: Each test should be independent
2. **Clear Names**: Use descriptive test names that explain what is being tested
3. **Arrange-Act-Assert**: Follow the AAA pattern
4. **Mock External Services**: Always mock API calls in tests
5. **Test Edge Cases**: Include tests for error conditions
6. **Keep Tests Fast**: Use test mode to avoid real API calls
7. **Test Documentation**: Include docstrings explaining complex tests