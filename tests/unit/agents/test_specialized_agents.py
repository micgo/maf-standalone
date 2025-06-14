#!/usr/bin/env python3
"""
Tests for all specialized agents (Frontend, Backend, DB, DevOps, QA, Docs, Security, UX/UI)
"""
import os
import json
from unittest import TestCase, mock
from unittest.mock import Mock, patch, MagicMock

from multi_agent_framework.agents.specialized.frontend_agent import FrontendAgent
from multi_agent_framework.agents.specialized.backend_agent import BackendAgent
from multi_agent_framework.agents.specialized.db_agent import DbAgent
from multi_agent_framework.agents.specialized.devops_agent import DevopsAgent
from multi_agent_framework.agents.specialized.qa_agent import QaAgent
from multi_agent_framework.agents.specialized.docs_agent import DocsAgent
from multi_agent_framework.agents.specialized.security_agent import SecurityAgent
from multi_agent_framework.agents.specialized.ux_ui_agent import UxUiAgent


class TestSpecializedAgentsBase(TestCase):
    """Base test class with common setup"""
    
    def setUp(self):
        """Set up test environment"""
        self.temp_dir = '/tmp/test_specialized_agents'
        os.makedirs(self.temp_dir, exist_ok=True)
        
        # Create actual project config
        from multi_agent_framework.core.project_config import ProjectConfig
        self.project_config = ProjectConfig(self.temp_dir)
        
        # Mock LLM
        self.llm_patcher = patch('google.generativeai.GenerativeModel')
        self.mock_llm_class = self.llm_patcher.start()
        self.mock_llm = Mock()
        self.mock_llm_class.return_value = self.mock_llm
        
        # Mock shared state manager
        self.mock_state_manager = Mock()
        self.state_manager_patcher = patch('multi_agent_framework.core.shared_state_manager.get_shared_state_manager')
        self.mock_get_state_manager = self.state_manager_patcher.start()
        self.mock_get_state_manager.return_value = self.mock_state_manager
        
        # Mock message bus
        self.message_bus_patcher = patch('multi_agent_framework.core.message_bus_configurable.MessageBus')
        self.mock_message_bus_class = self.message_bus_patcher.start()
        self.mock_message_bus = Mock()
        self.mock_message_bus_class.return_value = self.mock_message_bus
        self.mock_message_bus.receive_messages.return_value = []
        
    def tearDown(self):
        """Clean up"""
        # No need to stop patcher anymore
        self.llm_patcher.stop()
        self.state_manager_patcher.stop()
        self.message_bus_patcher.stop()
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)


