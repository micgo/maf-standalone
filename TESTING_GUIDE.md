# Multi-Agent Framework Testing Guide

## Quick Start

### Run All Tests
```bash
# Run all tests
python3 -m pytest tests/

# Run with coverage report
python3 -m pytest --cov=multi_agent_framework --cov-report=html tests/

# Run with coverage summary
python3 -m pytest --cov=multi_agent_framework --cov-report=term-missing tests/
```

### Run Specific Test Categories

#### Agent Tests
```bash
# All agent tests
python3 -m pytest tests/unit/agents/ -v

# Specific agent type
python3 -m pytest tests/unit/agents/test_event_driven_specialized_agents.py -v
```

#### Core Component Tests
```bash
# All core tests
python3 -m pytest tests/unit/core/ -v

# Specific components
python3 -m pytest tests/unit/core/test_project_state_manager.py -v
python3 -m pytest tests/unit/core/test_event_bus.py -v
```

#### Utility Tests
```bash
# Recovery tool
python3 -m pytest tests/unit/test_recovery_tool.py -v

# Error handler
python3 -m pytest tests/unit/core/test_error_handler.py -v
```

## Test Organization

### Unit Tests
Located in `tests/unit/`, organized by component:
- `agents/` - Agent implementation tests
- `core/` - Core infrastructure tests
- `cli/` - Command-line interface tests

### Integration Tests
Located in `tests/integration/`:
- `test_agent_communication_full.py` - Inter-agent communication
- `test_event_driven_agents.py` - Event-driven workflows
- `test_end_to_end_workflow.py` - Complete feature development

### Mock Infrastructure
- `tests/unit/agents/mock_llm.py` - Mock LLM for agent testing
- No real API calls made during testing

## Key Test Files

### High Coverage Components
1. **ProjectStateManager** (100%)
   - `tests/unit/core/test_project_state_manager.py`
   - 27 comprehensive tests

2. **Agents** (~80%)
   - `tests/unit/agents/test_event_driven_specialized_agents.py`
   - Tests all 9 specialized agents

3. **CLI** (78%)
   - `tests/unit/cli/test_cli.py`
   - `tests/unit/test_cli_enhanced.py`

### Recently Added Tests
1. **RecoveryTool** (~40%)
   - `tests/unit/test_recovery_tool.py`
   - 15 tests for task recovery

2. **ProjectAnalyzer** (~60%)
   - `tests/unit/core/test_project_analyzer.py`
   - 15 tests for project structure analysis

3. **CrossAgentValidator** (~35%)
   - `tests/unit/core/test_cross_agent_validator.py`
   - 19 tests for cross-agent validation

4. **ErrorHandler** (~40%)
   - `tests/unit/core/test_error_handler.py`
   - 10 tests for error handling

## Common Test Patterns

### Testing Agents with Mock LLM
```python
from tests.unit.agents.mock_llm import MockLLM

def test_agent():
    llm = MockLLM(responses=["Test response"])
    agent = MyAgent("test_agent", llm)
    result = agent.process_task(task)
    assert "Test response" in result
```

### Testing Event-Driven Components
```python
def test_event_handling():
    event_bus = InMemoryEventBus()
    agent = EventDrivenAgent("test", Mock(), event_bus)
    
    # Publish event
    event_bus.publish(Event(EventType.TASK_CREATED, {...}))
    
    # Process events
    agent.run_once()
```

### Testing with Mock State Manager
```python
def test_with_state():
    state_manager = Mock()
    state_manager.get_task.return_value = {
        "id": "task-123",
        "status": "pending"
    }
    
    # Test component using state manager
```

## Debugging Failed Tests

### Common Issues and Solutions

1. **API Mismatch**
   - Problem: Test calls method that doesn't exist
   - Solution: Check actual implementation for correct method names

2. **Mock Return Values**
   - Problem: Mock returns wrong type
   - Solution: Match return value to actual method signature

3. **Event Bus Type Issues**
   - Problem: String vs dict in event data
   - Solution: Ensure consistent event data types

4. **File Path Issues**
   - Problem: Tests fail on different systems
   - Solution: Use `pathlib.Path` and temporary directories

## Coverage Goals

### Current Status (43%+)
- ✅ Agents: Good coverage
- ✅ Core state management: Excellent coverage
- ✅ CLI: Good coverage
- ⚠️ Integration: Needs improvement
- ⚠️ SmartIntegrator: Low coverage

### Target: 80% Coverage
Priority areas for improvement:
1. SmartIntegrator implementation
2. FileIntegrator edge cases
3. Integration test fixes
4. End-to-end workflows

## Best Practices

1. **Use Mocks Appropriately**
   - Mock external dependencies (LLMs, APIs)
   - Don't mock the code under test

2. **Test Real Behavior**
   - Align tests with actual implementation
   - Verify return values match reality

3. **Isolate Tests**
   - Each test should be independent
   - Clean up resources in tearDown

4. **Clear Test Names**
   - Use descriptive test method names
   - Follow pattern: `test_component_scenario_expected`

5. **Assertions**
   - Test both success and failure cases
   - Verify side effects (logs, state changes)

## Continuous Integration

To add to CI/CD pipeline:
```yaml
# Example GitHub Actions
- name: Run tests with coverage
  run: |
    python -m pytest --cov=multi_agent_framework --cov-report=xml tests/
    
- name: Upload coverage
  uses: codecov/codecov-action@v3
  with:
    file: ./coverage.xml
```

## Contributing Tests

When adding new features:
1. Write tests first (TDD approach)
2. Ensure tests match actual implementation
3. Run coverage to verify improvement
4. Update this guide if adding new patterns