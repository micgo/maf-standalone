#!/usr/bin/env python3
"""
Test script for the Multi-Agent Framework
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path

# Add parent directories to path to import from multi_agent_framework
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from multi_agent_framework.core.project_config import ProjectConfig
from multi_agent_framework.core.agent_factory import create_agent, AgentFactory
from multi_agent_framework.core.message_bus_configurable import MessageBus

def test_project_config():
    """Test project configuration functionality"""
    print("Testing Project Configuration...")
    
    # Create a temporary test project
    with tempfile.TemporaryDirectory() as tmp_dir:
        # Create a mock Next.js project
        package_json = {
            "name": "test-project",
            "dependencies": {
                "react": "^18.0.0",
                "next": "^13.0.0"
            }
        }
        
        with open(os.path.join(tmp_dir, "package.json"), "w") as f:
            import json
            json.dump(package_json, f)
        
        # Create next.config.js
        with open(os.path.join(tmp_dir, "next.config.js"), "w") as f:
            f.write("module.exports = {}")
        
        # Initialize project config
        config = ProjectConfig.initialize_project(tmp_dir)
        
        assert config.config["project_type"] == "nextjs", "Failed to detect Next.js project"
        assert config.get_project_root() == tmp_dir, "Project root mismatch"
        assert os.path.exists(config.get_message_queue_dir()), "Message queue dir not created"
        assert os.path.exists(config.get_log_dir()), "Log dir not created"
        
        print("✓ Project configuration test passed")
        return config

def test_agent_creation(project_config):
    """Test agent creation with project config"""
    print("\nTesting Agent Creation...")
    
    # Test creating agents with project config
    try:
        # Create orchestrator agent
        orchestrator = create_agent(
            "orchestrator", 
            mode="polling",
            project_config=project_config
        )
        assert orchestrator.name == "orchestrator", "Agent name mismatch"
        assert orchestrator.project_config == project_config, "Project config not set"
        print("✓ Created orchestrator agent")
        
        # Create frontend agent
        frontend = create_agent(
            "frontend",
            mode="polling", 
            project_config=project_config
        )
        assert frontend.name == "frontend_agent", "Frontend agent name mismatch"
        print("✓ Created frontend agent")
        
        # Create backend agent
        backend = create_agent(
            "backend",
            mode="polling",
            project_config=project_config
        )
        assert backend.name == "backend_agent", "Backend agent name mismatch"
        print("✓ Created backend agent")
        
    except Exception as e:
        print(f"✗ Agent creation failed: {e}")
        raise

def test_message_bus(project_config):
    """Test message bus functionality"""
    print("\nTesting Message Bus...")
    
    # Create message bus with project config
    message_bus = MessageBus(project_config.get_message_queue_dir())
    
    # Initialize inboxes
    agents = ["orchestrator", "frontend_agent", "backend_agent"]
    message_bus.initialize_agent_inboxes(agents)
    
    # Test sending message
    test_message = {
        "sender": "test",
        "recipient": "orchestrator",
        "type": "test",
        "content": "Test message",
        "task_id": "test-123"
    }
    
    message_bus.send_message("orchestrator", test_message)
    
    # Test receiving message
    messages = message_bus.receive_messages("orchestrator")
    assert len(messages) == 1, "Message not received"
    assert messages[0]["content"] == "Test message", "Message content mismatch"
    
    # Test queue status
    status = message_bus.get_queue_status()
    assert status["orchestrator"] == 0, "Queue should be empty after receiving"
    
    print("✓ Message bus test passed")

def test_event_driven_agents(project_config):
    """Test event-driven agent creation"""
    print("\nTesting Event-Driven Agents...")
    
    try:
        # Create event-driven orchestrator
        orchestrator = create_agent(
            "orchestrator",
            mode="event_driven",
            project_config=project_config
        )
        assert orchestrator.name == "orchestrator", "Event-driven agent name mismatch"
        print("✓ Created event-driven orchestrator")
        
        # Create event-driven frontend agent  
        frontend = create_agent(
            "frontend",
            mode="event_driven",
            project_config=project_config
        )
        print("✓ Created event-driven frontend agent")
        
    except Exception as e:
        print(f"✗ Event-driven agent creation failed: {e}")
        raise

def main():
    """Run all tests"""
    print("Multi-Agent Framework Test Suite")
    print("=" * 50)
    
    try:
        # Test project configuration
        project_config = test_project_config()
        
        # Test agent creation
        test_agent_creation(project_config)
        
        # Test message bus
        test_message_bus(project_config)
        
        # Test event-driven agents
        test_event_driven_agents(project_config)
        
        print("\n" + "=" * 50)
        print("✅ All tests passed!")
        
    except Exception as e:
        print("\n" + "=" * 50)
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()