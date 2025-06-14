"""
Project-specific configuration for Multi-Agent Framework
"""
import os
import json
from typing import Dict, Optional, Any
from pathlib import Path


class ProjectConfig:
    """Configuration for a specific project using the Multi-Agent Framework"""
    
    DEFAULT_CONFIG = {
        "project_name": "Unnamed Project",
        "project_root": None,
        "message_queue_dir": "message_queue",
        "state_file": "project_state.json",
        "event_bus": {
            "type": "inmemory",
            "kafka_config": {
                "bootstrap_servers": ["localhost:9092"],
                "consumer_group": "multi-agent-framework",
                "max_workers": 10
            }
        },
        "agents": {
            "model_provider": "gemini",
            "model_name": "gemini-2.0-flash-exp",
            "enabled_agents": [
                "orchestrator",
                "frontend",
                "backend",
                "database",
                "security",
                "qa",
                "devops",
                "docs",
                "ux_ui"
            ]
        },
        "retry_config": {
            "max_attempts": 3,
            "delay_seconds": 5
        },
        "task_config": {
            "timeout_minutes": 30,
            "max_concurrent_per_agent": 1
        }
    }
    
    CONFIG_FILE_NAME = ".maf-config.json"
    
    def __init__(self, project_root: Optional[str] = None, config_file: Optional[str] = None):
        """
        Initialize project configuration
        
        Args:
            project_root: Path to the project root directory
            config_file: Path to configuration file (defaults to .maf-config.json in project root)
        """
        self.config = self.DEFAULT_CONFIG.copy()
        
        if project_root:
            self.config["project_root"] = os.path.abspath(project_root)
        else:
            # Try to detect project root from current directory
            self.config["project_root"] = os.getcwd()
        
        # Load configuration from file if it exists
        if config_file:
            config_path = config_file
        else:
            config_path = os.path.join(self.config["project_root"], self.CONFIG_FILE_NAME)
        
        if os.path.exists(config_path):
            self.load_from_file(config_path)
        
        # Ensure all paths are absolute
        self._resolve_paths()
    
    def load_from_file(self, config_path: str) -> None:
        """Load configuration from JSON file"""
        try:
            with open(config_path, 'r') as f:
                file_config = json.load(f)
                # Update config with file values, preserving defaults for missing keys
                self._deep_update(self.config, file_config)
        except Exception as e:
            print(f"Warning: Could not load config from {config_path}: {e}")
    
    def save_to_file(self, config_path: Optional[str] = None) -> None:
        """Save configuration to JSON file"""
        if not config_path:
            config_path = os.path.join(self.config["project_root"], self.CONFIG_FILE_NAME)
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        
        with open(config_path, 'w') as f:
            json.dump(self.config, f, indent=4)
    
    def _deep_update(self, base: Dict, update: Dict) -> None:
        """Deep update dictionary"""
        for key, value in update.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._deep_update(base[key], value)
            else:
                base[key] = value
    
    def _resolve_paths(self) -> None:
        """Convert relative paths to absolute paths based on project root"""
        project_root = self.config["project_root"]
        
        # Resolve message queue directory
        if not os.path.isabs(self.config["message_queue_dir"]):
            self.config["message_queue_dir"] = os.path.join(
                project_root, self.config["message_queue_dir"]
            )
        
        # Resolve state file path
        if not os.path.isabs(self.config["state_file"]):
            self.config["state_file"] = os.path.join(
                project_root, self.config["state_file"]
            )
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value with dot notation support"""
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set(self, key: str, value: Any) -> None:
        """Set configuration value with dot notation support"""
        keys = key.split('.')
        config = self.config
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
    
    @property
    def project_root(self) -> str:
        """Get project root directory"""
        return self.config["project_root"]
    
    @property
    def message_queue_dir(self) -> str:
        """Get message queue directory"""
        return self.config["message_queue_dir"]
    
    @property
    def state_file(self) -> str:
        """Get project state file path"""
        return self.config["state_file"]
    
    @property
    def enabled_agents(self) -> list:
        """Get list of enabled agents"""
        return self.config["agents"]["enabled_agents"]
    
    def validate(self) -> bool:
        """Validate configuration"""
        # Check if project root exists
        if not os.path.exists(self.project_root):
            raise ValueError(f"Project root does not exist: {self.project_root}")
        
        # Check if project root is a directory
        if not os.path.isdir(self.project_root):
            raise ValueError(f"Project root is not a directory: {self.project_root}")
        
        return True
    
    def initialize_project(self) -> None:
        """Initialize project structure for multi-agent framework"""
        # Create message queue directory
        os.makedirs(self.message_queue_dir, exist_ok=True)
        
        # Create inbox files for each agent
        for agent in self.enabled_agents:
            inbox_file = os.path.join(self.message_queue_dir, f"{agent}_inbox.json")
            if not os.path.exists(inbox_file):
                with open(inbox_file, 'w') as f:
                    json.dump([], f)
        
        # Create initial state file
        if not os.path.exists(self.state_file):
            with open(self.state_file, 'w') as f:
                json.dump({"features": {}, "tasks": {}}, f)
        
        # Save configuration file
        self.save_to_file()
        
        print(f"Initialized Multi-Agent Framework for project: {self.project_root}")
        print(f"Configuration saved to: {os.path.join(self.project_root, self.CONFIG_FILE_NAME)}")


# Global configuration instance
_project_config: Optional[ProjectConfig] = None


def get_project_config() -> ProjectConfig:
    """Get the global project configuration instance"""
    if _project_config is None:
        raise RuntimeError("Project configuration not initialized. Call init_project_config() first.")
    return _project_config


def init_project_config(project_root: Optional[str] = None, config_file: Optional[str] = None) -> ProjectConfig:
    """Initialize the global project configuration"""
    global _project_config
    _project_config = ProjectConfig(project_root, config_file)
    return _project_config