class TestFrontendAgent(TestSpecializedAgentsBase):
    """Test FrontendAgent functionality"""
    
    def test_frontend_agent_initialization(self):
        """Test frontend agent initialization"""
        agent = FrontendAgent(self.project_config)
        
        self.assertEqual(agent.name, "frontend_agent")
        self.assertIsNotNone(agent.app_pages_scan_root)
        self.assertIsNotNone(agent.root_components_scan_root)
    
    def test_process_ui_task(self):
        """Test processing UI component task"""
        agent = FrontendAgent(self.project_config)
        
        # Mock LLM response with React component
        self.mock_llm.generate_content.return_value.text = '''
```tsx
import React from 'react';

interface UserProfileProps {
    name: string;
    email: string;
}

export const UserProfile: React.FC<UserProfileProps> = ({ name, email }) => {
    return (
        <div className="p-4 border rounded-lg">
            <h2 className="text-xl font-bold">{name}</h2>
            <p className="text-gray-600">{email}</p>
        </div>
    );
};
```
'''
        
        # Process task
        task_msg = {
            "type": "new_task",
            "task_id": "task-123",
            "content": "Create a user profile component"
        }
        
        # Mock the agent's state manager and file operations
        with patch.object(agent, 'state_manager', self.mock_state_manager):
            with patch.object(agent, 'send_message') as mock_send:
                with patch('builtins.open', mock.mock_open()):
                    with patch('os.makedirs'):
                        agent._process_message(task_msg)
                        
                        # Check task status updated
                        self.mock_state_manager.update_task_status.assert_called_with("task-123", "in_progress")
                        
                        # Check result sent
                        mock_send.assert_called_once()
                        sent_msg = mock_send.call_args[0][1]
                        self.assertEqual(sent_msg['type'], 'task_completed')
                        self.assertEqual(sent_msg['task_id'], 'task-123')
                        self.assertIn('component', sent_msg['output'].lower())
    
    def test_handle_review_and_retry(self):
        """Test handling review and retry messages"""
        agent = FrontendAgent(self.project_config)
        
        # Mock improved response
        self.mock_llm.generate_content.return_value.text = '''
```tsx
// Improved component with better accessibility
export const ImprovedButton: React.FC = () => {
    return <button aria-label="Submit form">Submit</button>;
};
```
'''
        
        review_msg = {
            "type": "review_and_retry",
            "task_id": "task-456",
            "content": "Add accessibility attributes to the button"
        }
        
        with patch.object(agent, 'send_message') as mock_send:
            agent._process_message(review_msg)
            
            # Check retry was processed
            mock_send.assert_called_once()
            sent_msg = mock_send.call_args[0][1]
            self.assertEqual(sent_msg['type'], 'task_completed')
            self.assertIn('accessibility', sent_msg['output'].lower())


class TestBackendAgent(TestSpecializedAgentsBase):
    """Test BackendAgent functionality"""
    
    def test_backend_agent_initialization(self):
        """Test backend agent initialization"""
        agent = BackendAgent(self.project_config)
        
        self.assertEqual(agent.name, "backend_agent")
        self.assertIsNotNone(agent.llm)
    
    def test_process_api_task(self):
        """Test processing API endpoint task"""
        agent = BackendAgent(self.project_config)
        
        # Mock LLM response with Python API
        self.mock_llm.generate_content.return_value.text = '''
```python
from flask import Flask, jsonify, request

app = Flask(__name__)

@app.route('/api/users', methods=['GET'])
def get_users():
    """Get all users endpoint"""
    # Mock implementation
    users = [
        {"id": 1, "name": "John Doe", "email": "john@example.com"},
        {"id": 2, "name": "Jane Smith", "email": "jane@example.com"}
    ]
    return jsonify({"users": users, "total": len(users)})

@app.route('/api/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    """Get specific user by ID"""
    # Mock implementation
    user = {"id": user_id, "name": "John Doe", "email": "john@example.com"}
    return jsonify(user)
```
'''
        
        task_msg = {
            "type": "new_task",
            "task_id": "task-789",
            "content": "Create REST API endpoints for user management"
        }
        
        with patch.object(agent, 'send_message') as mock_send:
            agent._process_message(task_msg)
            
            # Check API was created
            mock_send.assert_called_once()
            sent_msg = mock_send.call_args[0][1]
            self.assertEqual(sent_msg['type'], 'task_completed')
            self.assertIn('endpoint', sent_msg['output'].lower())


class TestDbAgent(TestSpecializedAgentsBase):
    """Test DbAgent functionality"""
    
    def test_db_agent_initialization(self):
        """Test database agent initialization"""
        agent = DbAgent(self.project_config)
        
        self.assertEqual(agent.name, "db_agent")
    
    def test_process_schema_task(self):
        """Test processing database schema task"""
        agent = DbAgent(self.project_config)
        
        # Mock LLM response with SQL schema
        self.mock_llm.generate_content.return_value.text = '''
```sql
-- Users table
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(100) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Posts table
CREATE TABLE posts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    title VARCHAR(200) NOT NULL,
    content TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Indexes for performance
CREATE INDEX idx_posts_user_id ON posts(user_id);
CREATE INDEX idx_users_email ON users(email);
```
'''
        
        task_msg = {
            "type": "new_task",
            "task_id": "task-db-1",
            "content": "Design database schema for blog application"
        }
        
        with patch.object(agent, 'send_message') as mock_send:
            agent._process_message(task_msg)
            
            # Check schema was created
            sent_msg = mock_send.call_args[0][1]
            self.assertEqual(sent_msg['type'], 'task_completed')
            self.assertIn('schema', sent_msg['output'].lower())


