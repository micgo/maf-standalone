# Multi-Agent Framework File Structure

## 🏗️ Core Framework

### Essential Scripts
- **`launch_agents.sh`** - Launch all agents in iTerm2 tabs (main launcher)
- **`setup_venv.sh`** - Set up virtual environment and dependencies
- **`recovery_tool.py`** - System health monitoring and recovery
- **`trigger_feature.py`** - Start new feature development
- **`test_agent_communication.py`** - Test framework functionality
- **`check_agents.sh`** - Quick system status check

### Configuration
- **`requirements.txt`** - Python dependencies
- **`.env.example`** - Environment variables template
- **`.env`** - Your API keys (not in git)

## 📁 Directory Structure

### `/agents/`
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

### `/core/`
- **`project_state_manager.py`** - Task tracking and recovery
- **`message_bus.py`** - Inter-agent communication
- **`intelligent_namer.py`** - Smart file naming
- **`smart_integrator.py`** - File consolidation
- **`cross_agent_validator.py`** - Quality validation
- **`project_analyzer.py`** - Codebase analysis
- **`file_integrator.py`** - File management

### `/message_queue/`
- Individual agent inbox JSON files
- Handles asynchronous communication between agents

### `/venv/`
- Python virtual environment
- Contains all framework dependencies

## 📊 State Files
- **`project_state.json`** - Current tasks and features
- Individual agent inbox files in `message_queue/`

## 📚 Documentation
- **`README.md`** - Framework overview and features
- **`RECOVERY_FEATURES.md`** - Recovery system documentation
- **`FILE_STRUCTURE.md`** - This file

## 🚀 Quick Start

1. **Setup:** `./setup_venv.sh`
2. **Launch:** `./launch_agents.sh`
3. **Test:** `python3 test_agent_communication.py`
4. **Develop:** `python3 trigger_feature.py`
5. **Monitor:** `python3 recovery_tool.py health`

## 🔧 Maintenance

- **Health Check:** `python3 recovery_tool.py health`
- **Agent Status:** `python3 recovery_tool.py agents`
- **System Recovery:** `python3 recovery_tool.py full`
- **Quick Status:** `./check_agents.sh`

## 📈 Features

- ✅ 9 specialized AI agents
- ✅ Intelligent task coordination
- ✅ Smart file naming and integration
- ✅ Automatic recovery and health monitoring
- ✅ Real-time system status
- ✅ Cross-agent validation
- ✅ iTerm2 integration for easy monitoring

---

**Total Files:** ~30 framework files  
**Total Agents:** 9 (1 orchestrator + 8 specialists)  
**Development Status:** Production ready ✅