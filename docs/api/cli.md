# CLI Reference

The Multi-Agent Framework provides a command-line interface through the `maf` command.

## Installation

After installing the package, the `maf` command becomes available:

```bash
pip install -e .
maf --help
```

## Commands

### maf init

Initialize a new MAF project in the current directory.

```bash
maf init [OPTIONS]
```

**Options**:
- `--name TEXT`: Project name (default: current directory name)
- `--type TEXT`: Project type (auto-detected if not specified)
- `--path PATH`: Project path (default: current directory)

**Example**:
```bash
maf init --name "My App" --type nextjs
```

### maf launch

Launch the multi-agent framework.

```bash
maf launch [OPTIONS]
```

**Options**:
- `--project PATH`: Project directory (default: current directory)
- `--agents TEXT`: Comma-separated list of agents to launch
- `--mode [event|polling]`: Launch mode (default: event)
- `--verbose`: Enable verbose logging

**Examples**:
```bash
# Launch all agents in event-driven mode
maf launch

# Launch specific agents
maf launch --agents orchestrator,frontend_agent,backend_agent

# Launch in polling mode
maf launch --mode polling
```

### maf trigger

Trigger a new feature development task.

```bash
maf trigger DESCRIPTION [OPTIONS]
```

**Arguments**:
- `DESCRIPTION`: Feature description (required)

**Options**:
- `--project PATH`: Project directory (default: current directory)
- `--priority [low|medium|high]`: Task priority (default: medium)
- `--agents TEXT`: Specific agents to involve

**Examples**:
```bash
# Simple feature request
maf trigger "Add user authentication with email and password"

# High priority task
maf trigger "Fix critical security vulnerability" --priority high

# Specific agents
maf trigger "Update API documentation" --agents docs_agent
```

### maf status

Check the status of the framework and running agents.

```bash
maf status [OPTIONS]
```

**Options**:
- `--project PATH`: Project directory (default: current directory)
- `--detailed`: Show detailed status information
- `--json`: Output in JSON format

**Examples**:
```bash
# Basic status
maf status

# Detailed status
maf status --detailed

# JSON output for scripting
maf status --json
```

### maf reset

Reset the framework state, clearing all tasks and messages.

```bash
maf reset [OPTIONS]
```

**Options**:
- `--project PATH`: Project directory (default: current directory)
- `--force`: Skip confirmation prompt
- `--keep-logs`: Preserve log files

**Examples**:
```bash
# Reset with confirmation
maf reset

# Force reset
maf reset --force

# Reset but keep logs
maf reset --keep-logs
```

### maf config

Manage framework configuration.

```bash
maf config [OPTIONS]
```

**Options**:
- `--show`: Display current configuration
- `--save PATH`: Save configuration to file
- `--load PATH`: Load configuration from file
- `--set KEY=VALUE`: Set a configuration value
- `--project PATH`: Project directory (default: current directory)

**Examples**:
```bash
# Show current config
maf config --show

# Save config to file
maf config --save my-config.json

# Load config from file
maf config --load my-config.json

# Set configuration value
maf config --set agent_config.default_model_provider=openai
```

### maf logs

View framework logs.

```bash
maf logs [OPTIONS] [AGENT]
```

**Arguments**:
- `AGENT`: Specific agent to show logs for (optional)

**Options**:
- `--project PATH`: Project directory (default: current directory)
- `--follow`: Follow log output (like tail -f)
- `--lines N`: Number of lines to show (default: 50)
- `--level [DEBUG|INFO|WARNING|ERROR]`: Log level filter

**Examples**:
```bash
# View all logs
maf logs

# View frontend agent logs
maf logs frontend_agent

# Follow logs in real-time
maf logs --follow

# Show only errors
maf logs --level ERROR
```

### maf version

Show the framework version.

```bash
maf version
```

## Environment Variables

### API Keys

- `GEMINI_API_KEY`: Google Gemini API key
- `ANTHROPIC_API_KEY`: Anthropic Claude API key
- `OPENAI_API_KEY`: OpenAI API key

### Configuration

- `MAF_PROJECT_PATH`: Default project path
- `MAF_CONFIG_FILE`: Path to configuration file
- `MAF_LOG_LEVEL`: Default log level
- `MAF_TEST_MODE`: Enable test mode (mocks LLM calls)

## Configuration File

The `.maf-config.json` file in your project directory:

```json
{
  "project_name": "My App",
  "project_type": "nextjs",
  "framework_config": {
    "state_file": ".maf/state.json",
    "message_queue_dir": ".maf/message_queues",
    "log_dir": ".maf_logs"
  },
  "agent_config": {
    "default_model_provider": "gemini",
    "default_model_name": "gemini-2.0-flash-exp",
    "enabled_agents": [
      "orchestrator",
      "frontend_agent",
      "backend_agent",
      "db_agent",
      "qa_agent"
    ]
  },
  "event_bus": {
    "type": "in_memory"
  }
}
```

## Exit Codes

- `0`: Success
- `1`: General error
- `2`: Configuration error
- `3`: API key error
- `4`: Project not initialized
- `5`: Agent startup failure

## Tips

1. Always run `maf init` before other commands
2. Use `--verbose` for debugging
3. Check `maf status` if agents seem unresponsive
4. Use `maf reset` if tasks get stuck
5. Set up `.env` file for API keys
6. Use event-driven mode for better performance
7. Monitor logs with `maf logs --follow`