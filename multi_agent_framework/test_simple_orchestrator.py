#!/usr/bin/env python3
"""
Simple test to debug orchestrator
"""

import sys
import os
import time

# Add framework to path
framework_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, framework_root)

from agents.event_driven_orchestrator_agent import EventDrivenOrchestratorAgent

# Test if orchestrator can generate responses
def test_orchestrator():
    print("=== Testing Orchestrator LLM ===\n")
    
    # Create orchestrator
    orchestrator = EventDrivenOrchestratorAgent()
    
    # Test LLM generation directly
    prompt = "Say hello in JSON format: {\"message\": \"your message\"}"
    
    print(f"Testing LLM with prompt: {prompt}")
    response = orchestrator._generate_response(prompt)
    print(f"Response: {response}")
    
    # Test the feature breakdown
    print("\n=== Testing Feature Breakdown ===")
    orchestrator._break_down_feature("test-123", "Create a simple login page")
    

if __name__ == "__main__":
    test_orchestrator()