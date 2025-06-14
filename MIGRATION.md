# Migration Guide

This guide helps you migrate from the embedded multi_agent_framework to the standalone version.

## Key Changes

### 1. Installation Method
**Before**: Copy framework files into your project
**After**: Install as a package with `pip install multi-agent-framework`

### 2. Project Initialization
**Before**: Manual setup of message queues and state files
**After**: Run `maf init` to automatically set up your project

### 3. Configuration
**Before**: Hardcoded paths in scripts
**After**: Configuration via `.maf-config.json` file

### 4. Launching Agents
**Before**: `./launch_agents.sh`
**After**: `maf launch`

### 5. Imports
**Before**:
```python
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from agents.base_agent import BaseAgent
```

**After**:
```python
from multi_agent_framework.agents.base_agent import BaseAgent
```

## Step-by-Step Migration

### 1. Install the Standalone Framework

```bash
pip install multi-agent-framework
```

Or from source:
```bash
git clone https://github.com/yourusername/multi-agent-framework.git
cd multi-agent-framework
pip install -e .
```

### 2. Initialize Your Project

In your existing project directory:
```bash
maf init
```

This creates:
- `.maf-config.json` - Project configuration
- `.maf/` - Runtime directory containing:
  - `state.json` - Task tracking
  - `message_queues/` - Agent communication

### 3. Update Your Configuration

Edit `.maf-config.json` to match your project:

```json
{
    "project_name": "Your Project Name",
    "agents": {
        "model_provider": "gemini",
        "enabled_agents": ["orchestrator", "frontend", "backend", "database"]
    }
}
```

### 4. Update Custom Agents

If you have custom agents, update them to use the new imports:

```python
# Old way
from agents.base_agent import BaseAgent

# New way
from multi_agent_framework.agents.base_agent import BaseAgent

class MyCustomAgent(BaseAgent):
    def __init__(self, project_root=None):
        # Pass project_root to base class
        super().__init__("my_agent", project_root=project_root)
```

### 5. Update Launch Scripts

Replace shell scripts with CLI commands:

```bash
# Old way
./launch_agents.sh

# New way
maf launch
```

### 6. Update Feature Triggers

```bash
# Old way
python trigger_feature.py

# New way
maf trigger "Your feature description"
```

## Environment Variables

The framework now supports environment-based configuration:

- `MAF_PROJECT_ROOT` - Override project root directory
- `MAF_CONFIG_FILE` - Path to configuration file
- `EVENT_BUS_TYPE` - Set to 'kafka' for Kafka support

## Backwards Compatibility

The framework maintains backwards compatibility where possible:
- Old message queue formats are preserved
- State file structure remains the same
- Agent communication protocol is unchanged

## Troubleshooting

### Import Errors
If you get import errors, ensure:
1. The framework is properly installed: `pip show multi-agent-framework`
2. You're not mixing old and new import styles
3. Your PYTHONPATH doesn't include the old framework location

### Configuration Issues
- Run `maf init` to create a default configuration
- Check that `.maf-config.json` is valid JSON
- Ensure all paths in the config are accessible

### Agent Communication
- Verify `.maf/message_queues/` directory exists and is writable
- Check that all agents are using the same project root
- Run `maf status` to diagnose communication issues

## Getting Help

- Check the [README](README.md) for detailed documentation
- Run `maf --help` for CLI options
- Report issues on GitHub