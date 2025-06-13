# Event Bus Architecture

## Overview

The Multi-Agent Framework now supports a hybrid event bus architecture that allows you to choose between different messaging backends based on your needs:

- **In-Memory Event Bus**: Fast, simple, suitable for development and single-instance deployments
- **Kafka Event Bus**: Distributed, scalable, suitable for production and multi-instance deployments

## Architecture

```
┌─────────────────┐
│   Agent Code    │
└────────┬────────┘
         │ Uses
         ▼
┌─────────────────┐
│  IEventBus      │ ◄── Interface
└────────┬────────┘
         │ Implements
    ┌────┴────┐
    ▼         ▼
┌─────────┐ ┌──────────┐
│InMemory │ │  Kafka   │
│EventBus │ │EventBus  │
└─────────┘ └──────────┘
```

## Configuration

### Via Code

```python
from multi_agent_framework.core.event_bus_factory import get_event_bus

# Default (in-memory)
event_bus = get_event_bus()

# Kafka
kafka_config = {
    'type': 'kafka',
    'kafka_config': {
        'bootstrap_servers': ['localhost:9092'],
        'consumer_group': 'multi-agent-framework',
        'max_workers': 10
    }
}
event_bus = get_event_bus(kafka_config)
```

### Via Configuration File

Edit `multi_agent_framework/config.py`:

```python
EVENT_BUS_CONFIG = {
    'type': 'kafka',  # or 'inmemory'
    'kafka_config': {
        'bootstrap_servers': ['broker1:9092', 'broker2:9092'],
        'consumer_group': 'multi-agent-framework',
        'max_workers': 20
    }
}
```

### Via Environment Variables

```bash
export EVENT_BUS_TYPE=kafka
export KAFKA_BOOTSTRAP_SERVERS=broker1:9092,broker2:9092
export KAFKA_CONSUMER_GROUP=my-app
export KAFKA_MAX_WORKERS=20
```

## Usage

### Publishing Events

```python
from multi_agent_framework.core.event_bus_interface import Event, EventType
from multi_agent_framework.core.event_bus_factory import get_event_bus

event_bus = get_event_bus()

# Publish a generic event
event = Event(
    id="unique-id",
    type=EventType.TASK_CREATED,
    source="my_agent",
    timestamp=time.time(),
    data={"description": "Process user data"}
)
event_bus.publish(event)

# Publish a task event (convenience method)
event_bus.publish_task_event(
    EventType.TASK_COMPLETED,
    task_id="task-123",
    source="backend_agent",
    data={"result": "Success"}
)
```

### Subscribing to Events

```python
def handle_task_created(event: Event):
    print(f"New task: {event.data['description']}")

event_bus.subscribe(EventType.TASK_CREATED, handle_task_created)
```

### Event Filtering

```python
# Add a filter to only process high-priority events
def priority_filter(event: Event) -> bool:
    return event.data.get('priority', 'normal') == 'high'

event_bus.add_filter(priority_filter)
```

### Event History and Replay

```python
# Get event history
all_events = event_bus.get_event_history()
recent_events = event_bus.get_event_history(since=time.time() - 3600)
agent_events = event_bus.get_event_history(source="frontend_agent")

# Replay events (useful for recovery)
event_bus.replay_events(recent_events)
```

## Event Types

Standard event types are defined in `EventType` enum:

- **Task Events**: `TASK_CREATED`, `TASK_ASSIGNED`, `TASK_STARTED`, `TASK_COMPLETED`, `TASK_FAILED`, `TASK_RETRY`
- **Feature Events**: `FEATURE_CREATED`, `FEATURE_STARTED`, `FEATURE_COMPLETED`, `FEATURE_BLOCKED`
- **Agent Events**: `AGENT_STARTED`, `AGENT_STOPPED`, `AGENT_HEARTBEAT`, `AGENT_ERROR`
- **System Events**: `SYSTEM_SHUTDOWN`, `SYSTEM_HEALTH_CHECK`
- **Custom Events**: `CUSTOM`

## Migration Guide

### From Polling to Event-Driven

1. Change agent base class:
   ```python
   # Old
   from multi_agent_framework.agents.base_agent import BaseAgent
   
   # New
   from multi_agent_framework.agents.event_driven_base_agent import EventDrivenBaseAgent
   ```

2. Implement `process_task` instead of polling loop:
   ```python
   class MyAgent(EventDrivenBaseAgent):
       def process_task(self, task_id: str, task_data: Dict[str, Any]) -> Any:
           # Process the task
           return result
   ```

3. Enable event-driven mode in config:
   ```python
   EVENT_DRIVEN_MODE = True
   ```

### From In-Memory to Kafka

1. Install Kafka dependencies:
   ```bash
   pip install kafka-python
   ```

2. Start Kafka locally or point to your Kafka cluster

3. Update configuration:
   ```python
   EVENT_BUS_CONFIG = {
       'type': 'kafka',
       'kafka_config': {
           'bootstrap_servers': ['localhost:9092']
       }
   }
   ```

## Performance Considerations

### In-Memory Event Bus
- **Pros**: Zero network latency, no external dependencies
- **Cons**: Limited to single process, events lost on crash
- **Use when**: Development, testing, small deployments

### Kafka Event Bus
- **Pros**: Distributed, persistent, handles high volume
- **Cons**: Network latency, operational complexity
- **Use when**: Production, multi-instance deployments, need persistence

## Troubleshooting

### In-Memory Issues
- **Events not received**: Check that event bus is started
- **Memory growth**: Limit event history size in configuration

### Kafka Issues
- **Connection failed**: Verify Kafka is running and accessible
- **Slow processing**: Increase `max_workers` in configuration
- **Missing events**: Check consumer group and topic names

## Future Enhancements

1. **Redis Event Bus**: For medium-scale deployments
2. **RabbitMQ Event Bus**: For AMQP compatibility
3. **Event Schemas**: Validate event data structure
4. **Event Metrics**: Prometheus integration
5. **Dead Letter Queue**: Handle failed events