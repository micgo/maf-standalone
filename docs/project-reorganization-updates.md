# Documentation Updates for Project Reorganization

## Summary of Changes

This document summarizes the documentation updates made to reflect the recent project reorganization.

### Runtime Directory Structure

The framework now uses a centralized `.maf/` directory for all runtime files:
- **Old**: Separate `message_queue/` and `project_state.json` files
- **New**: `.maf/` directory containing:
  - `state.json` - Framework state tracking
  - `message_queues/` - Agent message queues

### Test Organization

Tests have been reorganized into categories:
- **Old**: Test files in root and `/multi_agent_framework/test_*.py`
- **New**: Organized in `/tests/` with subdirectories:
  - `/tests/unit/` - Unit tests
  - `/tests/integration/` - Integration tests
  - `/tests/e2e/` - End-to-end tests

### Shell Scripts

Shell scripts have been moved:
- **Old**: Scripts in `/multi_agent_framework/`
- **New**: Scripts in `/scripts/` directory

## Files Updated

### Main Documentation
1. **README.md**
   - Updated runtime directory structure
   - Updated test running examples

2. **CLAUDE.md**
   - Updated virtual environment setup instructions
   - Confirmed test locations are correct

3. **MIGRATION.md**
   - Updated project initialization output
   - Updated agent communication troubleshooting

4. **multi_agent_framework/FILE_STRUCTURE.md**
   - Updated runtime directory references
   - Updated state file locations

### API Documentation
1. **docs/api/cli.md**
   - Updated default configuration paths

### Guide Documentation
1. **docs/guides/quick-start.md**
   - Updated project initialization output
   
2. **docs/guides/event-driven-migration.md**
   - Updated test command to use pytest

### Wiki Documentation
1. **wiki/Configuration.md**
   - Updated file locations diagram
   - Updated default configuration paths

2. **wiki/Installation.md**
   - Updated project initialization output

3. **wiki/Architecture.md**
   - Updated persistence file locations

4. **wiki/Troubleshooting.md**
   - Updated all directory references
   - Updated troubleshooting commands

## No Updates Needed

The following files were checked but did not require updates:
- **docs/architecture/event-driven.md** - Test references are correct
- **docs/architecture/error-handling.md** - No outdated references
- **docs/development/testing.md** - Correctly documents new test structure
- **docs/recent-changes.md** - Documents historical changes
- **CHANGELOG.md** - Already documents the reorganization

## Verification

All markdown files have been checked for outdated references to:
- `.maf_messages` → `.maf/message_queues`
- `.maf_state.json` → `.maf/state.json`
- `project_state.json` → `.maf/state.json`
- `/message_queue/` → `.maf/message_queues/`
- Test files in old locations → `/tests/` subdirectories
- Shell scripts in old locations → `/scripts/`

The documentation is now fully updated to reflect the new project structure.