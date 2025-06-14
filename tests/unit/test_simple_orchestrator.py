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

from multi_agent_framework.agents.event_driven_orchestrator_agent import EventDrivenOrchestratorAgent

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
    
    # Initialize the feature first
    feature_id = "test-123"
    orchestrator._features[feature_id] = {
        'id': feature_id,
        'description': "Create a simple login page",
        'status': 'pending'
    }
    
    # Now break it down
    orchestrator._break_down_feature(feature_id, "Create a simple login page")
    
    # Check results
    assert feature_id in orchestrator._features
    assert orchestrator._features[feature_id]['status'] in ['in_progress', 'failed']
    

if __name__ == "__main__":
    test_orchestrator()