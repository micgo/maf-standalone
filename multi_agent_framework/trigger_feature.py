import os
import sys
import uuid
import time
import json # Import json, specifically used by initialize_agent_inboxes for dump/load

# Ensure project root is in sys.path for core imports
# This script is now in the multi_agent_framework directory
framework_root = os.path.abspath(os.path.dirname(__file__))
project_root = os.path.abspath(os.path.join(framework_root, '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
if framework_root not in sys.path:
    sys.path.insert(0, framework_root)

# Import MessageBus and initialize_agent_inboxes from core.message_bus
from multi_agent_framework.core.message_bus import MessageBus, initialize_agent_inboxes

if __name__ == "__main__":
    # Create an instance of the MessageBus to send messages
    mb = MessageBus()

    # Define a list of all agents. This is crucial for initialize_agent_inboxes
    # to create their inbox files if they don't already exist.
    all_agent_names = [
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
    # Initialize inboxes for all agents in the list
    initialize_agent_inboxes(all_agent_names)

    print("\n--- Starting New Feature Request ---")
    # Prompt the user to enter a description for the new feature
    feature_desc = input("Enter a new feature description (e.g., 'Implement user authentication with OAuth and profile management'): ")

    # Generate a unique ID for this initial feature request
    initial_request_id = str(uuid.uuid4())

    # Construct the message to be sent to the orchestrator agent
    message_to_orchestrator = {
        "sender": "user",        # The sender of this message is the user
        "type": "new_feature",   # This message type tells the orchestrator to handle a new feature
        "content": feature_desc, # The actual description of the feature
        "task_id": initial_request_id, # A unique ID for this top-level request
        "timestamp": time.time() # Timestamp for logging and ordering
    }

    # Send the message to the "orchestrator" agent's inbox
    mb.send_message("orchestrator", message_to_orchestrator)
    
    print(f"\nSent new feature request: '{feature_desc}' to orchestrator with ID: {initial_request_id}.")
    print("Please check the orchestrator's terminal and your project_state.json file for progress.")
    print("Also, observe the output in the terminals of other specialized agents as they receive tasks.")

