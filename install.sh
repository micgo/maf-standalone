#!/bin/bash
#
# Multi-Agent Framework Installation Script
#

echo "🚀 Multi-Agent Framework Installer"
echo "=================================="

# Check Python version
echo "Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
required_version="3.8"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "❌ Python $required_version or higher is required. Found: $python_version"
    exit 1
fi

echo "✅ Python version: $python_version"

# Create virtual environment
echo ""
echo "Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo ""
echo "Upgrading pip..."
pip install --upgrade pip

# Install the framework
echo ""
echo "Installing Multi-Agent Framework..."
pip install -e .

# Run tests
echo ""
echo "Running tests..."
python test_framework.py

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Installation successful!"
    echo ""
    echo "Next steps:"
    echo "1. Activate the virtual environment: source venv/bin/activate"
    echo "2. Initialize a project: maf init /path/to/your/project"
    echo "3. Configure API keys in .env file"
    echo "4. Launch agents: maf launch"
    echo "5. Start developing: maf trigger 'Your feature description'"
else
    echo ""
    echo "❌ Installation tests failed. Please check the error messages above."
    exit 1
fi