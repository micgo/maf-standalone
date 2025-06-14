"""
Configurable Message Bus

Updated message bus that accepts custom directories instead of hardcoded paths.
"""

import json
import os
import time
from typing import Optional, List, Dict


class MessageBus:
    """
    Handles inter-agent communication using a simple file-based inbox/outbox system.
    Each agent has its own inbox file.
    """
    
    INBOX_SUFFIX = "_inbox.json"
    OUTBOX_SUFFIX = "_outbox.json"  # Not currently used but kept for completeness
    
    def __init__(self, message_dir: Optional[str] = None):
        """
        Initialize message bus with configurable directory.
        
        Args:
            message_dir: Directory for message queue files. If None, uses current directory.
        """
        self.message_dir = message_dir or os.path.join(os.getcwd(), ".maf/message_queues")
        
        # Ensure the message directory exists
        os.makedirs(self.message_dir, exist_ok=True)
    
    def send_message(self, recipient_agent: str, message: dict):
        """Sends a message to a recipient agent's inbox."""
        inbox_file = os.path.join(self.message_dir, f"{recipient_agent}{self.INBOX_SUFFIX}")
        
        # Ensure the inbox file exists and is a valid JSON array
        if not os.path.exists(inbox_file):
            with open(inbox_file, 'w') as f:
                json.dump([], f)  # Initialize with an empty list
        
        try:
            with open(inbox_file, 'r+') as f:
                # Try to load existing messages
                f.seek(0)
                try:
                    messages = json.load(f)
                except json.JSONDecodeError:
                    # If the file is corrupted, start fresh
                    messages = []
                
                # Add timestamp if not present
                if 'timestamp' not in message:
                    message['timestamp'] = time.time()
                
                # Append the new message
                messages.append(message)
                
                # Write back to file
                f.seek(0)
                f.truncate()
                json.dump(messages, f, indent=2)
                
            print(f"Message sent to {recipient_agent}: Type='{message.get('type')}', TaskID='{message.get('task_id')}'")
            
        except (IOError, json.JSONDecodeError) as e:
            print(f"ERROR: MessageBus failed to send message to {recipient_agent} at {inbox_file}: {e}")
    
    def receive_messages(self, agent_name: str) -> List[Dict]:
        """Receives messages from the agent's inbox and clears it."""
        inbox_file = os.path.join(self.message_dir, f"{agent_name}{self.INBOX_SUFFIX}")
        messages = []
        
        if os.path.exists(inbox_file):
            try:
                with open(inbox_file, 'r+') as f:
                    f.seek(0)
                    file_content = f.read()
                    if file_content:
                        messages = json.loads(file_content)
                    
                    # Clear the inbox after reading
                    f.seek(0)
                    f.truncate()
                    json.dump([], f)
                    
            except (IOError, json.JSONDecodeError) as e:
                print(f"ERROR: MessageBus failed to read messages for {agent_name} at {inbox_file}: {e}")
        
        return messages
    
    def broadcast_message(self, message: dict, agent_names: List[str]):
        """Broadcast a message to multiple agents."""
        for agent_name in agent_names:
            self.send_message(agent_name, message.copy())
    
    def initialize_agent_inboxes(self, agent_names: List[str]):
        """
        Ensures that inbox files exist for all specified agents,
        initializing them with an empty JSON list if they don't.
        """
        for agent_name in agent_names:
            inbox_file = os.path.join(self.message_dir, f"{agent_name}{self.INBOX_SUFFIX}")
            if not os.path.exists(inbox_file):
                try:
                    with open(inbox_file, 'w') as f:
                        json.dump([], f)
                except IOError as e:
                    print(f"ERROR: Failed to initialize inbox for {agent_name}: {e}")
    
    def clear_all_messages(self):
        """Clear all message queues (useful for testing or reset)."""
        if os.path.exists(self.message_dir):
            for filename in os.listdir(self.message_dir):
                if filename.endswith(self.INBOX_SUFFIX):
                    filepath = os.path.join(self.message_dir, filename)
                    try:
                        with open(filepath, 'w') as f:
                            json.dump([], f)
                    except IOError as e:
                        print(f"ERROR: Failed to clear {filename}: {e}")
    
    def get_queue_status(self) -> Dict[str, int]:
        """Get the status of all message queues."""
        status = {}
        
        if os.path.exists(self.message_dir):
            for filename in os.listdir(self.message_dir):
                if filename.endswith(self.INBOX_SUFFIX):
                    agent_name = filename[:-len(self.INBOX_SUFFIX)]
                    filepath = os.path.join(self.message_dir, filename)
                    
                    try:
                        with open(filepath, 'r') as f:
                            messages = json.load(f)
                            status[agent_name] = len(messages)
                    except:
                        status[agent_name] = 0
        
        return status