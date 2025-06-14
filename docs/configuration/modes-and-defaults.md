# Modes and Default Configuration

## Overview

The Multi-Agent Framework supports two communication modes and provides intelligent defaults to ensure a smooth experience.

## Communication Modes

### Polling Mode (Default)
- **Stability**: Production-ready and well-tested
- **How it works**: Agents check their message queues at regular intervals
- **Pros**:
  - Predictable behavior
  - Lower resource usage
  - More stable message processing
  - Better error recovery
- **Cons**:
  - Slight delay between message send and receive (typically 1-2 seconds)
- **Best for**: Most projects, especially when starting out

### Event-Driven Mode (Experimental)
- **Stability**: Experimental, may have issues
- **How it works**: Agents react immediately to new messages via event bus
- **Pros**:
  - Real-time communication
  - Immediate agent reactions
  - No polling delays
- **Cons**:
  - Higher resource usage
  - May have message processing issues
  - Requires more complex setup (Kafka for production)
- **Best for**: Projects requiring real-time coordination

## Choosing a Mode

```bash
# Use default (polling) - Recommended
maf launch

# Explicitly use polling mode
maf launch --mode polling

# Use experimental event-driven mode
maf launch --mode event
```

## Default Configuration

The framework uses intelligent defaults based on your project type:

### 1. Mode Selection
- Default: `polling` (stable and reliable)
- Can be changed in `.maf-config.json`

### 2. Agent Recommendations
The framework automatically recommends agents based on your project:

- **Next.js projects**: orchestrator, frontend_agent, backend_agent, ux_ui_agent
- **React projects**: orchestrator, frontend_agent, ux_ui_agent
- **Django projects**: orchestrator, backend_agent, db_agent, frontend_agent
- **Flask projects**: orchestrator, backend_agent, db_agent
- **Python projects**: orchestrator, backend_agent
- **Unknown/Auto**: orchestrator, frontend_agent, backend_agent

### 3. Critical Agent Detection
The framework will warn you if critical agents are missing:
- `orchestrator`: Required for coordinating other agents

## Customizing Defaults

Edit `.maf-config.json` to customize defaults:

```json
{
  "framework_config": {
    "default_mode": "polling",
    "event_bus_type": "in_memory"
  },
  "agent_config": {
    "enabled_agents": [
      "orchestrator",
      "frontend_agent",
      "backend_agent"
    ]
  }
}
```

## Understanding Mode Differences

Use the `maf modes` command to see detailed information:

```bash
$ maf modes

📡 Multi-Agent Framework Communication Modes

🔄 Polling Mode (Default - Recommended):
   - Agents check for messages at regular intervals
   - More stable and predictable behavior
   - Lower resource usage
   - Slight delay between message send and processing
   - Best for: Most projects, especially when starting out

⚡ Event-Driven Mode (Experimental):
   - Agents react immediately to new messages
   - Real-time communication between agents
   - Higher resource usage
   - May have stability issues with message processing
   - Best for: Projects requiring real-time coordination
```

## Health Checks

The `maf status` command now provides intelligent health checks:

```bash
$ maf status

📊 Multi-Agent Framework Status
   Project: My Next.js App

🤖 Agent Health Check:
   Enabled agents: 5
   💡 Tip: For nextjs projects, consider enabling: ux_ui_agent

⚙️ Configuration:
   Default mode: polling
   Default model: gemini
   Event bus: in_memory
```

## Migration Guide

If you're upgrading from an earlier version:

1. The default mode has changed from `event` to `polling`
2. To keep using event-driven mode, add to `.maf-config.json`:
   ```json
   {
     "framework_config": {
       "default_mode": "event"
     }
   }
   ```
3. Or specify mode when launching: `maf launch --mode event`

## Troubleshooting

### "Critical agents missing" warning
- The orchestrator agent is required to coordinate other agents
- The CLI will prompt to add it automatically

### Project type not detected
- The framework will use sensible defaults
- You can manually specify in `.maf-config.json`:
  ```json
  {
    "project_type": "nextjs"
  }
  ```

### Want to use Kafka for event-driven mode?
- Set environment variables:
  ```bash
  EVENT_BUS_TYPE=kafka
  KAFKA_BOOTSTRAP_SERVERS=localhost:9092
  ```