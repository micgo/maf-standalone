# Multi-Agent Framework v2.0

An advanced AI-powered development framework that coordinates multiple specialized agents to handle different aspects of software development with intelligent code generation, smart file integration, and cross-agent validation.

## 🚀 Key Features

### 1. **Intelligent Component Naming**
- Automatically extracts meaningful names from generated code
- Handles naming conflicts intelligently
- Supports different naming conventions (PascalCase, kebab-case, snake_case)
- Falls back to context-based naming when code extraction fails

### 2. **Smart File Integration**
- Reduces file proliferation by consolidating related functionality
- Intelligently determines when to modify vs. create files
- Supports multiple consolidation strategies:
  - **Function merging**: Combines utility functions
  - **Component consolidation**: Groups related components
  - **Enhancement mode**: Improves existing functionality
- Maintains code organization and readability

### 3. **Cross-Agent Validation**
- Validates API contracts between frontend and backend
- Ensures database schema consistency
- Checks component dependencies
- Validates test coverage
- Enforces security best practices

## 📁 Framework Structure

```
multi_agent_framework/
├── agents/
│   ├── base_agent.py          # Base class with enhanced integration
│   ├── orchestrator_agent.py  # Central coordinator
│   └── specialized/
│       ├── frontend_agent.py  # React/Next.js specialist
│       ├── backend_agent.py   # API/Server specialist
│       ├── db_agent.py        # Database specialist
│       ├── qa_agent.py        # Testing specialist
│       └── ...
├── core/
│   ├── intelligent_namer.py   # Smart naming system
│   ├── smart_integrator.py    # File consolidation logic
│   ├── cross_agent_validator.py # Validation pipeline
│   ├── message_bus.py         # Inter-agent communication
│   ├── project_analyzer.py    # Codebase analysis
│   └── file_integrator.py     # File management
└── state/
    └── project_state.json     # Task tracking
```

## 🔧 Enhanced Capabilities

### Intelligent Naming Examples

**Before:**
```
GeneratedComponent67e3afba.tsx
GeneratedComponent09941f33.tsx
```

**After:**
```
RsvpForm.tsx
EventAttendanceSummary.tsx
```

### Smart Integration Examples

**Scenario 1: Utility Functions**
Instead of creating `formatDate.ts`, the framework adds the function to existing `utils.ts`

**Scenario 2: Related Components**
`UserAvatar` component is added to existing `UserProfile.tsx` instead of creating a new file

**Scenario 3: API Enhancements**
New validation logic is merged into existing API route instead of creating duplicate endpoints

## 🛡️ Validation Features

### API Contract Validation
```typescript
// Frontend: api call
fetch('/api/users/profile', { method: 'GET' })

// Backend: validated endpoint
export async function GET(request) { ... }
```

### Security Compliance
- Detects hardcoded secrets
- Identifies SQL injection risks
- Warns about XSS vulnerabilities
- Ensures authentication on protected routes

### Test Coverage Analysis
- Identifies untested functions
- Validates test structure
- Suggests missing test cases

## 🚀 Usage

### Basic Feature Request
```python
python multi_agent_framework/trigger_feature.py
# Enter: "Add user profile editing with avatar upload"
```

### What Happens:
1. **Orchestrator** breaks down the feature into tasks
2. **Smart Naming** extracts "UserProfileEdit" and "AvatarUpload" as component names
3. **Smart Integration** consolidates into existing profile components
4. **Cross-Validation** ensures frontend/backend compatibility
5. **Security Check** validates file upload security

## 🔄 Improvement Benefits

### Before Enhancements:
- 50+ generated files with UUID names
- Duplicate functionality across files
- No validation between components
- Manual integration required

### After Enhancements:
- Meaningful, searchable file names
- Consolidated, organized codebase
- Automatic compatibility validation
- Reduced manual refactoring

## 🎯 Best Practices

1. **Task Descriptions**: Be specific about relationships
   - ✅ "Enhance user profile with avatar upload"
   - ❌ "Create avatar feature"

2. **Consolidation**: Framework automatically determines when to merge
   - Utility functions → existing utils
   - Sub-components → parent components
   - API enhancements → existing routes

3. **Validation**: Review validation results
   - Fix errors before deployment
   - Address warnings for better quality
   - Implement security suggestions

## 🛡️ Task State Management & Recovery

### Automatic Recovery Features

- **Stalled Task Detection**: Automatically identifies tasks stuck in progress >30 minutes
- **Smart Retry Logic**: Retries failed tasks up to 3 times with intelligent backoff
- **Health Monitoring**: Continuous monitoring of task states and agent performance  
- **Automatic Cleanup**: Archives old completed tasks to keep state manageable
- **Recovery Reporting**: Detailed health reports and recovery statistics

### Recovery Tool Usage

```bash
# Check system health
python multi_agent_framework/recovery_tool.py health

# Recover stalled tasks
python multi_agent_framework/recovery_tool.py recover --timeout 30

# Retry failed tasks  
python multi_agent_framework/recovery_tool.py retry --retries 3

# Clean old tasks
python multi_agent_framework/recovery_tool.py cleanup --days 7

# View agent status
python multi_agent_framework/recovery_tool.py agents

# Full recovery operation
python multi_agent_framework/recovery_tool.py full
```

### Automatic Orchestrator Features

The orchestrator now includes:
- **Health checks every 5 minutes**: Monitors all task states
- **Recovery operations every 10 minutes**: Automatic stalled task recovery
- **Immediate retry triggering**: Re-sends recovered tasks to agents
- **Performance tracking**: Completion rates and retry statistics

## 🔮 Future Enhancements

- **Learning System**: Improve based on successful patterns
- **Performance Monitoring**: Track generation efficiency
- **Interactive Mode**: Real-time task approval
- **Advanced Context**: AST-based code understanding
- **Agent Heartbeat Monitoring**: Detect unresponsive agents
- **Distributed Recovery**: Cross-system task recovery

## 🤝 Contributing

The framework is designed for extensibility. To add new capabilities:

1. Extend base classes in `core/`
2. Add new validation rules in `cross_agent_validator.py`
3. Enhance naming patterns in `intelligent_namer.py`
4. Improve consolidation strategies in `smart_integrator.py`

## 📊 Metrics

Track framework performance:
- Name extraction success rate
- File consolidation ratio
- Validation accuracy
- Code quality improvements

---

Built with ❤️ for efficient, intelligent code generation