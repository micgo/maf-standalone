# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

The Multi-Agent Framework (MAF) is a Python-based autonomous software development framework that orchestrates multiple specialized AI agents to collaboratively build software projects. It's designed as a standalone, installable package.

## Common Commands

### Installation and Setup
```bash
# Install from source
pip install -e .

# Or use the install script
./scripts/install.sh

# Setup virtual environment (use built-in venv)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### Running the Framework
```bash
# Launch agents (default event-driven mode)
maf launch

# Launch specific agents
maf launch --agents orchestrator,frontend,backend

# Trigger feature development
maf trigger "Add user authentication"

# Check status
maf status --detailed

# Reset framework
maf reset
```

### Testing
```bash
# Run all tests
pytest tests/

# Run specific test categories
pytest tests/unit/
pytest tests/integration/
pytest tests/e2e/

# Health check
python -m multi_agent_framework.recovery_tool health
```

### Development
```bash
# Install dev dependencies
pip install -e ".[dev]"

# The project follows these standards:
# - Black formatting (line-length: 100)
# - MyPy type checking
# - Flake8 linting
# - pytest for testing
```
- Do not add yourself to commit messages

## High-Level Architecture

### Core Components

1. **Event-Driven Architecture**: The framework operates in either polling or event-driven mode, with event-driven being the default and recommended approach.

2. **Event Bus System**: Located in `core/event_bus.py` and `core/kafka_event_bus.py`, it handles all inter-agent communication through standardized event types (TASK_CREATED, TASK_COMPLETED, etc.).

3. **Agent Factory Pattern**: `core/agent_factory.py` creates specialized agents based on configuration and detected project type.

4. **Project Configuration**: `core/project_config.py` auto-detects project types (React, Next.js, Django, etc.) and loads configuration from `.maf-config.json`.

5. **Smart Integration**: `core/smart_integrator.py` and `core/file_integrator.py` intelligently consolidate agent outputs to reduce file proliferation.

### Agent Hierarchy

- **Base Classes**: `agents/base_agent.py` and `agents/event_driven_base_agent.py` define the core agent interface
- **Orchestrator**: `agents/event_driven_orchestrator_agent.py` coordinates all other agents
- **Specialized Agents**: Located in `agents/specialized/`, each handles specific domains (frontend, backend, database, etc.)

### Key Patterns

1. **Message-Based Communication**: All agents communicate via JSON messages with standardized formats
2. **Task State Management**: Tasks progress through states (pending, in_progress, completed, failed)
3. **Cross-Agent Validation**: `core/cross_agent_validator.py` ensures compatibility between agent outputs
4. **Recovery System**: `recovery_tool.py` provides automatic task recovery and retry logic

### Configuration Structure

The framework uses `.maf-config.json` for project-specific configuration:
- Agent selection and model providers
- Custom paths for state files and message queues
- Event bus configuration (in-memory or Kafka)
- Project type detection overrides

### Migration Path

When migrating from embedded to standalone version:
1. Install as package instead of copying files
2. Use `maf` CLI instead of shell scripts
3. Update imports to use `multi_agent_framework` package
4. Configuration via `.maf-config.json` instead of environment variables