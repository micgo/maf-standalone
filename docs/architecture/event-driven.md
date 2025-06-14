# Event-Driven Architecture

This document consolidates information about the Multi-Agent Framework's event-driven architecture.

## Overview

The Multi-Agent Framework operates in either polling or event-driven mode, with event-driven being the default and recommended approach. The event-driven architecture provides better scalability, lower latency, and more efficient resource usage.

## Core Components

### Event Bus System

Located in `core/event_bus.py` and `core/kafka_event_bus.py`, the event bus handles all inter-agent communication through standardized event types:

- `TASK_CREATED` - New task created by orchestrator
- `TASK_ASSIGNED` - Task assigned to a specific agent
- `TASK_COMPLETED` - Agent completed a task
- `TASK_FAILED` - Task execution failed
- `AGENT_MESSAGE` - General inter-agent communication
- `STATUS_UPDATE` - Progress updates
- `ERROR` - Error notifications
- `VALIDATION_REQUEST` - Request for cross-agent validation
- `VALIDATION_RESPONSE` - Validation results

### Event-Driven Base Agent

The `EventDrivenBaseAgent` class in `agents/event_driven_base_agent.py` provides:

- Asynchronous event processing
- Automatic event subscription based on agent role
- Built-in error handling and retry logic
- Event acknowledgment and tracking

## Migration Guide

See the [Event-Driven Migration Guide](../guides/event-driven-migration.md) for details on migrating from polling to event-driven mode.

## Implementation Details

### Message Format

```json
{
  "event_type": "TASK_CREATED",
  "event_id": "unique-uuid",
  "timestamp": "2025-01-13T10:00:00Z",
  "source": "orchestrator",
  "target": "frontend_agent",
  "payload": {
    "task_id": "task-uuid",
    "description": "Create user profile component",
    "priority": "high",
    "metadata": {}
  }
}
```

### Event Flow

1. **Task Creation**: Orchestrator creates a task and publishes `TASK_CREATED` event
2. **Task Assignment**: Target agent receives event and publishes `TASK_ASSIGNED` acknowledgment
3. **Processing**: Agent works on the task, publishing `STATUS_UPDATE` events
4. **Completion**: Agent publishes `TASK_COMPLETED` with results
5. **Validation**: Cross-agent validation via `VALIDATION_REQUEST/RESPONSE` events

### Kafka Integration

When using Kafka as the event bus:

```json
{
  "event_bus": {
    "type": "kafka",
    "config": {
      "bootstrap_servers": "localhost:9092",
      "topic_prefix": "maf",
      "consumer_group": "maf-agents"
    }
  }
}
```

### Benefits

1. **Scalability**: Agents can be distributed across multiple machines
2. **Reliability**: Event persistence and replay capabilities
3. **Observability**: Complete audit trail of all agent interactions
4. **Flexibility**: Easy to add new agents or modify workflows
5. **Performance**: Asynchronous processing reduces latency

### Best Practices

1. **Event Naming**: Use clear, descriptive event types
2. **Payload Design**: Keep payloads focused and minimal
3. **Error Handling**: Always include error events in workflows
4. **Idempotency**: Design event handlers to be idempotent
5. **Monitoring**: Track event processing metrics

## Testing

The event-driven system includes comprehensive tests in:
- `tests/integration/test_event_driven_agents.py`
- `tests/integration/test_event_driven_integration.py`
- `tests/unit/test_kafka_event_bus.py`