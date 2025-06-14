#!/usr/bin/env python3
"""
Centralized error handling and user-friendly error messages
"""
import os
import sys
import traceback
import logging
from typing import Dict, Any, Optional, Callable
from datetime import datetime
from enum import Enum


class ErrorLevel(Enum):
    """Error severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class ErrorCategory(Enum):
    """Error categories for better organization"""
    API_KEY = "api_key"
    NETWORK = "network"
    FILE_SYSTEM = "file_system"
    CONFIGURATION = "configuration"
    TASK_EXECUTION = "task_execution"
    AGENT_COMMUNICATION = "agent_communication"
    DEPENDENCY = "dependency"
    VALIDATION = "validation"
    SYSTEM = "system"


class ErrorHandler:
    """Centralized error handling with user-friendly messages"""
    
    # User-friendly error messages
    ERROR_MESSAGES = {
        ErrorCategory.API_KEY: {
            "missing": "API key not found. Please set {key_name} environment variable.\nExample: export {key_name}=your_api_key_here",
            "invalid": "Invalid API key. Please check your {provider} API key.\nYou can get a new key from: {url}",
            "expired": "API key has expired. Please renew your {provider} subscription.",
        },
        ErrorCategory.NETWORK: {
            "connection": "Unable to connect to {service}. Please check your internet connection.",
            "timeout": "Request timed out. The {service} might be slow or unavailable.",
            "rate_limit": "Rate limit exceeded for {service}. Please wait {wait_time} seconds before trying again.",
        },
        ErrorCategory.FILE_SYSTEM: {
            "not_found": "File not found: {file_path}\nPlease ensure the file exists and the path is correct.",
            "permission": "Permission denied accessing: {file_path}\nPlease check file permissions.",
            "disk_space": "Insufficient disk space to write: {file_path}",
        },
        ErrorCategory.CONFIGURATION: {
            "missing_config": "Configuration file not found. Run 'maf init' to create one.",
            "invalid_config": "Invalid configuration: {field}\nExpected: {expected}\nGot: {actual}",
            "incompatible": "Incompatible configuration settings: {details}",
        },
        ErrorCategory.TASK_EXECUTION: {
            "failed": "Task '{task_id}' failed: {reason}\nSuggestion: {suggestion}",
            "timeout": "Task '{task_id}' timed out after {duration} seconds.",
            "invalid_input": "Invalid task input: {details}",
        },
        ErrorCategory.AGENT_COMMUNICATION: {
            "no_response": "Agent '{agent_name}' is not responding. It might be offline or busy.",
            "invalid_message": "Invalid message format from '{agent_name}': {details}",
            "delivery_failed": "Failed to deliver message to '{agent_name}': {reason}",
        },
        ErrorCategory.DEPENDENCY: {
            "missing": "Required dependency '{package}' is not installed.\nInstall with: pip install {package}",
            "version": "Incompatible version of '{package}'. Required: {required}, Found: {found}",
            "import": "Failed to import '{module}': {reason}",
        },
        ErrorCategory.VALIDATION: {
            "invalid_type": "Invalid type for '{field}'. Expected {expected}, got {actual}.",
            "missing_field": "Required field '{field}' is missing.",
            "constraint": "Value '{value}' violates constraint: {constraint}",
        },
        ErrorCategory.SYSTEM: {
            "memory": "Insufficient memory. Consider closing other applications or upgrading your system.",
            "cpu": "High CPU usage detected. Performance may be degraded.",
            "unexpected": "An unexpected error occurred: {details}\nPlease report this issue.",
        }
    }
    
    # API provider URLs for help
    API_URLS = {
        "openai": "https://platform.openai.com/api-keys",
        "anthropic": "https://console.anthropic.com/account/keys",
        "gemini": "https://makersuite.google.com/app/apikey",
        "google": "https://console.cloud.google.com/apis/credentials"
    }
    
    def __init__(self, log_file: Optional[str] = None):
        """Initialize error handler with optional logging"""
        self.log_file = log_file
        self.logger = self._setup_logger()
        
    def _setup_logger(self) -> logging.Logger:
        """Set up logging configuration"""
        logger = logging.getLogger("maf.errors")
        logger.setLevel(logging.DEBUG)
        
        # Console handler with user-friendly format
        console_handler = logging.StreamHandler(sys.stderr)
        console_handler.setLevel(logging.INFO)
        console_format = logging.Formatter('%(levelname)s: %(message)s')
        console_handler.setFormatter(console_format)
        logger.addHandler(console_handler)
        
        # File handler with detailed format
        if self.log_file:
            file_handler = logging.FileHandler(self.log_file)
            file_handler.setLevel(logging.DEBUG)
            file_format = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            file_handler.setFormatter(file_format)
            logger.addHandler(file_handler)
            
        return logger
        
    def handle_error(self, 
                    error: Exception,
                    category: ErrorCategory,
                    context: Dict[str, Any],
                    level: ErrorLevel = ErrorLevel.ERROR) -> str:
        """Handle an error with user-friendly messaging"""
        # Get appropriate error message template
        message_template = self._get_error_message(error, category, context)
        
        # Format the message with context
        try:
            user_message = message_template.format(**context)
        except KeyError:
            user_message = f"{category.value} error: {str(error)}"
            
        # Add helpful suggestions
        suggestion = self._get_suggestion(error, category, context)
        if suggestion:
            user_message += f"\n💡 {suggestion}"
            
        # Log the error
        self._log_error(error, category, context, user_message, level)
        
        # Display to user
        self._display_error(user_message, level)
        
        return user_message
        
    def _get_error_message(self, error: Exception, category: ErrorCategory, context: Dict[str, Any]) -> str:
        """Get appropriate error message template"""
        # Try to match specific error type
        error_type = self._identify_error_type(error, category, context)
        
        category_messages = self.ERROR_MESSAGES.get(category, {})
        message = category_messages.get(error_type, str(error))
        
        return message
        
    def _identify_error_type(self, error: Exception, category: ErrorCategory, context: Dict[str, Any]) -> str:
        """Identify specific error type within category"""
        error_str = str(error).lower()
        
        if category == ErrorCategory.API_KEY:
            if "not found" in error_str or "not set" in error_str:
                return "missing"
            elif "invalid" in error_str or "unauthorized" in error_str:
                return "invalid"
            elif "expired" in error_str:
                return "expired"
                
        elif category == ErrorCategory.NETWORK:
            if "connection" in error_str or "refused" in error_str:
                return "connection"
            elif "timeout" in error_str:
                return "timeout"
            elif "rate limit" in error_str or "429" in error_str:
                return "rate_limit"
                
        elif category == ErrorCategory.FILE_SYSTEM:
            if "not found" in error_str or "no such file" in error_str:
                return "not_found"
            elif "permission" in error_str or "access denied" in error_str:
                return "permission"
            elif "no space" in error_str:
                return "disk_space"
                
        elif category == ErrorCategory.TASK_EXECUTION:
            if "timeout" in error_str:
                return "timeout"
            elif "invalid" in error_str:
                return "invalid_input"
            else:
                return "failed"
                
        return "unknown"
        
    def _get_suggestion(self, error: Exception, category: ErrorCategory, context: Dict[str, Any]) -> Optional[str]:
        """Get helpful suggestion for the error"""
        suggestions = {
            ErrorCategory.API_KEY: self._get_api_key_suggestion,
            ErrorCategory.NETWORK: self._get_network_suggestion,
            ErrorCategory.FILE_SYSTEM: self._get_file_suggestion,
            ErrorCategory.CONFIGURATION: self._get_config_suggestion,
            ErrorCategory.TASK_EXECUTION: self._get_task_suggestion,
            ErrorCategory.AGENT_COMMUNICATION: self._get_agent_suggestion,
            ErrorCategory.DEPENDENCY: self._get_dependency_suggestion,
        }
        
        handler = suggestions.get(category)
        if handler:
            return handler(error, context)
            
        return None
        
    def _get_api_key_suggestion(self, error: Exception, context: Dict[str, Any]) -> str:
        """Get suggestion for API key errors"""
        provider = context.get('provider', 'your provider')
        
        if 'missing' in str(error).lower():
            return f"Set your API key: export {context.get('key_name', 'API_KEY')}=your_key_here"
        elif 'invalid' in str(error).lower():
            url = self.API_URLS.get(provider.lower(), "your provider's dashboard")
            return f"Get a new API key from: {url}"
            
        return "Check your API key configuration"
        
    def _get_network_suggestion(self, error: Exception, context: Dict[str, Any]) -> str:
        """Get suggestion for network errors"""
        if 'timeout' in str(error).lower():
            return "Try again in a few moments or check service status"
        elif 'connection' in str(error).lower():
            return "Check your internet connection and firewall settings"
        elif 'rate limit' in str(error).lower():
            return "Consider implementing request throttling or upgrading your plan"
            
        return "Check network connectivity and service availability"
        
    def _get_file_suggestion(self, error: Exception, context: Dict[str, Any]) -> str:
        """Get suggestion for file system errors"""
        if 'not found' in str(error).lower():
            return "Verify the file path and ensure the file exists"
        elif 'permission' in str(error).lower():
            return "Try running with appropriate permissions or check file ownership"
            
        return "Check file system permissions and available space"
        
    def _get_config_suggestion(self, error: Exception, context: Dict[str, Any]) -> str:
        """Get suggestion for configuration errors"""
        return "Run 'maf init' to create a default configuration"
        
    def _get_task_suggestion(self, error: Exception, context: Dict[str, Any]) -> str:
        """Get suggestion for task execution errors"""
        return "Try breaking down the task into smaller steps or check task requirements"
        
    def _get_agent_suggestion(self, error: Exception, context: Dict[str, Any]) -> str:
        """Get suggestion for agent communication errors"""
        agent_name = context.get('agent_name', 'the agent')
        return f"Ensure {agent_name} is running and properly configured"
        
    def _get_dependency_suggestion(self, error: Exception, context: Dict[str, Any]) -> str:
        """Get suggestion for dependency errors"""
        package = context.get('package', 'the required package')
        return f"Install with: pip install {package}"
        
    def _log_error(self, error: Exception, category: ErrorCategory, 
                   context: Dict[str, Any], user_message: str, level: ErrorLevel):
        """Log error with full details"""
        # Log user-friendly message
        log_method = getattr(self.logger, level.value, self.logger.error)
        log_method(user_message)
        
        # Log technical details at debug level
        self.logger.debug(f"Error Category: {category.value}")
        self.logger.debug(f"Error Type: {type(error).__name__}")
        self.logger.debug(f"Error Details: {str(error)}")
        self.logger.debug(f"Context: {context}")
        
        # Log full traceback at debug level
        if level in [ErrorLevel.ERROR, ErrorLevel.CRITICAL]:
            self.logger.debug("Traceback:\n" + traceback.format_exc())
            
    def _display_error(self, message: str, level: ErrorLevel):
        """Display error to user with appropriate formatting"""
        # Color codes for terminal
        colors = {
            ErrorLevel.INFO: '\033[94m',      # Blue
            ErrorLevel.WARNING: '\033[93m',   # Yellow
            ErrorLevel.ERROR: '\033[91m',     # Red
            ErrorLevel.CRITICAL: '\033[95m',  # Magenta
        }
        
        reset_color = '\033[0m'
        
        # Icons for different levels
        icons = {
            ErrorLevel.INFO: 'ℹ️ ',
            ErrorLevel.WARNING: '⚠️ ',
            ErrorLevel.ERROR: '❌ ',
            ErrorLevel.CRITICAL: '🚨 ',
        }
        
        # Format and display
        color = colors.get(level, '')
        icon = icons.get(level, '')
        
        print(f"\n{color}{icon}{message}{reset_color}\n", file=sys.stderr)
        
    def wrap_function(self, func: Callable, category: ErrorCategory, 
                     context_provider: Optional[Callable] = None):
        """Decorator to wrap functions with error handling"""
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                # Get context from provider or use default
                context = {}
                if context_provider:
                    context = context_provider(*args, **kwargs)
                    
                # Handle the error
                self.handle_error(e, category, context)
                
                # Re-raise for caller to handle if needed
                raise
                
        return wrapper


# Global error handler instance
error_handler = ErrorHandler()


def handle_api_key_error(error: Exception, provider: str, key_name: str):
    """Convenience function for API key errors"""
    context = {
        'provider': provider,
        'key_name': key_name,
        'url': ErrorHandler.API_URLS.get(provider.lower(), '')
    }
    return error_handler.handle_error(error, ErrorCategory.API_KEY, context)


def handle_task_error(error: Exception, task_id: str, reason: str = "Unknown"):
    """Convenience function for task execution errors"""
    context = {
        'task_id': task_id,
        'reason': reason,
        'suggestion': 'Check task requirements and agent capabilities'
    }
    return error_handler.handle_error(error, ErrorCategory.TASK_EXECUTION, context)


def handle_agent_error(error: Exception, agent_name: str, operation: str = "communication"):
    """Convenience function for agent communication errors"""
    context = {
        'agent_name': agent_name,
        'details': f"during {operation}",
        'reason': str(error)
    }
    return error_handler.handle_error(error, ErrorCategory.AGENT_COMMUNICATION, context)