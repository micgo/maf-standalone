# Multi-Agent Framework File Structure

## 🏗️ Core Framework

### Essential Scripts
- **`cli.py`** - Main CLI interface (accessed via `maf` command)
- **`recovery_tool.py`** - System health monitoring and recovery
- **`trigger_feature.py`** - Start new feature development
- **`run_agents.py`** - Agent runner script

### Configuration
- **`pyproject.toml`** - Package configuration and dependencies
- **`config.py`** - Framework configuration
- **`.maf-config.json`** - Project-specific configuration (created by `maf init`)
- **`.env`** - Your API keys (not in git)

## 📁 Directory Structure

### `/multi_agent_framework/agents/`
- **`orchestrator_agent.py`** - Central coordinator
- **`base_agent.py`** - Base class for all agents
- **`specialized/`** - Domain-specific agents:
  - `frontend_agent.py` - React/Next.js specialist
  - `backend_agent.py` - API/Server specialist
  - `db_agent.py` - Database specialist
  - `security_agent.py` - Security specialist
  - `qa_agent.py` - Testing specialist
  - `devops_agent.py` - DevOps specialist
  - `docs_agent.py` - Documentation specialist
  - `ux_ui_agent.py` - UX/UI specialist

### `/multi_agent_framework/core/`
- **`project_state_manager.py`** - Task tracking and recovery
- **`message_bus.py`** - Inter-agent communication
- **`intelligent_namer.py`** - Smart file naming
- **`smart_integrator.py`** - File consolidation
- **`cross_agent_validator.py`** - Quality validation
- **`project_analyzer.py`** - Codebase analysis
- **`file_integrator.py`** - File management

### Runtime Directory
- Runtime files are now stored in `.maf/` in the target project directory
- Contains `state.json` and `message_queues/`
- Created automatically by `maf init`

### Installation
- Install as package: `pip install -e .`
- Virtual environment is recommended but not required

## 📊 State Files
- **`.maf/state.json`** - Current tasks and features (in target project directory)
- Individual agent inbox files in `.maf/message_queues/` (in target project directory)

## 📚 Documentation
- **`README.md`** - Framework overview and features
- **`RECOVERY_FEATURES.md`** - Recovery system documentation
- **`FILE_STRUCTURE.md`** - This file

## 🚀 Quick Start

1. **Install:** `pip install -e .`
2. **Initialize:** `maf init`
3. **Launch:** `maf launch`
4. **Develop:** `maf trigger "Your feature description"`
5. **Monitor:** `maf status`

## 🔧 Maintenance

- **Status Check:** `maf status`
- **Detailed Status:** `maf status --detailed`
- **Reset Framework:** `maf reset`
- **View Logs:** `maf logs`

## 📈 Features

- ✅ 9 specialized AI agents
- ✅ Intelligent task coordination
- ✅ Smart file naming and integration
- ✅ Automatic recovery and health monitoring
- ✅ Real-time system status
- ✅ Cross-agent validation
- ✅ CLI interface for easy management

---

**Total Files:** ~30 framework files  
**Total Agents:** 9 (1 orchestrator + 8 specialists)  
**Development Status:** Production ready ✅