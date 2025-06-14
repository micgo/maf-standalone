import json
import os
import time # Added this import to support timestamp in messages

MESSAGE_QUEUE_DIR = ".maf/message_queues"
INBOX_SUFFIX = "_inbox.json"
OUTBOX_SUFFIX = "_outbox.json" # Not currently used but kept for completeness

# Ensure the message_queue directory exists
if not os.path.exists(MESSAGE_QUEUE_DIR):
    os.makedirs(MESSAGE_QUEUE_DIR)

class MessageBus:
    """
    Handles inter-agent communication using a simple file-based inbox/outbox system.
    Each agent has its own inbox file.
    """
    def send_message(self, recipient_agent: str, message: dict):
        """Sends a message to a recipient agent's inbox."""
        inbox_file = os.path.join(MESSAGE_QUEUE_DIR, f"{recipient_agent}{INBOX_SUFFIX}")
        
        # Ensure the inbox file exists and is a valid JSON array
        if not os.path.exists(inbox_file):
            with open(inbox_file, 'w') as f:
                json.dump([], f) # Initialize with an empty list

        try:
            with open(inbox_file, 'r+') as f:
                # Read existing messages
                f.seek(0)
                file_content = f.read()
                if not file_content: # Handle truly empty file
                    messages = []
                else:
                    messages = json.loads(file_content)

                messages.append(message)

                # Write updated messages back, clearing the file first
                f.seek(0)
                f.truncate()
                json.dump(messages, f, indent=2)
            print(f"Message sent to {recipient_agent}: Type='{message.get('type')}', TaskID='{message.get('task_id')}'")
        except (IOError, json.JSONDecodeError) as e:
            print(f"ERROR: MessageBus failed to send message to {recipient_agent} at {inbox_file}: {e}")

    def receive_messages(self, agent_name: str):
        """Receives messages from the agent's inbox and clears it."""
        inbox_file = os.path.join(MESSAGE_QUEUE_DIR, f"{agent_name}{INBOX_SUFFIX}")
        messages = []
        if os.path.exists(inbox_file):
            try:
                with open(inbox_file, 'r+') as f:
                    f.seek(0)
                    file_content = f.read()
                    if file_content:
                        messages = json.loads(file_content)
                    
                    f.seek(0)
                    f.truncate() # Clear the inbox after reading
                    json.dump([], f, indent=2) # Ensure it's an empty list

                if messages:
                    pass  # Messages were read successfully
            except (IOError, json.JSONDecodeError) as e:
                print(f"ERROR: MessageBus failed to receive messages for {agent_name} at {inbox_file}: {e}")
                messages = [] # Ensure no partial or corrupted data is returned
        return messages

    def broadcast_message(self, message: dict):
        """Placeholder for broadcasting to all agents (e.g., for project updates)."""
        # In a more advanced system, this would iterate through all known agents
        # For now, orchestrator will manage explicit sending to known agents.

# Helper function to initialize agent inboxes on first run
def initialize_agent_inboxes(agent_names):
    """
    Ensures that inbox files exist for all specified agents,
    initializing them with an empty JSON list if they don't.
    """
    if not os.path.exists(MESSAGE_QUEUE_DIR):
        os.makedirs(MESSAGE_QUEUE_DIR)

    for agent_name in agent_names:
        inbox_file = os.path.join(MESSAGE_QUEUE_DIR, f"{agent_name}{INBOX_SUFFIX}")
        if not os.path.exists(inbox_file):
            try:
                with open(inbox_file, 'w') as f:
                    json.dump([], f)
            except IOError as e:
                print(f"ERROR: Failed to initialize inbox for {agent_name}: {e}")
