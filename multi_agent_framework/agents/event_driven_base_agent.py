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
from ..core.error_handler import error_handler, ErrorCategory, ErrorLevel, handle_task_error


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
        
        # Process any existing messages in inbox
        self._process_inbox_messages()
        
        # Publish agent started event
        self.event_bus.publish(Event(
            id=f"{self.name}-started-{time.time()}",
            type=EventType.AGENT_STARTED,
            source=self.name,
            timestamp=time.time(),
            data={"agent": self.name}
        ))
        
        print(f"{self.name}: Started in event-driven mode")
        
    def _process_inbox_messages(self):
        """Process any existing messages in the agent's inbox"""
        from ..core.message_bus_configurable import MessageBus
        
        # Get message directory from project config
        message_dir = None
        if hasattr(self, 'project_config') and self.project_config:
            message_dir = self.project_config.get_message_queue_dir()
        
        # Create message bus instance
        message_bus = MessageBus(message_dir)
        
        # Receive messages from inbox
        messages = message_bus.receive_messages(self.name)
        
        if messages:
            print(f"{self.name}: Processing {len(messages)} inbox messages...")
            
            for msg in messages:
                # Convert inbox message to appropriate event
                self._convert_inbox_message_to_event(msg)
                
    def _convert_inbox_message_to_event(self, message: Dict[str, Any]):
        """Convert an inbox message to an event and publish it"""
        msg_type = message.get('type', '')
        
        # Handle orchestrator messages
        if self.name == 'orchestrator':
            if msg_type == 'new_feature':
                # Convert to FEATURE_CREATED event
                event = Event(
                    id=f"inbox-{self.name}-{time.time()}",
                    type=EventType.FEATURE_CREATED,
                    source=message.get('sender', 'cli'),
                    timestamp=time.time(),
                    data={
                        'feature_id': f"feature_{int(message.get('timestamp', time.time()))}",
                        'description': message.get('content', ''),
                        'target': self.name,
                        'from_inbox': True
                    }
                )
                self.event_bus.publish(event)
                print(f"{self.name}: Converted inbox message to FEATURE_CREATED event")
                
        # Handle task assignments for other agents
        elif msg_type == 'task_assignment':
            task_data = message.get('task', {})
            event = Event(
                id=f"inbox-{self.name}-{time.time()}",
                type=EventType.TASK_ASSIGNED,
                source=message.get('sender', 'orchestrator'),
                timestamp=time.time(),
                data={
                    'task_id': task_data.get('id'),
                    'description': task_data.get('description'),
                    'assigned_agent': self.name,
                    'feature_id': task_data.get('feature_id'),
                    'target': self.name,
                    'from_inbox': True
                }
            )
            self.event_bus.publish(event)
            print(f"{self.name}: Converted inbox message to TASK_ASSIGNED event")
            
        # Handle other message types as CUSTOM events
        else:
            event = Event(
                id=f"inbox-{self.name}-{time.time()}",
                type=EventType.CUSTOM,
                source=message.get('sender', 'unknown'),
                timestamp=time.time(),
                data={
                    'message_type': msg_type,
                    'content': message.get('content'),
                    'original_message': message,
                    'target': self.name,
                    'from_inbox': True
                }
            )
            self.event_bus.publish(event)
            print(f"{self.name}: Converted inbox message to CUSTOM event")
        
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
        
    def report_progress(self, task_id: str, progress: int, message: str = None):
        """Report task progress (0-100)"""
        # Publish progress update event
        self.event_bus.publish(Event(
            id=f"progress-{task_id}-{time.time()}",
            type=EventType.CUSTOM,
            source=self.name,
            timestamp=time.time(),
            data={
                'event_type': 'task_progress',
                'task_id': task_id,
                'progress': max(0, min(100, progress)),
                'message': message
            }
        ))
        
    def _process_task_safe(self, task_id: str, task_data: Dict[str, Any]):
        """Safely process a task with error handling"""
        try:
            # Report task starting at 10%
            self.report_progress(task_id, 10, "Starting task processing")
            
            # Call the agent-specific task processing
            result = self.process_task(task_id, task_data)
            
            # Report task near completion
            self.report_progress(task_id, 90, "Finalizing task")
            
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
            # Use centralized error handler
            handle_task_error(e, task_id, f"Task processing failed in {self.name}")
            
            error_msg = str(e)
            
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