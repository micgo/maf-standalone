#!/usr/bin/env python3
"""
Test script to verify agent communication and basic functionality.
"""

import os
import sys
import time
from datetime import datetime

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

from core.message_bus import MessageBus
from core.project_state_manager import ProjectStateManager

def test_message_bus():
    """Test the message bus functionality."""
    print("🔄 Testing Message Bus...")
    
    try:
        bus = MessageBus()
        
        # Send a test message
        test_message = {
            "sender": "test_script",
            "recipient": "orchestrator_agent", 
            "type": "test",
            "content": "Hello from test script",
            "timestamp": time.time()
        }
        
        bus.send_message("orchestrator_agent", test_message)
        print("✅ Message sent successfully")
        
        # Try to receive messages
        messages = bus.receive_messages("test_script")
        print(f"📥 Received {len(messages)} messages")
        
        return True
    except Exception as e:
        print(f"❌ Message bus test failed: {e}")
        return False

def test_project_state():
    """Test the project state manager."""
    print("🗄️  Testing Project State Manager...")
    
    try:
        state_manager = ProjectStateManager()
        
        # Get current state
        stats = state_manager.get_task_statistics()
        print(f"📊 Total tasks: {stats['total_tasks']}")
        print(f"📈 Completion rate: {stats['completion_rate']:.1%}")
        
        # Test health check
        health = state_manager.task_health_check()
        status = "🟢 HEALTHY" if health['healthy'] else "🔴 ISSUES"
        print(f"🏥 System health: {status}")
        
        return True
    except Exception as e:
        print(f"❌ Project state test failed: {e}")
        return False

def test_agent_import():
    """Test importing agent classes."""
    print("🤖 Testing Agent Imports...")
    
    try:
        from agents.orchestrator_agent import OrchestratorAgent
        print("✅ Orchestrator agent imported")
        
        from agents.specialized.frontend_agent import FrontendAgent
        print("✅ Frontend agent imported")
        
        from agents.specialized.backend_agent import BackendAgent  
        print("✅ Backend agent imported")
        
        return True
    except Exception as e:
        print(f"❌ Agent import test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_environment():
    """Check environment setup."""
    print("🔧 Checking Environment...")
    
    # Check API keys
    gemini_key = os.getenv('GEMINI_API_KEY')
    anthropic_key = os.getenv('ANTHROPIC_API_KEY')
    openai_key = os.getenv('OPENAI_API_KEY')
    
    print(f"🔑 GEMINI_API_KEY: {'✅ Set' if gemini_key else '❌ Not set'}")
    print(f"🔑 ANTHROPIC_API_KEY: {'✅ Set' if anthropic_key else '❌ Not set'}")
    print(f"🔑 OPENAI_API_KEY: {'✅ Set' if openai_key else '❌ Not set'}")
    
    # Check directories
    required_dirs = ['agents', 'core', 'message_queue']
    for dir_name in required_dirs:
        exists = os.path.exists(dir_name)
        print(f"📁 {dir_name}/: {'✅ Exists' if exists else '❌ Missing'}")
    
    return gemini_key is not None  # At least Gemini key should be set

def main():
    """Run all tests."""
    print("🧪 Multi-Agent Framework Communication Test")
    print("=" * 50)
    print(f"⏰ Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    tests = [
        ("Environment Check", check_environment),
        ("Agent Import Test", test_agent_import),
        ("Message Bus Test", test_message_bus),
        ("Project State Test", test_project_state),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{test_name}")
        print("-" * len(test_name))
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} crashed: {e}")
            results.append((test_name, False))
        print()
    
    # Summary
    print("📋 Test Summary:")
    print("=" * 20)
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status} {test_name}")
    
    print(f"\n🎯 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The framework is ready to use.")
        print("\n🚀 Next steps:")
        print("  1. Launch agents: ./launch_agents_verbose.sh")
        print("  2. Start development: python3 trigger_feature.py")
    else:
        print("⚠️  Some tests failed. Check the errors above.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)