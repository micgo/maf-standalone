#!/bin/bash

# Quick Agent Status Checker

PROJECT_ROOT="/Users/micgo/Development/pack429/multi_agent_framework"

echo "🔍 Multi-Agent Framework Status Check"
echo "======================================"

# Check if virtual environment exists
if [ ! -d "$PROJECT_ROOT/venv" ]; then
    echo "❌ Virtual environment not found at $PROJECT_ROOT/venv"
    echo "Run: cd multi_agent_framework && ./setup_venv.sh"
    exit 1
fi

echo "✅ Virtual environment: Found"

# Check if iTerm2 is running
if pgrep -f "iTerm" >/dev/null; then
    echo "✅ iTerm2: Running"
    
    # Count iTerm2 tabs (approximate)
    tab_count=$(osascript -e 'tell application "iTerm2" to count tabs of current window' 2>/dev/null || echo "Unknown")
    echo "📊 iTerm2 tabs: $tab_count"
else
    echo "❌ iTerm2: Not running"
fi

# Check system health if possible
if [ -f "$PROJECT_ROOT/venv/bin/activate" ]; then
    echo ""
    echo "🏥 System Health:"
    cd "$PROJECT_ROOT"
    source venv/bin/activate
    python3 recovery_tool.py health | grep -E "(System Status|Total Tasks|Completion Rate)"
else
    echo "⚠️  Cannot check system health - virtual environment issue"
fi

echo ""
echo "🚀 Quick Actions:"
echo "  Launch agents: ./launch_agents.sh"
echo "  Full health:   source venv/bin/activate && python3 recovery_tool.py health"
echo "  Agent status:  source venv/bin/activate && python3 recovery_tool.py agents"  
echo "  New feature:   source venv/bin/activate && python3 trigger_feature.py"