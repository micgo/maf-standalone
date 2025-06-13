"""
Project Configuration Module

Handles configuration for pointing the multi-agent framework at different projects.
"""

import os
import json
from typing import Dict, Any, Optional
from pathlib import Path


class ProjectConfig:
    """
    Manages project-specific configuration for the multi-agent framework.
    """
    
    DEFAULT_CONFIG = {
        "project_name": "My Project",
        "project_root": "",
        "framework_config": {
            "state_file": ".maf_state.json",
            "message_queue_dir": ".maf_messages",
            "log_dir": ".maf_logs"
        },
        "agent_config": {
            "default_model_provider": "gemini",
            "default_model_name": "gemini-2.0-flash-exp",
            "enabled_agents": [
                "orchestrator",
                "frontend_agent",
                "backend_agent", 
                "db_agent",
                "devops_agent",
                "qa_agent",
                "docs_agent",
                "security_agent",
                "ux_ui_agent"
            ]
        },
        "project_type": "auto",  # auto, nextjs, django, flask, etc.
        "technology_stack": {
            "frontend": ["react", "typescript", "tailwind"],
            "backend": ["nodejs", "typescript"],
            "database": ["postgresql", "supabase"],
            "deployment": ["vercel", "docker"]
        }
    }
    
    CONFIG_FILENAME = ".maf-config.json"
    
    def __init__(self, project_root: Optional[str] = None):
        """
        Initialize project configuration.
        
        Args:
            project_root: Path to the project root directory
        """
        self.project_root = project_root or os.getcwd()
        self.config_path = os.path.join(self.project_root, self.CONFIG_FILENAME)
        self.config = self._load_config()
        
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file or create default."""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r') as f:
                    loaded_config = json.load(f)
                    # Merge with defaults to ensure all keys exist
                    config = self.DEFAULT_CONFIG.copy()
                    config.update(loaded_config)
                    config["project_root"] = self.project_root
                    return config
            except Exception as e:
                print(f"Warning: Failed to load config from {self.config_path}: {e}")
                print("Using default configuration")
        
        # Create default config
        config = self.DEFAULT_CONFIG.copy()
        config["project_root"] = self.project_root
        config["project_name"] = os.path.basename(self.project_root)
        
        # Auto-detect project type
        config["project_type"] = self._detect_project_type()
        
        return config
    
    def save_config(self):
        """Save current configuration to file."""
        try:
            with open(self.config_path, 'w') as f:
                # Don't save project_root as it should be dynamic
                config_to_save = {k: v for k, v in self.config.items() if k != "project_root"}
                json.dump(config_to_save, f, indent=2)
            print(f"Configuration saved to {self.config_path}")
        except Exception as e:
            print(f"Error saving configuration: {e}")
    
    def _detect_project_type(self) -> str:
        """Auto-detect the project type based on files present."""
        project_files = os.listdir(self.project_root)
        
        # Next.js detection
        if "next.config.js" in project_files or "next.config.mjs" in project_files:
            return "nextjs"
        
        # React detection
        if "package.json" in project_files:
            try:
                with open(os.path.join(self.project_root, "package.json"), 'r') as f:
                    package_json = json.load(f)
                    deps = package_json.get("dependencies", {})
                    if "react" in deps:
                        return "react"
                    if "vue" in deps:
                        return "vue"
                    if "angular" in deps:
                        return "angular"
            except:
                pass
        
        # Python project detection
        if "requirements.txt" in project_files or "setup.py" in project_files:
            if "manage.py" in project_files:
                return "django"
            if any(f.endswith(".py") and "flask" in open(os.path.join(self.project_root, f)).read().lower() 
                   for f in project_files if f.endswith(".py")):
                return "flask"
            return "python"
        
        return "auto"
    
    def get_project_root(self) -> str:
        """Get the project root directory."""
        return self.project_root
    
    def get_state_file_path(self) -> str:
        """Get the path to the state file."""
        return os.path.join(
            self.project_root,
            self.config["framework_config"]["state_file"]
        )
    
    def get_message_queue_dir(self) -> str:
        """Get the message queue directory."""
        return os.path.join(
            self.project_root,
            self.config["framework_config"]["message_queue_dir"]
        )
    
    def get_log_dir(self) -> str:
        """Get the log directory."""
        return os.path.join(
            self.project_root,
            self.config["framework_config"]["log_dir"]
        )
    
    def get_enabled_agents(self) -> list:
        """Get list of enabled agents."""
        return self.config["agent_config"]["enabled_agents"]
    
    def get_model_config(self) -> Dict[str, str]:
        """Get default model configuration."""
        return {
            "provider": self.config["agent_config"]["default_model_provider"],
            "name": self.config["agent_config"]["default_model_name"]
        }
    
    def update_config(self, updates: Dict[str, Any]):
        """Update configuration with new values."""
        def deep_update(d, u):
            for k, v in u.items():
                if isinstance(v, dict):
                    d[k] = deep_update(d.get(k, {}), v)
                else:
                    d[k] = v
            return d
        
        self.config = deep_update(self.config, updates)
        self.save_config()
    
    @classmethod
    def initialize_project(cls, project_root: str) -> 'ProjectConfig':
        """
        Initialize a new project with the framework.
        
        Args:
            project_root: Path to the project to initialize
            
        Returns:
            ProjectConfig instance
        """
        config = cls(project_root)
        
        # Create framework directories
        os.makedirs(config.get_message_queue_dir(), exist_ok=True)
        os.makedirs(config.get_log_dir(), exist_ok=True)
        
        # Save initial configuration
        config.save_config()
        
        print(f"✅ Initialized Multi-Agent Framework for project: {project_root}")
        print(f"   Config file: {config.config_path}")
        print(f"   Project type: {config.config['project_type']}")
        
        return config