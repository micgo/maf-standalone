"""
Multi-Agent Framework for automated project development.

This framework coordinates multiple specialized agents to handle different aspects
of software development including backend, frontend, database, DevOps, QA,
documentation, security, and UX/UI tasks.
"""

from .core.message_bus import MessageBus, initialize_agent_inboxes
from .core.project_state_manager import ProjectStateManager
from .core.project_analyzer import ProjectAnalyzer
from .core.file_integrator import FileIntegrator

__version__ = "1.0.0"
__all__ = [
    "MessageBus",
    "initialize_agent_inboxes",
    "ProjectStateManager",
    "ProjectAnalyzer",
    "FileIntegrator"
]