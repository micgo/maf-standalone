#!/usr/bin/env python3
"""
Tests for SmartIntegrator
"""
import os
from unittest import TestCase, mock
from unittest.mock import Mock, patch, MagicMock, mock_open

from multi_agent_framework.core.smart_integrator import SmartIntegrator


class TestSmartIntegrator(TestCase):
    """Test SmartIntegrator functionality"""
    
    def setUp(self):
        """Set up test environment"""
        self.temp_dir = '/tmp/test_smart_integrator'
        os.makedirs(self.temp_dir, exist_ok=True)
        self.integrator = SmartIntegrator(self.temp_dir)
    
    def tearDown(self):
        """Clean up"""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_initialization(self):
        """Test integrator initialization"""
        self.assertEqual(self.integrator.project_root, self.temp_dir)
        self.assertIsNotNone(self.integrator.file_integrator)
        self.assertIsNotNone(self.integrator.analyzer)
    
    def test_should_create_new_file_component(self):
        """Test decision to create new file for component"""
        # Test React component
        code = '''
        export const UserProfile = () => {
            return <div>User Profile</div>;
        };
        '''
        
        result = self.integrator._should_create_new_file(code, 'component')
        self.assertTrue(result)
    
    def test_should_create_new_file_small_snippet(self):
        """Test decision for small code snippets"""
        code = 'const API_URL = "http://localhost:3000";'
        
        result = self.integrator._should_create_new_file(code, 'config')
        self.assertFalse(result)  # Too small for new file
    
    def test_find_integration_target_existing_file(self):
        """Test finding existing file for integration"""
        code = '''
        export const formatDate = (date) => {
            return new Date(date).toLocaleDateString();
        };
        '''
        
        # Mock existing utility file
        with patch('os.walk') as mock_walk:
            mock_walk.return_value = [
                (self.temp_dir, ['utils'], []),
                (os.path.join(self.temp_dir, 'utils'), [], ['date.js', 'format.js'])
            ]
            
            with patch('builtins.open', mock_open(read_data='// Date utilities\n')):
                target = self.integrator._find_integration_target(code, 'utility')
                
                self.assertIsNotNone(target)
                self.assertIn('utils', target)
    
    def test_integrate_component(self):
        """Test integrating a React component"""
        component_code = '''
        import React from 'react';
        
        export const Button = ({ label, onClick }) => {
            return <button onClick={onClick}>{label}</button>;
        };
        '''
        
        with patch('os.makedirs'):
            with patch('builtins.open', mock_open()) as mock_file:
                result = self.integrator.integrate_code(
                    component_code,
                    'component',
                    'Button',
                    {'component_type': 'ui'}
                )
                
                self.assertTrue(result['created_new_file'])
                self.assertIn('components', result['file_path'])
                mock_file.assert_called()
    
    def test_integrate_api_endpoint(self):
        """Test integrating API endpoint into existing file"""
        endpoint_code = '''
        @app.route('/api/users/<int:user_id>')
        def get_user(user_id):
            user = User.query.get_or_404(user_id)
            return jsonify(user.to_dict())
        '''
        
        existing_content = '''
        from flask import Flask, jsonify
        
        app = Flask(__name__)
        
        @app.route('/api/users')
        def get_users():
            return jsonify([])
        '''
        
        with patch('os.walk') as mock_walk:
            mock_walk.return_value = [
                (self.temp_dir, ['api'], []),
                (os.path.join(self.temp_dir, 'api'), [], ['routes.py'])
            ]
            
            with patch('builtins.open', mock_open(read_data=existing_content)) as mock_file:
                result = self.integrator.integrate_code(
                    endpoint_code,
                    'api_endpoint',
                    'get_user'
                )
                
                self.assertFalse(result['created_new_file'])
                self.assertEqual(result['integration_type'], 'appended')
    
    def test_integrate_with_imports(self):
        """Test integrating code with import management"""
        new_code = '''
        import { useState, useEffect } from 'react';
        import axios from 'axios';
        
        export const DataFetcher = () => {
            const [data, setData] = useState(null);
            
            useEffect(() => {
                axios.get('/api/data').then(res => setData(res.data));
            }, []);
            
            return <div>{data}</div>;
        };
        '''
        
        existing_code = '''
        import React from 'react';
        import { useState } from 'react';
        
        export const Header = () => {
            return <header>App Header</header>;
        };
        '''
        
        integrated = self.integrator._merge_imports(existing_code, new_code)
        
        # Should merge imports intelligently
        self.assertIn('useEffect', integrated)
        self.assertIn('axios', integrated)
        self.assertEqual(integrated.count("import { useState"), 1)  # No duplicate
    
    def test_integrate_database_migration(self):
        """Test integrating database migrations"""
        migration_code = '''
        -- Add user roles table
        CREATE TABLE roles (
            id SERIAL PRIMARY KEY,
            name VARCHAR(50) UNIQUE NOT NULL,
            permissions JSONB DEFAULT '{}'
        );
        
        ALTER TABLE users ADD COLUMN role_id INTEGER REFERENCES roles(id);
        '''
        
        with patch('os.makedirs'):
            with patch('builtins.open', mock_open()) as mock_file:
                result = self.integrator.integrate_code(
                    migration_code,
                    'database_migration',
                    'add_user_roles'
                )
                
                self.assertTrue(result['created_new_file'])
                self.assertIn('migrations', result['file_path'])
    
    def test_detect_code_type(self):
        """Test automatic code type detection"""
        test_cases = [
            ("export const Component = () => {}", "react_component"),
            ("@app.route('/api')", "flask_endpoint"),
            ("CREATE TABLE users", "sql"),
            ("class UserModel(db.Model):", "python_model"),
            ("describe('test', () => {", "test"),
            ("# Dockerfile\nFROM node:14", "config")
        ]
        
        for code, expected_type in test_cases:
            detected = self.integrator._detect_code_type(code)
            self.assertEqual(detected, expected_type)
    
    def test_validate_integration(self):
        """Test integration validation"""
        # Valid integration
        valid_result = {
            'file_path': '/tmp/test/components/Button.jsx',
            'created_new_file': True,
            'integration_type': 'new_file'
        }
        
        is_valid, errors = self.integrator._validate_integration(valid_result)
        self.assertTrue(is_valid)
        self.assertEqual(len(errors), 0)
        
        # Invalid integration
        invalid_result = {
            'file_path': None,
            'error': 'Failed to integrate'
        }
        
        is_valid, errors = self.integrator._validate_integration(invalid_result)
        self.assertFalse(is_valid)
        self.assertGreater(len(errors), 0)
    
    def test_smart_file_naming(self):
        """Test intelligent file naming"""
        test_cases = [
            ("UserProfile", "component", "UserProfile.jsx"),
            ("get_users", "api_endpoint", "users.py"),
            ("CREATE TABLE products", "database", "products.sql"),
            ("test user creation", "test", "test_user_creation.py")
        ]
        
        for description, code_type, expected in test_cases:
            filename = self.integrator._generate_filename(description, code_type)
            self.assertEqual(filename, expected)
    
    def test_handle_conflicts(self):
        """Test conflict resolution during integration"""
        existing_code = '''
        def get_user(user_id):
            return User.query.get(user_id)
        '''
        
        new_code = '''
        def get_user(user_id):
            # Enhanced version with error handling
            user = User.query.get(user_id)
            if not user:
                raise NotFound("User not found")
            return user
        '''
        
        resolved = self.integrator._resolve_conflicts(existing_code, new_code, 'get_user')
        
        # Should prefer new code or merge intelligently
        self.assertIn('NotFound', resolved)
    
    def test_integration_rollback(self):
        """Test rollback on integration failure"""
        with patch('builtins.open', mock_open()) as mock_file:
            mock_file.side_effect = IOError("Disk full")
            
            result = self.integrator.integrate_code(
                "test code",
                "component",
                "TestComponent"
            )
            
            self.assertFalse(result.get('success', True))
            self.assertIn('error', result)
    
    def test_batch_integration(self):
        """Test integrating multiple code pieces"""
        code_pieces = [
            {
                'code': 'export const Header = () => <header>Header</header>',
                'type': 'component',
                'name': 'Header'
            },
            {
                'code': 'export const Footer = () => <footer>Footer</footer>',
                'type': 'component', 
                'name': 'Footer'
            }
        ]
        
        with patch('os.makedirs'):
            with patch('builtins.open', mock_open()):
                results = self.integrator.integrate_batch(code_pieces)
                
                self.assertEqual(len(results), 2)
                self.assertTrue(all(r.get('created_new_file') for r in results))
    
    def test_integration_with_dependencies(self):
        """Test handling code with dependencies"""
        component_code = '''
        import { Button } from './Button';
        import { useAuth } from '../hooks/useAuth';
        
        export const LoginForm = () => {
            const { login } = useAuth();
            return <Button onClick={login}>Login</Button>;
        };
        '''
        
        # Check if dependencies exist
        with patch('os.path.exists') as mock_exists:
            mock_exists.side_effect = lambda p: 'Button' in p or 'useAuth' in p
            
            deps = self.integrator._check_dependencies(component_code)
            self.assertEqual(len(deps['missing']), 0)
            self.assertEqual(len(deps['found']), 2)
    
    def test_preserve_file_structure(self):
        """Test preserving project file structure conventions"""
        # Mock project structure detection
        with patch.object(self.integrator.analyzer, 'analyze_structure') as mock_analyze:
            mock_analyze.return_value = {
                'framework': 'react',
                'structure_type': 'feature-based',
                'conventions': {
                    'components': 'PascalCase',
                    'utilities': 'camelCase'
                }
            }
            
            path = self.integrator._determine_file_path('UserList', 'component')
            self.assertIn('features', path)  # Feature-based structure
    
    def test_integration_logging(self):
        """Test integration operation logging"""
        with patch('builtins.open', mock_open()):
            self.integrator.integrate_code(
                "test code",
                "component",
                "TestComponent"
            )
            
            # Check if operation was logged
            self.assertGreater(len(self.integrator.integration_history), 0)
            last_op = self.integrator.integration_history[-1]
            self.assertEqual(last_op['name'], 'TestComponent')
    
    def test_dry_run_mode(self):
        """Test dry run integration without file changes"""
        with patch('builtins.open', mock_open()) as mock_file:
            result = self.integrator.integrate_code(
                "test code",
                "component", 
                "TestComponent",
                dry_run=True
            )
            
            self.assertTrue(result.get('dry_run'))
            self.assertIn('file_path', result)
            mock_file.assert_not_called()  # No actual file operations


if __name__ == '__main__':
    import unittest
    unittest.main()