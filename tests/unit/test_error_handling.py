#!/usr/bin/env python3
"""
Test script to demonstrate improved error handling in MAF
"""

import os
import sys

# Add parent directories to path to import from multi_agent_framework
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from multi_agent_framework.core.error_handler import (
    error_handler, ErrorCategory, ErrorLevel,
    handle_api_key_error, handle_task_error, handle_agent_error
)


def test_api_key_errors():
    """Test API key error handling"""
    print("=== Testing API Key Errors ===\n")
    
    # Test missing API key
    try:
        raise ValueError("OPENAI_API_KEY environment variable not set.")
    except Exception as e:
        handle_api_key_error(e, "openai", "OPENAI_API_KEY")
    
    print("\n")
    
    # Test invalid API key
    try:
        raise Exception("Invalid API key: Unauthorized (401)")
    except Exception as e:
        handle_api_key_error(e, "anthropic", "ANTHROPIC_API_KEY")


def test_network_errors():
    """Test network error handling"""
    print("\n=== Testing Network Errors ===\n")
    
    # Test rate limit
    try:
        raise Exception("Rate limit exceeded (429). Please try again later.")
    except Exception as e:
        error_handler.handle_error(
            e,
            ErrorCategory.NETWORK,
            {'service': 'OpenAI', 'wait_time': 60},
            ErrorLevel.WARNING
        )
    
    print("\n")
    
    # Test connection error
    try:
        raise Exception("Connection refused: Unable to reach server")
    except Exception as e:
        error_handler.handle_error(
            e,
            ErrorCategory.NETWORK,
            {'service': 'Gemini API'},
            ErrorLevel.ERROR
        )


def test_task_errors():
    """Test task execution error handling"""
    print("\n=== Testing Task Errors ===\n")
    
    # Test task failure
    try:
        raise Exception("Failed to generate code: Invalid syntax in prompt")
    except Exception as e:
        handle_task_error(e, "task_001", "Code generation failed")
    
    print("\n")
    
    # Test task timeout
    try:
        raise Exception("Task execution timed out after 300 seconds")
    except Exception as e:
        error_handler.handle_error(
            e,
            ErrorCategory.TASK_EXECUTION,
            {
                'task_id': 'task_002',
                'duration': 300,
                'suggestion': 'Consider breaking the task into smaller parts'
            },
            ErrorLevel.ERROR
        )


def test_file_errors():
    """Test file system error handling"""
    print("\n=== Testing File System Errors ===\n")
    
    # Test file not found
    try:
        raise FileNotFoundError("No such file or directory: /app/config.json")
    except Exception as e:
        error_handler.handle_error(
            e,
            ErrorCategory.FILE_SYSTEM,
            {'file_path': '/app/config.json'},
            ErrorLevel.ERROR
        )
    
    print("\n")
    
    # Test permission denied
    try:
        raise PermissionError("Access denied: /etc/protected.conf")
    except Exception as e:
        error_handler.handle_error(
            e,
            ErrorCategory.FILE_SYSTEM,
            {'file_path': '/etc/protected.conf'},
            ErrorLevel.ERROR
        )


def test_agent_errors():
    """Test agent communication error handling"""
    print("\n=== Testing Agent Communication Errors ===\n")
    
    # Test agent not responding
    try:
        raise Exception("No response from agent after 30 seconds")
    except Exception as e:
        handle_agent_error(e, "backend_agent", "health check")
    
    print("\n")
    
    # Test invalid message format
    try:
        raise Exception("Invalid JSON in message payload")
    except Exception as e:
        error_handler.handle_error(
            e,
            ErrorCategory.AGENT_COMMUNICATION,
            {
                'agent_name': 'frontend_agent',
                'details': 'Invalid message format'
            },
            ErrorLevel.ERROR
        )


def test_configuration_errors():
    """Test configuration error handling"""
    print("\n=== Testing Configuration Errors ===\n")
    
    # Test missing configuration
    try:
        raise Exception("Configuration file not found")
    except Exception as e:
        error_handler.handle_error(
            e,
            ErrorCategory.CONFIGURATION,
            {},
            ErrorLevel.ERROR
        )
    
    print("\n")
    
    # Test invalid configuration
    try:
        raise Exception("Invalid value for 'max_retries': expected int, got string")
    except Exception as e:
        error_handler.handle_error(
            e,
            ErrorCategory.CONFIGURATION,
            {
                'field': 'max_retries',
                'expected': 'integer',
                'actual': 'string'
            },
            ErrorLevel.ERROR
        )


def test_dependency_errors():
    """Test dependency error handling"""
    print("\n=== Testing Dependency Errors ===\n")
    
    # Test missing dependency
    try:
        raise ImportError("No module named 'kafka'")
    except Exception as e:
        error_handler.handle_error(
            e,
            ErrorCategory.DEPENDENCY,
            {'package': 'kafka-python', 'module': 'kafka'},
            ErrorLevel.ERROR
        )


if __name__ == "__main__":
    print("Multi-Agent Framework - Error Handling Test\n")
    print("This demonstrates the improved error messages and handling.\n")
    
    test_api_key_errors()
    test_network_errors()
    test_task_errors()
    test_file_errors()
    test_agent_errors()
    test_configuration_errors()
    test_dependency_errors()
    
    print("\n✅ Error handling test complete!")