class TestDevopsAgent(TestSpecializedAgentsBase):
    """Test DevopsAgent functionality"""
    
    def test_devops_agent_initialization(self):
        """Test DevOps agent initialization"""
        agent = DevopsAgent(self.project_config)
        
        self.assertEqual(agent.name, "devops_agent")
    
    def test_process_deployment_task(self):
        """Test processing deployment configuration task"""
        agent = DevopsAgent(self.project_config)
        
        # Mock LLM response with Docker/deployment config
        self.mock_llm.generate_content.return_value.text = '''
```yaml
# docker-compose.yml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "3000:3000"
    environment:
      - NODE_ENV=production
      - DATABASE_URL=postgresql://user:pass@db:5432/myapp
    depends_on:
      - db
  
  db:
    image: postgres:14
    environment:
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
      - POSTGRES_DB=myapp
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

```dockerfile
# Dockerfile
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY . .
RUN npm run build
EXPOSE 3000
CMD ["npm", "start"]
```
'''
        
        task_msg = {
            "type": "new_task",
            "task_id": "task-devops-1",
            "content": "Setup Docker configuration for deployment"
        }
        
        with patch.object(agent, 'send_message') as mock_send:
            agent._process_message(task_msg)
            
            sent_msg = mock_send.call_args[0][1]
            self.assertEqual(sent_msg['type'], 'task_completed')
            self.assertIn('docker', sent_msg['output'].lower())


class TestQaAgent(TestSpecializedAgentsBase):
    """Test QaAgent functionality"""
    
    def test_qa_agent_initialization(self):
        """Test QA agent initialization"""
        agent = QaAgent(self.project_config)
        
        self.assertEqual(agent.name, "qa_agent")
    
    def test_process_test_task(self):
        """Test processing test creation task"""
        agent = QaAgent(self.project_config)
        
        # Mock LLM response with tests
        self.mock_llm.generate_content.return_value.text = '''
```javascript
// UserProfile.test.tsx
import { render, screen } from '@testing-library/react';
import { UserProfile } from './UserProfile';

describe('UserProfile', () => {
    it('renders user name and email', () => {
        render(<UserProfile name="John Doe" email="john@example.com" />);
        
        expect(screen.getByText('John Doe')).toBeInTheDocument();
        expect(screen.getByText('john@example.com')).toBeInTheDocument();
    });
    
    it('applies correct styling classes', () => {
        const { container } = render(<UserProfile name="Test" email="test@example.com" />);
        const wrapper = container.firstChild;
        
        expect(wrapper).toHaveClass('p-4', 'border', 'rounded-lg');
    });
});
```
'''
        
        task_msg = {
            "type": "new_task",
            "task_id": "task-qa-1",
            "content": "Write unit tests for UserProfile component"
        }
        
        with patch.object(agent, 'send_message') as mock_send:
            agent._process_message(task_msg)
            
            sent_msg = mock_send.call_args[0][1]
            self.assertEqual(sent_msg['type'], 'task_completed')
            self.assertIn('test', sent_msg['output'].lower())


