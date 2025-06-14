# Test Improvement Plan

## Current Status (as of January 14, 2025)

### Test Results Summary
- **Total Tests**: 118
- **Passed**: 60 (unit tests)
- **Failed**: 11  
- **Skipped**: 10 (Kafka tests)
- **Current Coverage**: ~4% (Critical!)

### Key Issues
1. **Extremely Low Coverage** - Only 4% of codebase is tested
2. **Agent Code Not Tested** - 0% coverage for all agent implementations
3. **Core Components Untested** - Many critical components have 0% coverage
4. **Test Failures** - 11 failing tests need fixes

## Failing Tests Analysis

### 1. Test Return Value Issues (3 tests)
**Files**: `test_agent_communication.py`
- `test_message_bus` - Using `return True` instead of assertions
- `test_project_state` - Using `return True` instead of assertions  
- `test_agent_import` - Using `return True` instead of assertions

**Fix**: Replace `return True` with proper `assert` statements

### 2. CLI Test Failures (5 tests)
**Files**: `test_cli.py`, `test_cli_scenarios.py`
- `test_reset_command` - Looking for wrong output string
- `test_status_command` - Exit code 2 (missing _get_recommended_agents import)
- `test_config_nested_operations` - Config command not fully implemented
- `test_full_workflow` - Config command issues
- `test_reinit_existing_project` - Should fail but passes

**Fix**: Update expected outputs and fix missing imports

### 3. Orchestrator Test Failure (1 test)
**File**: `test_simple_orchestrator.py`
- `test_orchestrator` - KeyError: 'test-123' in features dict

**Fix**: Initialize features dict properly before testing

### 4. JSON Handling Issues (2 tests)
- `test_invalid_json_handling` - Error message format changed
- `test_error_recovery` - Warning message instead of error

**Fix**: Update expected error messages

## Coverage Improvement Plan

### Phase 1: Fix Failing Tests (Target: 1 day)
1. Fix test return value issues in `test_agent_communication.py`
2. Update CLI test expectations to match current output
3. Fix orchestrator test initialization
4. Update error message expectations

### Phase 2: Core Component Tests (Target: 80% coverage, 3 days)

#### High Priority Components (0% → 80%)
1. **Agent Factory** (31% → 80%)
   - Test all agent creation paths
   - Test error handling
   - Test mode selection

2. **Message Bus** (0% → 80%)
   - Test message sending/receiving
   - Test queue initialization
   - Test error cases

3. **Project Config** (0% → 80%)
   - Test config loading/saving
   - Test project type detection
   - Test default values

4. **Event Bus** (0% → 80%)
   - Test in-memory implementation
   - Test publish/subscribe
   - Test event filtering

#### Medium Priority Components
5. **Progress Tracker** (Already good coverage)
6. **Error Handler** (Already good coverage)
7. **CLI Commands** (58% → 80%)
   - Test all command variations
   - Test error paths

### Phase 3: Agent Tests (Target: 60% coverage, 5 days)

#### Base Agent Classes
1. **EventDrivenBaseAgent** (0% → 60%)
   - Mock LLM calls
   - Test message handling
   - Test lifecycle methods

2. **BaseAgent** (0% → 60%)
   - Test polling mechanism
   - Test state management

#### Specialized Agents (0% → 40% each)
For each agent type, create:
- Basic initialization tests
- Message handling tests
- Task execution tests (with mocked LLMs)

### Phase 4: Integration Tests (Target: 2 days)
1. Fix hanging integration tests
2. Add timeout decorators
3. Mock external dependencies

## Implementation Strategy

### 1. Test Infrastructure Improvements
```python
# conftest.py additions
@pytest.fixture
def mock_llm():
    """Mock LLM for agent tests"""
    with patch('google.generativeai.GenerativeModel') as mock:
        mock.return_value.generate_content.return_value.text = '{"result": "test"}'
        yield mock

@pytest.fixture
def test_event_bus():
    """Isolated event bus for testing"""
    # Implementation

@pytest.fixture
def test_agent_factory():
    """Factory with mocked dependencies"""
    # Implementation
```

### 2. Test File Organization
```
tests/
├── unit/
│   ├── core/
│   │   ├── test_agent_factory.py
│   │   ├── test_message_bus.py
│   │   ├── test_project_config.py
│   │   └── test_event_bus.py
│   ├── agents/
│   │   ├── test_base_agent.py
│   │   ├── test_event_driven_base.py
│   │   └── test_specialized_agents.py
│   └── cli/
│       └── (existing CLI tests)
└── integration/
    └── (existing integration tests)
```

### 3. Coverage Targets by Component

| Component | Current | Target | Priority |
|-----------|---------|--------|----------|
| cli.py | 58% | 80% | High |
| agent_factory.py | 31% | 80% | High |
| message_bus.py | 0% | 80% | High |
| project_config.py | 0% | 80% | High |
| event_bus.py | 0% | 80% | High |
| base_agent.py | 0% | 60% | Medium |
| event_driven_base_agent.py | 0% | 60% | Medium |
| orchestrator_agent.py | 0% | 60% | Medium |
| specialized agents | 0% | 40% | Low |

## Success Metrics
- All tests passing (0 failures)
- Overall coverage ≥ 80%
- Core components coverage ≥ 80%
- Agent base classes coverage ≥ 60%
- CI/CD pipeline stable with all Python versions

## Next Steps
1. Fix the 11 failing tests
2. Add core component tests
3. Add agent base class tests
4. Monitor coverage improvements
5. Add missing integration tests