#!/usr/bin/env python3
"""
Test script to verify enhanced agents with naming conventions
"""

import json
import uuid
from datetime import datetime
import os
import sys

# Add framework to path
framework_root = os.path.dirname(os.path.abspath(__file__))
if framework_root not in sys.path:
    sys.path.insert(0, framework_root)

from core.project_state_manager import ProjectStateManager

def create_test_task():
    """Create a test task to verify naming conventions"""
    
    # Initialize state manager
    state_manager = ProjectStateManager()
    
    # Create a test feature
    feature_id = str(uuid.uuid4())
    feature_desc = "TEST: Newsletter Subscription System - Create API endpoint and service layer for newsletter subscriptions"
    
    state_manager.add_feature(feature_id, feature_desc)
    
    # Create test tasks
    tasks = [
        {
            "description": "Create newsletter subscription API endpoint with CRUD operations",
            "agent": "backend_agent"
        },
        {
            "description": "Create newsletter subscription form component with email validation",
            "agent": "frontend_agent"
        },
        {
            "description": "Document the newsletter API endpoints and subscription process",
            "agent": "docs_agent"
        }
    ]
    
    for task in tasks:
        task_id = str(uuid.uuid4())
        state_manager.add_task(
            task_id=task_id,
            feature_id=feature_id,
            description=task["description"],
            assigned_agent=task["agent"]
        )
        
        # Create message for agent
        message = {
            "id": str(uuid.uuid4()),
            "type": "new_task",
            "task_id": task_id,
            "content": task["description"],
            "sender": "orchestrator",
            "timestamp": datetime.now().isoformat()
        }
        
        # Write to agent's inbox
        inbox_path = os.path.join(framework_root, 'message_queue', f'{task["agent"]}_inbox.json')
        
        # Read existing messages
        existing = []
        if os.path.exists(inbox_path):
            with open(inbox_path, 'r') as f:
                content = f.read().strip()
                if content:
                    existing = json.loads(content)
        
        # Add new message
        existing.append(message)
        
        # Write back
        with open(inbox_path, 'w') as f:
            json.dump(existing, f, indent=2)
        
        print(f"✅ Created test task for {task['agent']}: {task_id}")
    
    print(f"\n📋 Test feature created: {feature_id}")
    print("🚀 Agents should now process these tasks with proper naming conventions")
    print("\nExpected outputs:")
    print("- Backend: app/api/newsletter/route.ts and lib/newsletterService.ts")
    print("- Frontend: components/forms/NewsletterSubscription.tsx")
    print("- Docs: project-plan/api-docs/newsletter-api.md")

if __name__ == "__main__":
    create_test_task()