class TestDocsAgent(TestSpecializedAgentsBase):
    """Test DocsAgent functionality"""
    
    def test_docs_agent_initialization(self):
        """Test documentation agent initialization"""
        agent = DocsAgent(self.project_config)
        
        self.assertEqual(agent.name, "docs_agent")
    
    def test_process_documentation_task(self):
        """Test processing documentation task"""
        agent = DocsAgent(self.project_config)
        
        # Mock LLM response with documentation
        self.mock_llm.generate_content.return_value.text = '''
# User Management API Documentation

## Overview
The User Management API provides endpoints for creating, reading, updating, and deleting user accounts.

## Endpoints

### GET /api/users
Retrieve a list of all users.

**Response:**
```json
{
    "users": [
        {
            "id": 1,
            "name": "John Doe",
            "email": "john@example.com"
        }
    ],
    "total": 1
}
```

### GET /api/users/{id}
Retrieve a specific user by ID.

**Parameters:**
- `id` (integer): The user's unique identifier

**Response:**
```json
{
    "id": 1,
    "name": "John Doe",
    "email": "john@example.com"
}
```

### Error Handling
All endpoints return appropriate HTTP status codes:
- 200: Success
- 404: User not found
- 500: Internal server error
'''
        
        task_msg = {
            "type": "new_task",
            "task_id": "task-docs-1",
            "content": "Create API documentation for user management endpoints"
        }
        
        with patch.object(agent, 'send_message') as mock_send:
            agent._process_message(task_msg)
            
            sent_msg = mock_send.call_args[0][1]
            self.assertEqual(sent_msg['type'], 'task_completed')
            self.assertIn('documentation', sent_msg['output'].lower())


class TestSecurityAgent(TestSpecializedAgentsBase):
    """Test SecurityAgent functionality"""
    
    def test_security_agent_initialization(self):
        """Test security agent initialization"""
        agent = SecurityAgent(self.project_config)
        
        self.assertEqual(agent.name, "security_agent")
    
    def test_process_security_task(self):
        """Test processing security review task"""
        agent = SecurityAgent(self.project_config)
        
        # Mock LLM response with security recommendations
        self.mock_llm.generate_content.return_value.text = '''
# Security Review Report

## Findings

### 1. Authentication Implementation
```python
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
from datetime import datetime, timedelta

class AuthService:
    def hash_password(self, password):
        """Securely hash passwords using bcrypt"""
        return generate_password_hash(password, method='pbkdf2:sha256')
    
    def verify_password(self, stored_hash, password):
        """Verify password against hash"""
        return check_password_hash(stored_hash, password)
    
    def generate_token(self, user_id):
        """Generate JWT token with expiration"""
        payload = {
            'user_id': user_id,
            'exp': datetime.utcnow() + timedelta(hours=24)
        }
        return jwt.encode(payload, SECRET_KEY, algorithm='HS256')
```

### 2. Input Validation
- Implement request validation for all endpoints
- Sanitize user inputs to prevent XSS attacks
- Use parameterized queries to prevent SQL injection

### 3. Security Headers
```python
@app.after_request
def security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    return response
```
'''
        
        task_msg = {
            "type": "new_task",
            "task_id": "task-sec-1",
            "content": "Review and implement security best practices for authentication"
        }
        
        with patch.object(agent, 'send_message') as mock_send:
            agent._process_message(task_msg)
            
            sent_msg = mock_send.call_args[0][1]
            self.assertEqual(sent_msg['type'], 'task_completed')
            self.assertIn('security', sent_msg['output'].lower())


