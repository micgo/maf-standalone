# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed
- **BREAKING**: Reorganized runtime state files into `.maf` directory structure
  - Message queue files moved from `message_queue/` and `multi_agent_framework/message_queue/` to `.maf/message_queues/`
  - Project state file moved from `project_state.json` to `.maf/state.json`
  - Updated all internal paths to use the new centralized location
  - This change provides cleaner project organization and better separation of runtime state

### Added
- Implemented 4 new event-driven agents following TDD practices:
  - `EventDrivenDevOpsAgent`: Handles Docker, CI/CD, Kubernetes, and deployment configurations
  - `EventDrivenSecurityAgent`: Performs security audits and implements security best practices
  - `EventDrivenDocsAgent`: Generates API documentation, READMEs, and technical documentation
  - `EventDrivenUXUIAgent`: Creates design systems, UI components, and handles styling
- Comprehensive test suite for all event-driven agents in `tests/test_event_driven_agents.py`

### Fixed
- Fixed critical event-driven mode issue where agents weren't processing inbox messages on startup
- Fixed import error in CLI for `get_available_agents` function
- Fixed agent factory mappings for DevOps agent (was looking for wrong class name)

### Changed
- Updated agent factory to properly map all event-driven agent classes
- Enhanced error handling in agent implementations to handle missing project directories

## [0.1.0] - 2025-06-13

### Added
- Initial release of Multi-Agent Framework as standalone package
- Event-driven architecture with Kafka support
- Smart file integration to reduce code duplication
- Project type auto-detection
- Support for multiple LLM providers (Gemini, Claude, OpenAI)
- CLI interface with `maf` command
- Quick Start guide and comprehensive documentation