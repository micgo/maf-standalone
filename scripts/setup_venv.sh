#!/bin/bash

# Multi-Agent Framework Virtual Environment Setup Script

echo "🤖 Setting up Multi-Agent Framework Virtual Environment..."

# Create virtual environment
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
    echo "✅ Virtual environment created"
else
    echo "📦 Virtual environment already exists"
fi

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip

# Install requirements
echo "📥 Installing framework dependencies..."
pip install -r requirements.txt

echo ""
echo "✅ Setup complete! 🎉"
echo ""
echo "To activate the virtual environment in the future, run:"
echo "  source venv/bin/activate"
echo ""
echo "To deactivate when done:"
echo "  deactivate"
echo ""
echo "Environment variables needed (add to .env file):"
echo "  GEMINI_API_KEY=your_gemini_key_here"
echo "  ANTHROPIC_API_KEY=your_anthropic_key_here (optional)"
echo "  OPENAI_API_KEY=your_openai_key_here (optional)"
echo ""
echo "To test the framework:"
echo "  python -m multi_agent_framework.recovery_tool health"
echo "  pytest tests/"