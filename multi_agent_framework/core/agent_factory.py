"""
Agent Factory - Creates appropriate agent instances based on configuration

This module provides a factory for creating either polling-based or
event-driven agents based on the system configuration.
"""

import importlib
import sys
import os
from typing import Dict, Optional

# Add parent directory to path  # noqa: E402
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from .. import config  # noqa: E402
from ..agents.base_agent_configurable import BaseAgent  # noqa: E402
from multi_agent_framework.core.project_config import ProjectConfig  # noqa: E402


class AgentFactory:
    """Factory for creating agent instances"""

    # Mapping of agent types to their implementations
    AGENT_MAPPINGS = {
        'orchestrator': {
            'polling': ('multi_agent_framework.agents.orchestrator_agent', 'OrchestratorAgent'),
            'event_driven': ('multi_agent_framework.agents.event_driven_orchestrator_agent', 'EventDrivenOrchestratorAgent')
        },
        'frontend': {
            'polling': ('multi_agent_framework.agents.specialized.frontend_agent', 'FrontendAgent'),
            'event_driven': ('multi_agent_framework.agents.event_driven_frontend_agent', 'EventDrivenFrontendAgent')
        },
        'backend': {
            'polling': ('multi_agent_framework.agents.specialized.backend_agent', 'BackendAgent'),
            'event_driven': ('multi_agent_framework.agents.event_driven_backend_agent', 'EventDrivenBackendAgent')
        },
        'db': {
            'polling': ('multi_agent_framework.agents.specialized.db_agent', 'DbAgent'),
            'event_driven': ('multi_agent_framework.agents.event_driven_db_agent', 'EventDrivenDatabaseAgent')
        },
        'qa': {
            'polling': ('multi_agent_framework.agents.specialized.qa_agent', 'QATestingAgent'),
            'event_driven': ('multi_agent_framework.agents.event_driven_qa_agent', 'EventDrivenQAAgent')
        },
        'security': {
            'polling': ('multi_agent_framework.agents.specialized.security_agent', 'SecurityAgent'),
            'event_driven': ('multi_agent_framework.agents.event_driven_security_agent', 'EventDrivenSecurityAgent')
        },
        'devops': {
            'polling': ('multi_agent_framework.agents.specialized.devops_agent', 'DevopsAgent'),
            'event_driven': ('multi_agent_framework.agents.event_driven_devops_agent', 'EventDrivenDevOpsAgent')
        },
        'docs': {
            'polling': ('multi_agent_framework.agents.specialized.docs_agent', 'DocumentationAgent'),
            'event_driven': ('multi_agent_framework.agents.event_driven_docs_agent', 'EventDrivenDocsAgent')
        },
        'ux_ui': {
            'polling': ('multi_agent_framework.agents.specialized.ux_ui_agent', 'UXUIDesignAgent'),
            'event_driven': ('multi_agent_framework.agents.event_driven_ux_ui_agent', 'EventDrivenUXUIAgent')
        }
    }

    @classmethod
    def create_agent(cls, agent_type: str,
                     model_provider: Optional[str] = None,
                     model_name: Optional[str] = None,
                     mode: Optional[str] = None,
                     project_config: Optional[ProjectConfig] = None) -> BaseAgent:
        """
        Create an agent instance

        Args:
            agent_type: Type of agent ('orchestrator', 'frontend', etc.)
            model_provider: LLM provider (defaults to agent's default)
            model_name: LLM model name (defaults to agent's default)
            mode: 'polling' or 'event_driven' (defaults to config.EVENT_DRIVEN_MODE)

        Returns:
            Agent instance

        Raises:
            ValueError: If agent type is not supported
            ImportError: If agent class cannot be imported
        """
        # Normalize agent type
        agent_type = agent_type.lower().replace('_agent', '')

        if agent_type not in cls.AGENT_MAPPINGS:
            raise ValueError(
                f"Unsupported agent type: {agent_type}. "
                f"Supported types: {list(cls.AGENT_MAPPINGS.keys())}"
            )

        # Determine mode
        if mode is None:
            mode = 'event_driven' if config.EVENT_DRIVEN_MODE else 'polling'

        # Get agent module and class info
        module_name, class_name = cls.AGENT_MAPPINGS[agent_type][mode]

        try:
            # Dynamically import the module
            module = importlib.import_module(module_name)
            agent_class = getattr(module, class_name)

            # Create agent instance with project config
            kwargs = {}
            if project_config:
                kwargs['project_config'] = project_config
            if model_provider:
                kwargs['model_provider'] = model_provider
            if model_name:
                kwargs['model_name'] = model_name

            agent = agent_class(**kwargs)

            print(f"Created {mode} {agent_type} agent: {agent.name}")
            return agent

        except ImportError as e:
            raise ImportError(f"Failed to import {mode} {agent_type} agent: {e}")
        except AttributeError as e:
            raise ImportError(f"Agent class {class_name} not found in {module_name}: {e}")

    @classmethod
    def create_all_agents(cls, mode: Optional[str] = None,
                          project_config: Optional[ProjectConfig] = None) -> Dict[str, BaseAgent]:
        """
        Create all available agents

        Args:
            mode: 'polling' or 'event_driven' (defaults to config.EVENT_DRIVEN_MODE)

        Returns:
            Dictionary mapping agent type to agent instance
        """
        agents = {}

        for agent_type in cls.AGENT_MAPPINGS:
            try:
                agent = cls.create_agent(agent_type, mode=mode, project_config=project_config)
                agents[agent_type] = agent
            except Exception as e:
                print(f"Warning: Failed to create {agent_type} agent: {e}")

        return agents

    @classmethod
    def get_available_agents(cls, mode: Optional[str] = None) -> list:
        """
        Get list of available agent types for a given mode

        Args:
            mode: 'polling' or 'event_driven' (defaults to config.EVENT_DRIVEN_MODE)

        Returns:
            List of available agent types
        """
        if mode is None:
            mode = 'event_driven' if config.EVENT_DRIVEN_MODE else 'polling'

        available = []
        for agent_type, implementations in cls.AGENT_MAPPINGS.items():
            if mode in implementations:
                available.append(agent_type)

        return available


def create_agent(agent_type: str, **kwargs) -> BaseAgent:
    """
    Convenience function to create an agent

    Args:
        agent_type: Type of agent to create
        **kwargs: Additional arguments passed to AgentFactory.create_agent

    Returns:
        Agent instance
    """
    return AgentFactory.create_agent(agent_type, **kwargs)


def create_all_agents(**kwargs) -> Dict[str, BaseAgent]:
    """
    Convenience function to create all agents

    Args:
        **kwargs: Additional arguments passed to AgentFactory.create_all_agents

    Returns:
        Dictionary of agent instances
    """
    return AgentFactory.create_all_agents(**kwargs)
