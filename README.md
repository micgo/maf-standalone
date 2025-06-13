# Multi-Agent Framework (MAF)

An autonomous software development framework powered by AI agents that collaborate to build software projects.

## Overview

The Multi-Agent Framework (MAF) is a Python-based framework that orchestrates multiple specialized AI agents to autonomously develop software. Each agent has a specific role and expertise, working together to implement features, fix bugs, and maintain code quality.

## Features

- **Specialized AI Agents**: 9 specialized agents working in harmony:
  - Frontend, Backend, Database agents for core development
  - QA agent for testing and quality assurance
  - Security agent for vulnerability detection and secure coding
  - DevOps agent for deployment and infrastructure
  - Documentation agent for comprehensive docs
  - UX/UI agent for design systems and styling
- **Event-Driven Architecture**: Efficient publish/subscribe communication between agents
- **Intelligent Code Integration**: Smart file placement and code consolidation
- **Project Type Detection**: Automatically detects and adapts to different project types (Next.js, React, Django, etc.)
- **Configurable**: Point the framework at any codebase with custom configuration
- **Multiple LLM Support**: Works with OpenAI, Anthropic Claude, and Google Gemini

## Installation

### Prerequisites

- Python 3.8 or higher
- pip package manager
- At least one LLM API key (OpenAI, Anthropic, or Google Gemini)

### Install from PyPI (Coming Soon)

```bash
pip install multi-agent-framework
```

### Install from Source

1. Clone the repository:
```bash
git clone https://github.com/micgo/maf-standalone.git
cd maf-standalone
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install the package:
```bash
pip install -e .
```

## Quick Start

> 📚 **[View the detailed Quick Start Guide](docs/QUICK_START.md)** for step-by-step instructions with examples!

### 1. Initialize a Project

Navigate to your project directory and initialize MAF:

```bash
cd /path/to/your/project
maf init
```

This creates:
- `.maf-config.json` - Project configuration
- `.env.example` - Template for API keys
- Framework directories for state and message queues

### 2. Configure API Keys

Copy `.env.example` to `.env` and add your API keys:

```bash
cp .env.example .env
```

Edit `.env`:
```env
# At least one of these is required:
GEMINI_API_KEY=your_gemini_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
```

### 3. Launch Agents

Start the multi-agent framework:

```bash
maf launch
```

This starts all configured agents in event-driven mode.

### 4. Trigger Development

Request a new feature:

```bash
maf trigger "Add user authentication with email and password"
```

## Configuration

### Project Configuration

The `.maf-config.json` file contains project-specific settings:

```json
{
  "project_name": "My Awesome App",
  "project_type": "nextjs",
  "framework_config": {
    "state_file": ".maf_state.json",
    "message_queue_dir": ".maf_messages",
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
  }
}
```

### Model Configuration

Configure different LLM providers and models per agent:

```json
{
  "agent_config": {
    "default_model_provider": "gemini",
    "default_model_name": "gemini-2.0-flash-exp",
    "agent_models": {
      "orchestrator": {
        "provider": "anthropic",
        "name": "claude-3-sonnet-20240229"
      },
      "frontend_agent": {
        "provider": "openai",
        "name": "gpt-4-turbo-preview"
      }
    }
  }
}
```

## CLI Commands

### Basic Commands

```bash
# Initialize a project
maf init [PROJECT_PATH] [--name NAME] [--type TYPE]

# Launch agents
maf launch [--project PATH] [--agents agent1,agent2] [--mode polling|event]

# Trigger feature development
maf trigger "Feature description" [--project PATH]

# Check framework status
maf status [--project PATH] [--detailed]

# Reset framework state
maf reset [--project PATH]
```

### Configuration Management

```bash
# Show current configuration
maf config

# Save configuration to file
maf config --save config.json

# Load configuration from file
maf config --load config.json
```

## Agent Roles

### Orchestrator Agent
- Breaks down features into tasks
- Assigns tasks to appropriate agents
- Monitors progress and handles failures

### Frontend Agent
- Develops UI components
- Works with React, Next.js, Vue, etc.
- Implements responsive designs

### Backend Agent
- Creates API endpoints
- Implements business logic
- Handles authentication and authorization

### Database Agent
- Designs database schemas
- Creates migrations
- Optimizes queries

### QA Agent
- Writes unit and integration tests
- Performs code reviews
- Ensures code quality

### Security Agent
- Audits code for vulnerabilities
- Implements security best practices
- Reviews authentication flows

### DevOps Agent
- Manages deployment configurations
- Sets up CI/CD pipelines
- Handles infrastructure as code

### Documentation Agent
- Writes code documentation
- Creates API documentation
- Maintains README files

### UX/UI Agent
- Creates design mockups
- Ensures consistent styling
- Implements accessibility features

## Advanced Usage

### Event-Driven vs Polling Mode

```bash
# Launch in event-driven mode (default)
maf launch --mode event

# Launch in polling mode
maf launch --mode polling
```

### Custom Agent Selection

```bash
# Launch only specific agents
maf launch --agents orchestrator,frontend_agent,backend_agent
```

### Using Different Project Configurations

```bash
# Work on different projects
maf launch --project /path/to/project1
maf trigger "Add feature X" --project /path/to/project2
```

## Integration with Existing Projects

### Next.js Projects

MAF automatically detects Next.js projects and:
- Uses App Router conventions
- Integrates with existing components
- Follows Next.js best practices

### Django Projects

For Django projects, MAF:
- Creates Django apps and models
- Follows Django conventions
- Integrates with existing apps

### Custom Project Types

Add custom project type support by updating configuration:

```json
{
  "project_type": "custom",
  "technology_stack": {
    "frontend": ["custom-framework"],
    "backend": ["custom-backend"],
    "database": ["custom-db"]
  }
}
```

## Troubleshooting

### Agents Not Starting

1. Check API keys are configured correctly
2. Verify `.env` file exists and is readable
3. Check logs in `.maf_logs/` directory

### Tasks Getting Stuck

```bash
# Check agent status
maf status --detailed

# Reset if needed
maf reset
```

### Import Errors

Ensure the package is installed correctly:
```bash
pip install -e .
```

## Development

### Running Tests

```bash
python -m pytest tests/
```

### Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

MIT License - see LICENSE file for details

## Support

- GitHub Issues: [Report bugs and request features](https://github.com/micgo/maf-standalone/issues)
- Wiki: [Full documentation](https://github.com/micgo/maf-standalone/wiki)
- Discussions: [Join the conversation](https://github.com/micgo/maf-standalone/discussions)

## Acknowledgments

Built with:
- Google Gemini API
- Anthropic Claude API
- OpenAI API
- Python asyncio
- Click CLI framework