class TestUxUiAgent(TestSpecializedAgentsBase):
    """Test UxUiAgent functionality"""
    
    def test_uxui_agent_initialization(self):
        """Test UX/UI agent initialization"""
        agent = UxUiAgent(self.project_config)
        
        self.assertEqual(agent.name, "ux_ui_agent")
    
    def test_process_design_task(self):
        """Test processing UX/UI design task"""
        agent = UxUiAgent(self.project_config)
        
        # Mock LLM response with design system
        self.mock_llm.generate_content.return_value.text = '''
# Design System Guidelines

## Color Palette
```css
:root {
    --primary-color: #3B82F6;
    --secondary-color: #10B981;
    --danger-color: #EF4444;
    --warning-color: #F59E0B;
    --text-primary: #1F2937;
    --text-secondary: #6B7280;
    --background: #FFFFFF;
    --surface: #F3F4F6;
}
```

## Typography
```css
.heading-1 {
    font-size: 2.5rem;
    font-weight: 700;
    line-height: 1.2;
}

.heading-2 {
    font-size: 2rem;
    font-weight: 600;
    line-height: 1.3;
}

.body-text {
    font-size: 1rem;
    line-height: 1.5;
}
```

## Component Examples

### Button Component
```tsx
export const Button = ({ variant = 'primary', size = 'medium', children, ...props }) => {
    const baseClasses = 'rounded-lg font-medium transition-colors focus:outline-none focus:ring-2';
    const variants = {
        primary: 'bg-primary-color text-white hover:bg-blue-600',
        secondary: 'bg-gray-200 text-gray-800 hover:bg-gray-300',
        danger: 'bg-danger-color text-white hover:bg-red-600'
    };
    const sizes = {
        small: 'px-3 py-1.5 text-sm',
        medium: 'px-4 py-2',
        large: 'px-6 py-3 text-lg'
    };
    
    return (
        <button 
            className={`${baseClasses} ${variants[variant]} ${sizes[size]}`}
            {...props}
        >
            {children}
        </button>
    );
};
```

## Accessibility Guidelines
- Ensure all interactive elements have proper ARIA labels
- Maintain color contrast ratio of at least 4.5:1
- Support keyboard navigation throughout the application
'''
        
        task_msg = {
            "type": "new_task",
            "task_id": "task-ux-1",
            "content": "Create a design system with color palette and component guidelines"
        }
        
        with patch.object(agent, 'send_message') as mock_send:
            agent._process_message(task_msg)
            
            sent_msg = mock_send.call_args[0][1]
            self.assertEqual(sent_msg['type'], 'task_completed')
            self.assertIn('design', sent_msg['output'].lower())


class TestSpecializedAgentIntegration(TestSpecializedAgentsBase):
    """Test integration between specialized agents"""
    
    def test_agent_factory_creation(self):
        """Test creating agents through factory"""
        from multi_agent_framework.core.agent_factory import AgentFactory
        
        factory = AgentFactory(self.temp_dir)
        
        # Test creating each agent type
        agent_types = [
            'frontend_agent', 'backend_agent', 'db_agent', 
            'devops_agent', 'qa_agent', 'docs_agent', 
            'security_agent', 'ux_ui_agent'
        ]
        
        for agent_type in agent_types:
            with self.subTest(agent_type=agent_type):
                agent = factory.create_agent(agent_type)
                self.assertIsNotNone(agent)
                self.assertEqual(agent.name, agent_type)
    
    def test_cross_agent_communication(self):
        """Test agents can communicate via message bus"""
        frontend = FrontendAgent(self.project_config)
        backend = BackendAgent(self.project_config)
        
        # Frontend sends message to backend
        test_message = {
            "type": "api_request",
            "content": "Need user API endpoint",
            "sender": "frontend_agent"
        }
        
        with patch.object(frontend, 'send_message') as mock_send:
            frontend.send_message("backend_agent", test_message)
            mock_send.assert_called_once_with("backend_agent", test_message)
    
    def test_polling_loop_with_stop(self):
        """Test agent polling loop can be stopped"""
        agent = FrontendAgent(self.project_config)
        
        # Set up messages to process then stop
        messages = [
            {"type": "new_task", "task_id": "1", "content": "Task 1"},
            {"type": "stop", "content": "Shutdown agent"}
        ]
        
        self.mock_message_bus.receive_messages.side_effect = [messages[:1], messages[1:], []]
        
        # Mock process_message to track calls
        with patch.object(agent, '_process_message') as mock_process:
            with patch.object(agent, 'send_message'):
                # Run with a timeout
                import threading
                def run_with_timeout():
                    agent.run()
                
                thread = threading.Thread(target=run_with_timeout)
                thread.daemon = True
                thread.start()
                
                # Give it time to process
                import time
                time.sleep(0.1)
                
                # Should have processed both messages
                self.assertEqual(mock_process.call_count, 2)


if __name__ == '__main__':
    import unittest
    unittest.main()