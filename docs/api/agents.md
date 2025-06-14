# Agent API Reference

This document provides the API reference for all agents in the Multi-Agent Framework.

## Base Classes

### BaseAgent

```python
from multi_agent_framework.agents.base_agent import BaseAgent

class BaseAgent:
    def __init__(self, name: str, model_provider: str = "gemini", model_name: str = None)
    def process_message(self, message: Dict[str, Any]) -> Dict[str, Any]
    def run(self) -> None
```

### EventDrivenBaseAgent

```python
from multi_agent_framework.agents.event_driven_base_agent import EventDrivenBaseAgent

class EventDrivenBaseAgent:
    def __init__(self, event_bus: EventBus, name: str, role: str)
    async def start(self) -> None
    async def stop(self) -> None
    async def handle_event(self, event: Dict[str, Any]) -> None
    async def publish_event(self, event_type: str, payload: Dict[str, Any], target: str = None)
```

## Specialized Agents

### Orchestrator Agent

**Role**: Coordinates all other agents and manages task distribution.

```python
from multi_agent_framework.agents.orchestrator_agent import OrchestratorAgent

# Event-driven version
from multi_agent_framework.agents.event_driven_orchestrator_agent import EventDrivenOrchestratorAgent
```

**Capabilities**:
- Breaks down features into tasks
- Assigns tasks to appropriate agents
- Monitors progress and handles failures
- Manages task dependencies

### Frontend Agent

**Role**: Handles all frontend development tasks.

```python
from multi_agent_framework.agents.specialized.frontend_agent import FrontendAgent

# Event-driven version
from multi_agent_framework.agents.specialized.event_driven_frontend_agent import EventDrivenFrontendAgent
```

**Capabilities**:
- React/Next.js component development
- Vue.js and Angular support
- Responsive design implementation
- State management integration
- CSS/Tailwind styling

### Backend Agent

**Role**: Manages server-side logic and API development.

```python
from multi_agent_framework.agents.specialized.backend_agent import BackendAgent

# Event-driven version
from multi_agent_framework.agents.specialized.event_driven_backend_agent import EventDrivenBackendAgent
```

**Capabilities**:
- REST API development
- GraphQL endpoint creation
- Authentication/authorization
- Business logic implementation
- Database integration

### Database Agent

**Role**: Handles all database-related tasks.

```python
from multi_agent_framework.agents.specialized.db_agent import DatabaseAgent

# Event-driven version
from multi_agent_framework.agents.specialized.event_driven_db_agent import EventDrivenDatabaseAgent
```

**Capabilities**:
- Schema design
- Migration creation
- Query optimization
- Index management
- Data modeling

### QA Agent

**Role**: Ensures code quality through testing.

```python
from multi_agent_framework.agents.specialized.qa_agent import QAAgent

# Event-driven version
from multi_agent_framework.agents.specialized.event_driven_qa_agent import EventDrivenQAAgent
```

**Capabilities**:
- Unit test generation
- Integration test creation
- E2E test scenarios
- Code review
- Test coverage analysis

### Security Agent

**Role**: Identifies and fixes security vulnerabilities.

```python
from multi_agent_framework.agents.specialized.security_agent import SecurityAgent

# Event-driven version
from multi_agent_framework.agents.specialized.event_driven_security_agent import EventDrivenSecurityAgent
```

**Capabilities**:
- Vulnerability scanning
- Security best practices
- Authentication review
- OWASP compliance
- Secure coding patterns

### DevOps Agent

**Role**: Manages deployment and infrastructure.

```python
from multi_agent_framework.agents.specialized.devops_agent import DevOpsAgent

# Event-driven version
from multi_agent_framework.agents.specialized.event_driven_devops_agent import EventDrivenDevOpsAgent
```

**Capabilities**:
- Docker configuration
- CI/CD pipeline setup
- Kubernetes manifests
- Infrastructure as Code
- Deployment automation

### Documentation Agent

**Role**: Creates and maintains documentation.

```python
from multi_agent_framework.agents.specialized.docs_agent import DocsAgent

# Event-driven version
from multi_agent_framework.agents.specialized.event_driven_docs_agent import EventDrivenDocsAgent
```

**Capabilities**:
- API documentation
- README generation
- Code comments
- Architecture docs
- User guides

### UX/UI Agent

**Role**: Handles design and user experience.

```python
from multi_agent_framework.agents.specialized.ux_ui_agent import UXUIAgent

# Event-driven version
from multi_agent_framework.agents.specialized.event_driven_ux_ui_agent import EventDrivenUXUIAgent
```

**Capabilities**:
- Design system creation
- Component styling
- Accessibility features
- Responsive layouts
- UI/UX best practices

## Agent Communication

### Message Format

```python
{
    "task_id": "unique-task-id",
    "agent": "frontend_agent",
    "action": "create_component",
    "description": "Create user profile component",
    "dependencies": ["task-id-1", "task-id-2"],
    "metadata": {
        "priority": "high",
        "estimated_time": "2h"
    }
}
```

### Event Types

- `TASK_CREATED`: New task created
- `TASK_ASSIGNED`: Task assigned to agent
- `TASK_COMPLETED`: Task finished successfully
- `TASK_FAILED`: Task execution failed
- `STATUS_UPDATE`: Progress update
- `VALIDATION_REQUEST`: Request validation
- `VALIDATION_RESPONSE`: Validation result

## Custom Agent Development

### Creating a Custom Agent

```python
from multi_agent_framework.agents.base_agent import BaseAgent

class CustomAgent(BaseAgent):
    def __init__(self):
        super().__init__("custom_agent")
        self.capabilities = ["custom_task"]
    
    def process_message(self, message):
        # Custom processing logic
        return {
            "status": "completed",
            "result": "Custom task completed"
        }
```

### Registering Custom Agent

```python
# In agent_factory.py
AGENT_REGISTRY["custom_agent"] = CustomAgent
```