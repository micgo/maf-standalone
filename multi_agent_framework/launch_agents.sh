#!/bin/bash

# Verbose Multi-Agent Framework Launcher with Status Display

PROJECT_ROOT="/Users/micgo/Development/pack429/multi_agent_framework"

echo "🤖 Launching Multi-Agent Framework (Verbose Mode)..."

# Check virtual environment
if [ ! -d "$PROJECT_ROOT/venv" ]; then
    echo "❌ Virtual environment not found. Run setup_venv.sh first."
    exit 1
fi

# Start iTerm2 if not running  
if ! pgrep -f "iTerm" >/dev/null; then
    echo "📱 Starting iTerm2..."
    open -a iTerm.app
    sleep 3
fi

echo "🚀 Starting agents with status display..."

# Function to launch an agent with status info
launch_agent_verbose() {
    local name=$1
    local script=$2
    
    echo "  🚀 Starting $name..."
    
    osascript -e "
    tell application \"iTerm2\"
        tell current window
            set newTab to (create tab with default profile)
            tell newTab
                tell current session
                    write text \"echo '🎯 Multi-Agent Framework - $name Agent'\"
                    write text \"echo '========================================='\"
                    write text \"cd '$PROJECT_ROOT'\"
                    write text \"source venv/bin/activate\"
                    write text \"echo '✅ Virtual environment activated'\"
                    write text \"echo '🔑 Checking API keys...'\"
                    write text \"python3 -c 'import os; print(\\\"GEMINI_API_KEY:\\\", \\\"✅ Set\\\" if os.getenv(\\\"GEMINI_API_KEY\\\") else \\\"❌ Not set\\\")'\"
                    write text \"echo '🚀 Starting $name agent...'\"
                    write text \"echo '⏳ Agent will show \\\"Waiting for instructions...\\\" when ready'\"
                    write text \"python3 $script\"
                end tell
            end tell
        end tell
    end tell"
    
    echo "  ✅ $name agent tab created"
    sleep 0.5
}

# Launch each agent
launch_agent_verbose "Orchestrator" "agents/orchestrator_agent.py"
launch_agent_verbose "Frontend" "agents/specialized/frontend_agent.py"
launch_agent_verbose "Backend" "agents/specialized/backend_agent.py"
launch_agent_verbose "Database" "agents/specialized/db_agent.py"
launch_agent_verbose "Security" "agents/specialized/security_agent.py"
launch_agent_verbose "QA" "agents/specialized/qa_agent.py"
launch_agent_verbose "DevOps" "agents/specialized/devops_agent.py"
launch_agent_verbose "Docs" "agents/specialized/docs_agent.py"
launch_agent_verbose "UX-UI" "agents/specialized/ux_ui_agent.py"

echo ""
echo "🎉 All agent tabs created!"
echo ""
echo "📝 What to expect in each tab:"
echo "  1. Environment setup messages"
echo "  2. API key validation"
echo "  3. Agent startup messages"
echo "  4. 'Waiting for instructions...' (this means it's working!)"
echo ""
echo "🔍 To verify agents are running:"
echo "  1. Check each iTerm2 tab for 'Waiting for instructions...'"
echo "  2. Run: python3 recovery_tool.py health"
echo "  3. Look for agent processes: ps aux | grep python"
echo ""
echo "🚀 To start development:"
echo "  python3 trigger_feature.py"
echo ""
echo "💡 Note: Agents appear 'stuck' but are actually listening for messages!"
echo "   This is normal behavior - they're waiting for work."