#!/usr/bin/env python3
"""
Simple tests for error handler that match actual implementation
"""
import os
import sys
from unittest import TestCase, mock
from unittest.mock import Mock, patch, MagicMock
from io import StringIO
import logging

from multi_agent_framework.core.error_handler import (
    ErrorHandler, ErrorLevel, ErrorCategory,
    handle_api_key_error, handle_task_error, handle_agent_error
)


class TestErrorHandlerSimple(TestCase):
    """Test ErrorHandler basic functionality"""
    
    def setUp(self):
        """Set up test environment"""
        self.handler = ErrorHandler()
    
    def test_initialization(self):
        """Test error handler initialization"""
        self.assertIsNotNone(self.handler.logger)
        self.assertIsInstance(self.handler.logger, logging.Logger)
    
    def test_handle_error_basic(self):
        """Test basic error handling"""
        # Errors are printed to stderr
        with patch('sys.stderr', new=StringIO()) as fake_err:
            self.handler.handle_error(
                KeyError("test_key"),
                ErrorCategory.API_KEY,
                context={"key_name": "TEST_KEY"}
            )
            output = fake_err.getvalue()
            
            # Should contain error indicator
            self.assertIn("❌", output)
    
    def test_display_error_levels(self):
        """Test display with different error levels"""
        # Info level - goes to stderr
        with patch('sys.stderr', new=StringIO()) as fake_err:
            self.handler._display_error("Test info", ErrorLevel.INFO)
            output = fake_err.getvalue()
            self.assertIn("ℹ️", output)
        
        # Warning level
        with patch('sys.stderr', new=StringIO()) as fake_err:
            self.handler._display_error("Test warning", ErrorLevel.WARNING)
            output = fake_err.getvalue()
            self.assertIn("⚠️", output)
        
        # Error level
        with patch('sys.stderr', new=StringIO()) as fake_err:
            self.handler._display_error("Test error", ErrorLevel.ERROR)
            output = fake_err.getvalue()
            self.assertIn("❌", output)
    
    def test_critical_error_display(self):
        """Test critical error display"""
        with patch('sys.stderr', new=StringIO()) as fake_err:
            self.handler._display_error("Critical failure", ErrorLevel.CRITICAL)
            output = fake_err.getvalue()
            self.assertIn("🚨", output)
            self.assertIn("Critical failure", output)
    
    def test_wrap_function_decorator(self):
        """Test function wrapping as decorator"""
        # Create a function that might fail
        def test_func(x):
            if x < 0:
                raise ValueError("Negative value")
            return x * 2
        
        # Wrap it with error handling
        wrapped = self.handler.wrap_function(test_func, ErrorCategory.TASK_EXECUTION)
        
        # Test successful execution
        result = wrapped(5)
        self.assertEqual(result, 10)
        
        # Test error handling - should re-raise after handling
        with patch('sys.stderr', new=StringIO()):
            with self.assertRaises(ValueError):
                wrapped(-1)
    
    def test_standalone_error_functions(self):
        """Test standalone error handling functions"""
        # Test API key error
        with patch('sys.stderr', new=StringIO()) as fake_err:
            handle_api_key_error(
                KeyError("OPENAI_API_KEY"),
                "OpenAI",
                "OPENAI_API_KEY"
            )
            output = fake_err.getvalue()
            self.assertIn("❌", output)
        
        # Test task error
        with patch('sys.stderr', new=StringIO()) as fake_err:
            handle_task_error(
                RuntimeError("Task failed"),
                "task-123",
                "Database unavailable"
            )
            output = fake_err.getvalue()
            self.assertIn("❌", output)
        
        # Test agent error
        with patch('sys.stderr', new=StringIO()) as fake_err:
            handle_agent_error(
                ConnectionError("Agent offline"),
                "backend_agent",
                "message_passing"
            )
            output = fake_err.getvalue()
            self.assertIn("❌", output)
    
    def test_error_logging(self):
        """Test that errors are logged"""
        with patch.object(self.handler.logger, 'error') as mock_log:
            with patch('sys.stderr', new=StringIO()):
                self.handler.handle_error(
                    ValueError("Test error"),
                    ErrorCategory.VALIDATION,
                    context={"field": "email"}
                )
            
            # Verify logging was called
            mock_log.assert_called()
    
    def test_get_error_message_basic(self):
        """Test error message retrieval"""
        # This returns the string representation of the error
        message = self.handler._get_error_message(
            KeyError("TEST_KEY"),
            ErrorCategory.API_KEY,
            {}
        )
        self.assertEqual(message, "'TEST_KEY'")
    
    def test_identify_error_type_basic(self):
        """Test error type identification"""
        # Most errors return "unknown" unless specifically handled
        error_type = self.handler._identify_error_type(
            ValueError("test"),
            ErrorCategory.VALIDATION,
            {}
        )
        self.assertEqual(error_type, "unknown")
        
        # Rate limit detection
        error_type = self.handler._identify_error_type(
            Exception("Rate limit exceeded"),
            ErrorCategory.NETWORK,
            {}
        )
        self.assertEqual(error_type, "rate_limit")
    
    def test_suggestions_exist(self):
        """Test that suggestion methods exist and return strings"""
        # API key suggestion
        suggestion = self.handler._get_api_key_suggestion(
            KeyError("API_KEY"),
            {"key_name": "API_KEY"}
        )
        self.assertIsInstance(suggestion, str)
        self.assertIn("API", suggestion)
        
        # Network suggestion
        suggestion = self.handler._get_network_suggestion(
            ConnectionError("Failed"),
            {}
        )
        self.assertIsInstance(suggestion, str)
        
        # File suggestion
        suggestion = self.handler._get_file_suggestion(
            PermissionError("Denied"),
            {}
        )
        self.assertIsInstance(suggestion, str)


if __name__ == '__main__':
    import unittest
    unittest.main()