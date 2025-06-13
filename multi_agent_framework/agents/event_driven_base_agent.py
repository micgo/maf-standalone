"""
Event-Driven Base Agent

This is the new base class for agents that use event-driven architecture
instead of polling for messages.
"""

import time
import threading
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

from ..core.event_bus_interface import Event, EventType
from ..core.event_bus_factory import get_event_bus
from .. import config
from .base_agent_configurable import BaseAgent


class EventDrivenBaseAgent(BaseAgent):
    """
    Base class for event-driven agents.
    Extends the original BaseAgent but replaces polling with event subscriptions.
    """
    
    def __init__(self, name: str, model_provider="gemini", model_name="gemini-2.0-flash-exp", project_config=None):
        super().__init__(name, project_config, model_provider, model_name)
        
        # Event bus for communication (use configuration from config)
        self.event_bus = get_event_bus(config.EVENT_BUS_CONFIG)
        
        # Track active tasks
        self._active_tasks: Dict[str, Dict[str, Any]] = {}
        self._task_lock = threading.Lock()
        
        # Agent state
        self._running = False
        self._heartbeat_thread: Optional[threading.Thread] = None
        
    def start(self):
        """Start the agent and subscribe to relevant events"""
        if self._running:
            return
            
        self._running = True
        
        # Subscribe to events
        self._subscribe_to_events()
        
        # Start heartbeat
        self._start_heartbeat()
        
        # Publish agent started event
        self.event_bus.publish(Event(
            id=f"{self.name}-started-{time.time()}",
            type=EventType.AGENT_STARTED,
            source=self.name,
            timestamp=time.time(),
            data={"agent": self.name}
        ))
        
        print(f"{self.name}: Started in event-driven mode")
        
    def stop(self):
        """Stop the agent"""
        self._running = False
        
        # Publish agent stopped event
        self.event_bus.publish(Event(
            id=f"{self.name}-stopped-{time.time()}",
            type=EventType.AGENT_STOPPED,
            source=self.name,
            timestamp=time.time(),
            data={"agent": self.name}
        ))
        
        if self._heartbeat_thread:
            self._heartbeat_thread.join(timeout=5)
            
        print(f"{self.name}: Stopped")
        
    def _subscribe_to_events(self):
        """Subscribe to relevant events - override in subclasses"""
        # Subscribe to system shutdown
        self.event_bus.subscribe(EventType.SYSTEM_SHUTDOWN, self._handle_shutdown)
        
        # Subscribe to task assignment for this agent
        self.event_bus.subscribe(EventType.TASK_ASSIGNED, self._handle_task_assigned)
        
        # Subscribe to health checks
        self.event_bus.subscribe(EventType.SYSTEM_HEALTH_CHECK, self._handle_health_check)
        
    def _handle_shutdown(self, event: Event):
        """Handle system shutdown event"""
        print(f"{self.name}: Received shutdown event")
        self.stop()
        
    def _handle_task_assigned(self, event: Event):
        """Handle task assignment event"""
        data = event.data
        
        # Check if task is for this agent
        if data.get("assigned_agent") != self.name:
            return
            
        task_id = data.get("task_id")
        if not task_id:
            return
            
        # Process the task
        print(f"{self.name}: Received task assignment: {task_id}")
        
        # Store task info
        with self._task_lock:
            self._active_tasks[task_id] = {
                "description": data.get("description", ""),
                "feature_id": data.get("feature_id"),
                "started_at": time.time()
            }
        
        # Publish task started event
        self.event_bus.publish_task_event(
            EventType.TASK_STARTED,
            task_id,
            self.name,
            {"description": data.get("description", "")}
        )
        
        # Process task in separate thread
        threading.Thread(
            target=self._process_task_safe,
            args=(task_id, data),
            daemon=True
        ).start()
        
    def _process_task_safe(self, task_id: str, task_data: Dict[str, Any]):
        """Safely process a task with error handling"""
        try:
            # Call the agent-specific task processing
            result = self.process_task(task_id, task_data)
            
            # Publish completion event
            self.event_bus.publish_task_event(
                EventType.TASK_COMPLETED,
                task_id,
                self.name,
                {"result": result}
            )
            
            # Update state manager
            self.state_manager.update_task_status(task_id, "completed", result)
            
        except Exception as e:
            error_msg = f"Error processing task: {str(e)}"
            print(f"{self.name}: {error_msg}")
            
            # Publish failure event
            self.event_bus.publish_task_event(
                EventType.TASK_FAILED,
                task_id,
                self.name,
                {"error": error_msg}
            )
            
            # Update state manager
            self.state_manager.update_task_status(task_id, "failed", error=error_msg)
            
        finally:
            # Remove from active tasks
            with self._task_lock:
                self._active_tasks.pop(task_id, None)
                
    @abstractmethod
    def process_task(self, task_id: str, task_data: Dict[str, Any]) -> Any:
        """
        Process a task - must be implemented by subclasses
        
        Args:
            task_id: Unique task identifier
            task_data: Task information including description, feature_id, etc.
            
        Returns:
            Task result
        """
        pass
        
    def _handle_health_check(self, event: Event):
        """Respond to health check"""
        self.event_bus.publish(Event(
            id=f"{self.name}-health-{time.time()}",
            type=EventType.AGENT_HEARTBEAT,
            source=self.name,
            timestamp=time.time(),
            data={
                "agent": self.name,
                "active_tasks": len(self._active_tasks),
                "status": "healthy" if self._running else "stopped"
            }
        ))
        
    def _start_heartbeat(self):
        """Start heartbeat thread"""
        def heartbeat():
            while self._running:
                self.event_bus.publish(Event(
                    id=f"{self.name}-heartbeat-{time.time()}",
                    type=EventType.AGENT_HEARTBEAT,
                    source=self.name,
                    timestamp=time.time(),
                    data={
                        "agent": self.name,
                        "active_tasks": len(self._active_tasks)
                    }
                ))
                time.sleep(30)  # Heartbeat every 30 seconds
                
        self._heartbeat_thread = threading.Thread(target=heartbeat, daemon=True)
        self._heartbeat_thread.start()
        
    def emit_custom_event(self, event_name: str, data: Dict[str, Any]):
        """Emit a custom event"""
        self.event_bus.publish(Event(
            id=f"{self.name}-{event_name}-{time.time()}",
            type=EventType.CUSTOM,
            source=self.name,
            timestamp=time.time(),
            data={"event_name": event_name, **data}
        ))
        
    def run(self):
        """
        Main run loop - in event-driven mode, this just keeps the agent alive
        """
        self.start()
        
        try:
            while self._running:
                time.sleep(1)
        except KeyboardInterrupt:
            print(f"{self.name}: Interrupted by user")
        finally:
            self.stop()