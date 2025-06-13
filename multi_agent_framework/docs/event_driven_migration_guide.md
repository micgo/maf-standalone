# Event-Driven Migration Guide

## Overview

This guide documents the migration from polling-based to event-driven architecture in the Multi-Agent Framework.

## Architecture Changes

### Before (Polling)
- Agents continuously poll message queues every few seconds
- High CPU usage from constant polling loops
- Delayed message processing (up to poll interval)
- Each agent manages its own message checking

### After (Event-Driven)
- Agents subscribe to specific event types
- Instant message delivery via publish/subscribe
- CPU usage only when processing events
- Centralized event bus manages all communication

## Migration Status

Currently migrated agents:
- ✅ Orchestrator Agent
- ✅ Frontend Agent  
- ✅ Backend Agent
- ✅ Database Agent

Pending migrations:
- ⚠️ QA Agent
- ⚠️ Security Agent
- ⚠️ DevOps Agent
- ⚠️ Documentation Agent
- ⚠️ UX/UI Agent

## How to Migrate an Agent

### 1. Create Event-Driven Version

```python
# Template for event-driven agent
from agents.event_driven_base_agent import EventDrivenBaseAgent
from core.event_bus_interface import Event, EventType

class EventDrivenMyAgent(EventDrivenBaseAgent):
    def __init__(self):
        super().__init__("my_agent")
    
    def process_task(self, task_id: str, task_data: Dict[str, Any]) -> Any:
        # Implement task processing logic
        return result
```

### 2. Subscribe to Custom Events

```python
def _subscribe_to_events(self):
    super()._subscribe_to_events()
    
    # Subscribe to agent-specific events
    self.event_bus.subscribe(EventType.CUSTOM, self._handle_custom_event)
```

### 3. Migrate Message Processing Logic

Move logic from `_process_message()` to `process_task()`:

```python
# Old (polling)
def _process_message(self, msg):
    if msg["type"] == "new_task":
        # Process task
        
# New (event-driven)  
def process_task(self, task_id: str, task_data: Dict[str, Any]) -> Any:
    # Process task
```

## Configuration

### Enable Event-Driven Mode

In `config.py`:
```python
EVENT_DRIVEN_MODE = True
```

### Choose Event Bus Implementation

```python
EVENT_BUS_CONFIG = {
    'type': 'inmemory',  # or 'kafka' for production
    'kafka_config': {
        'bootstrap_servers': ['localhost:9092'],
        'consumer_group': 'multi-agent-framework'
    }
}
```

## Running Agents

### Command Line
```bash
# Run all agents in event-driven mode
python run_agents.py --mode event_driven

# Run specific agents
python run_agents.py --agents orchestrator frontend backend --mode event_driven

# Send test feature
python run_agents.py --test-feature "Add user authentication"

# Enable monitoring
python run_agents.py --monitor
```

### Programmatically
```python
from core.agent_factory import create_agent

# Create event-driven agent
agent = create_agent('frontend', mode='event_driven')
agent.run()
```

## Event Types

Standard events all agents can use:
- `TASK_CREATED` - New task created
- `TASK_ASSIGNED` - Task assigned to agent
- `TASK_STARTED` - Agent started processing
- `TASK_COMPLETED` - Task finished successfully
- `TASK_FAILED` - Task failed
- `TASK_RETRY` - Retry failed task
- `AGENT_STARTED/STOPPED` - Agent lifecycle
- `SYSTEM_SHUTDOWN` - Graceful shutdown

## Testing Event-Driven Agents

Run the test script:
```bash
python test_event_driven_agents.py
```

This demonstrates:
- Feature request processing
- Direct task assignment
- Event propagation
- Error handling and retry
- Event filtering
- System health checks

## Best Practices

1. **Use Typed Events**: Always use the EventType enum
2. **Include Correlation IDs**: Track related events
3. **Emit Custom Events**: For cross-agent communication
4. **Handle Errors Gracefully**: Emit error events for monitoring
5. **Test Both Modes**: Ensure agents work in both polling and event-driven modes

## Monitoring

Check event bus statistics:
```python
stats = event_bus.get_statistics()
print(f"Total events: {stats['total_events_processed']}")
print(f"Queue size: {stats['queue_size']}")
```

View event history:
```python
# Get recent events
recent = event_bus.get_event_history(since=time.time() - 3600)

# Filter by type
task_events = event_bus.get_event_history(event_type=EventType.TASK_COMPLETED)
```

## Rollback Plan

If issues arise, you can quickly rollback:

1. Set `EVENT_DRIVEN_MODE = False` in config
2. Restart agents - they'll use polling mode
3. Both modes coexist, allowing gradual migration

## Future Enhancements

1. **Event Persistence**: Store events for replay and debugging
2. **Dead Letter Queue**: Handle permanently failed events
3. **Event Schemas**: Validate event data structure
4. **Distributed Tracing**: Track events across agents
5. **WebSocket Integration**: Real-time UI updates

## Troubleshooting

### Events Not Received
- Check agent is subscribed to event type
- Verify event bus is started
- Look for filters blocking events

### High Memory Usage
- Limit event history size
- Use Kafka for high-volume scenarios
- Clear old events periodically

### Agents Not Starting
- Check imports are correct
- Verify event bus configuration
- Look for initialization errors

### Performance Issues
- Use batch event processing
- Implement event aggregation
- Consider Kafka for scale