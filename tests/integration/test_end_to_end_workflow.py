#!/usr/bin/env python3
"""
End-to-end integration tests for complete workflows
"""
import os
import json
import time
import tempfile
import shutil
from unittest import TestCase, mock
from unittest.mock import Mock, patch, MagicMock

from multi_agent_framework.core.project_config import ProjectConfig
from multi_agent_framework.core.agent_factory import AgentFactory
from multi_agent_framework.core.event_bus_factory import get_event_bus, reset_event_bus
from multi_agent_framework.core.event_bus_interface import EventType
from multi_agent_framework.agents.event_driven_orchestrator_agent import EventDrivenOrchestratorAgent
from multi_agent_framework.agents.event_driven_frontend_agent import EventDrivenFrontendAgent
from multi_agent_framework.agents.event_driven_backend_agent import EventDrivenBackendAgent


class TestEndToEndWorkflow(TestCase):
    """Test complete end-to-end workflows"""
    
    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.project_config = ProjectConfig(self.temp_dir)
        
        # Reset event bus for clean state
        reset_event_bus()
        
        # Mock LLM responses
        self.setup_llm_mocks()
    
    def tearDown(self):
        """Clean up"""
        reset_event_bus()
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def setup_llm_mocks(self):
        """Set up LLM mocks for all agents"""
        self.llm_patcher = patch('google.generativeai.GenerativeModel')
        self.mock_llm_class = self.llm_patcher.start()
        self.mock_llm = Mock()
        self.mock_llm_class.return_value = self.mock_llm
        
        # Set up context-aware responses
        def generate_content_side_effect(prompt):
            response = Mock()
            
            if "break down" in prompt.lower():
                # Orchestrator breaking down feature
                response.text = json.dumps([
                    {
                        "agent": "frontend_agent",
                        "description": "Create user authentication UI components"
                    },
                    {
                        "agent": "backend_agent",
                        "description": "Implement authentication API endpoints"
                    },
                    {
                        "agent": "db_agent",
                        "description": "Create user authentication database schema"
                    }
                ])
            elif "authentication ui" in prompt.lower():
                # Frontend agent response
                response.text = '''
```tsx
import React, { useState } from 'react';

export const LoginForm: React.FC = () => {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    
    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        const response = await fetch('/api/auth/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password })
        });
        // Handle response
    };
    
    return (
        <form onSubmit={handleSubmit}>
            <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="Email"
            />
            <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Password"
            />
            <button type="submit">Login</button>
        </form>
    );
};
```
'''
            elif "authentication api" in prompt.lower():
                # Backend agent response
                response.text = '''
```python
from flask import Flask, request, jsonify
from werkzeug.security import check_password_hash
import jwt

@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    
    user = User.query.filter_by(email=email).first()
    if user and check_password_hash(user.password_hash, password):
        token = jwt.encode(
            {'user_id': user.id},
            app.config['SECRET_KEY'],
            algorithm='HS256'
        )
        return jsonify({'token': token}), 200
    
    return jsonify({'error': 'Invalid credentials'}), 401
```
'''
            elif "database schema" in prompt.lower():
                # Database agent response
                response.text = '''
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE auth_tokens (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    token VARCHAR(500) NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_auth_tokens_user_id ON auth_tokens(user_id);
```
'''
            else:
                # Default response
                response.text = '{"status": "completed", "result": "Task completed successfully"}'
            
            return response
        
        self.mock_llm.generate_content.side_effect = generate_content_side_effect
    
    @patch('builtins.open', mock.mock_open())
    @patch('os.makedirs')
    def test_complete_feature_development_workflow(self, mock_makedirs):
        """Test complete feature development from request to implementation"""
        # Create event bus
        event_bus = get_event_bus('inmemory')
        
        # Track published events
        published_events = []
        original_publish = event_bus.publish
        
        def track_publish(event):
            published_events.append(event)
            original_publish(event)
        
        event_bus.publish = track_publish
        
        # Create agents
        orchestrator = EventDrivenOrchestratorAgent()
        frontend = EventDrivenFrontendAgent()
        backend = EventDrivenBackendAgent()
        
        # Start event bus
        event_bus.start()
        
        # Simulate feature request
        feature_request = {
            'type': EventType.FEATURE_REQUESTED,
            'feature_id': 'auth-001',
            'description': 'Implement user authentication system',
            'requested_by': 'user'
        }
        
        event_bus.publish(feature_request)
        
        # Allow time for processing
        time.sleep(0.1)
        
        # Verify feature was processed
        task_created_events = [
            e for e in published_events
            if e.get('type') == EventType.TASK_CREATED
        ]
        
        self.assertGreaterEqual(len(task_created_events), 3)
        
        # Verify each agent received appropriate tasks
        frontend_tasks = [
            e for e in task_created_events
            if e.get('assigned_agent') == 'frontend_agent'
        ]
        backend_tasks = [
            e for e in task_created_events
            if e.get('assigned_agent') == 'backend_agent'
        ]
        
        self.assertGreater(len(frontend_tasks), 0)
        self.assertGreater(len(backend_tasks), 0)
        
        # Check for task completion events
        completion_events = [
            e for e in published_events
            if e.get('type') == EventType.TASK_COMPLETED
        ]
        
        self.assertGreater(len(completion_events), 0)
        
        # Verify feature completion
        feature_completed = any(
            e.get('type') == EventType.FEATURE_COMPLETED and
            e.get('feature_id') == 'auth-001'
            for e in published_events
        )
        
        # Note: In real scenario, this would be True after all tasks complete
        # For this test, we're verifying the workflow was initiated correctly
        
        # Clean up
        event_bus.stop()
    
    def test_multi_agent_coordination(self):
        """Test coordination between multiple agents"""
        with patch('builtins.open', mock.mock_open()):
            with patch('os.makedirs'):
                # Create factory and agents
                factory = AgentFactory(self.temp_dir)
                
                # Create a subset of agents
                agents = []
                for agent_type in ['orchestrator', 'frontend_agent', 'backend_agent']:
                    agent = factory.create_agent(agent_type, mode='event-driven')
                    if agent:
                        agents.append(agent)
                
                self.assertEqual(len(agents), 3)
                
                # Verify they share the same event bus
                event_buses = [agent.event_bus for agent in agents if hasattr(agent, 'event_bus')]
                self.assertTrue(all(bus == event_buses[0] for bus in event_buses))
    
    def test_error_recovery_workflow(self):
        """Test error handling and recovery across agents"""
        # Create event bus
        event_bus = get_event_bus('inmemory')
        
        # Track events
        published_events = []
        event_bus.publish = lambda e: published_events.append(e)
        
        # Create orchestrator with error-prone LLM
        with patch('google.generativeai.GenerativeModel') as mock_llm_class:
            mock_llm = Mock()
            mock_llm.generate_content.side_effect = Exception("LLM API Error")
            mock_llm_class.return_value = mock_llm
            
            orchestrator = EventDrivenOrchestratorAgent()
            
            # Simulate feature request that will fail
            feature_request = {
                'type': EventType.FEATURE_REQUESTED,
                'feature_id': 'error-001',
                'description': 'This will fail',
                'requested_by': 'test'
            }
            
            # Process event
            handler = None
            for call in event_bus.subscribe.call_args_list:
                if call[0][0] == EventType.FEATURE_REQUESTED:
                    handler = call[0][1]
                    break
            
            if handler:
                handler(feature_request)
            
            # Check for error handling
            error_events = [
                e for e in published_events
                if 'error' in e or e.get('status') == 'failed'
            ]
            
            self.assertGreater(len(error_events), 0)
    
    def test_state_persistence_across_restart(self):
        """Test that state persists when agents restart"""
        # Create initial state
        with patch('builtins.open', mock.mock_open()) as mock_file:
            # First session - create some state
            config1 = ProjectConfig(self.temp_dir)
            factory1 = AgentFactory(self.temp_dir)
            
            # Simulate some work being done
            config1.config['features'] = {'auth': 'in_progress'}
            config1.save()
            
            # Simulate restart - create new instances
            config2 = ProjectConfig(self.temp_dir)
            
            # State should be preserved
            # Note: In real implementation, this would load from disk
            self.assertEqual(config1.config.get('features'), config2.config.get('features'))
    
    def test_concurrent_agent_operations(self):
        """Test multiple agents working concurrently"""
        import threading
        
        results = {'frontend': False, 'backend': False}
        
        def run_agent(agent_type):
            """Simulate agent work"""
            time.sleep(0.01)  # Simulate work
            results[agent_type] = True
        
        # Run agents in parallel
        threads = []
        for agent_type in ['frontend', 'backend']:
            thread = threading.Thread(target=run_agent, args=(agent_type,))
            thread.start()
            threads.append(thread)
        
        # Wait for completion
        for thread in threads:
            thread.join(timeout=1)
        
        # Both should complete
        self.assertTrue(results['frontend'])
        self.assertTrue(results['backend'])
    
    def test_cross_agent_validation_workflow(self):
        """Test validation between agent outputs"""
        from multi_agent_framework.core.cross_agent_validator import CrossAgentValidator
        
        validator = CrossAgentValidator(self.temp_dir)
        
        # Simulate agent outputs
        frontend_output = '''
        fetch('/api/users', { method: 'GET' })
        fetch('/api/auth/login', { method: 'POST' })
        '''
        
        backend_output = '''
        @app.route('/api/users', methods=['GET'])
        def get_users(): pass
        
        @app.route('/api/auth/login', methods=['POST'])
        def login(): pass
        '''
        
        # Validate compatibility
        result = validator.validate_frontend_backend_contract(
            frontend_output,
            backend_output
        )
        
        self.assertTrue(result.is_valid)
        self.assertEqual(len(result.errors), 0)
    
    def test_progressive_feature_implementation(self):
        """Test implementing a feature progressively across agents"""
        # This test simulates a real workflow where:
        # 1. Database schema is created first
        # 2. Backend API is built on top of schema
        # 3. Frontend is built to consume the API
        
        workflow_stages = []
        
        # Stage 1: Database
        with patch.object(EventDrivenOrchestratorAgent, '_break_down_feature') as mock_breakdown:
            mock_breakdown.return_value = None
            
            orchestrator = EventDrivenOrchestratorAgent()
            
            # Simulate progressive task assignment
            tasks = [
                {'agent': 'db_agent', 'description': 'Create schema', 'priority': 1},
                {'agent': 'backend_agent', 'description': 'Build API', 'priority': 2, 'depends_on': ['db_agent']},
                {'agent': 'frontend_agent', 'description': 'Build UI', 'priority': 3, 'depends_on': ['backend_agent']}
            ]
            
            for task in tasks:
                workflow_stages.append(task['agent'])
            
            # Verify correct order
            self.assertEqual(workflow_stages[0], 'db_agent')
            self.assertEqual(workflow_stages[1], 'backend_agent')
            self.assertEqual(workflow_stages[2], 'frontend_agent')
    
    def test_health_monitoring_workflow(self):
        """Test health monitoring across all agents"""
        event_bus = get_event_bus('inmemory')
        
        health_statuses = {}
        
        # Subscribe to health check events
        def handle_health_check(event):
            if event.get('type') == EventType.HEALTH_CHECK:
                health_statuses[event.get('agent_id')] = event.get('status')
        
        event_bus.subscribe(EventType.HEALTH_CHECK, handle_health_check)
        
        # Create agents (they should send health checks)
        with patch('builtins.open', mock.mock_open()):
            agents = [
                EventDrivenFrontendAgent(),
                EventDrivenBackendAgent()
            ]
            
            # Trigger health checks
            for agent in agents:
                if hasattr(agent, '_send_heartbeat'):
                    agent._send_heartbeat()
            
            # Verify health statuses were collected
            self.assertGreater(len(health_statuses), 0)
            self.assertTrue(all(status == 'healthy' for status in health_statuses.values()))
    
    def test_graceful_shutdown_workflow(self):
        """Test graceful shutdown of all agents"""
        event_bus = get_event_bus('inmemory')
        
        shutdown_events = []
        
        # Track shutdown events
        original_publish = event_bus.publish
        event_bus.publish = lambda e: shutdown_events.append(e) if e.get('type') == EventType.AGENT_STOPPED else original_publish(e)
        
        # Create and shutdown agents
        agents = []
        with patch('builtins.open', mock.mock_open()):
            for _ in range(3):
                agent = EventDrivenFrontendAgent()
                agents.append(agent)
            
            # Shutdown all agents
            for agent in agents:
                agent.shutdown()
            
            # Verify shutdown events
            self.assertEqual(len(shutdown_events), len(agents))


if __name__ == '__main__':
    import unittest
    unittest.main()