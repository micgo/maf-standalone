#!/usr/bin/env python3
"""
Tests for FileIntegrator
"""
import os
from unittest import TestCase, mock
from unittest.mock import Mock, patch, MagicMock, mock_open

from multi_agent_framework.core.file_integrator import FileIntegrator


class TestFileIntegrator(TestCase):
    """Test FileIntegrator functionality"""
    
    def setUp(self):
        """Set up test environment"""
        self.temp_dir = '/tmp/test_file_integrator'
        os.makedirs(self.temp_dir, exist_ok=True)
        self.integrator = FileIntegrator(self.temp_dir)
    
    def tearDown(self):
        """Clean up"""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_initialization(self):
        """Test integrator initialization"""
        self.assertEqual(self.integrator.project_root, self.temp_dir)
        self.assertIsInstance(self.integrator.integration_log, list)
    
    def test_find_similar_files(self):
        """Test finding similar files for integration"""
        # Mock file system
        with patch('os.walk') as mock_walk:
            mock_walk.return_value = [
                (self.temp_dir, ['components'], []),
                (os.path.join(self.temp_dir, 'components'), [], [
                    'UserList.jsx',
                    'UserCard.jsx', 
                    'ProductList.jsx',
                    'utils.js'
                ])
            ]
            
            # Find files similar to user components
            similar = self.integrator.find_similar_files('UserProfile', 'jsx')
            
            self.assertGreater(len(similar), 0)
            self.assertIn('UserCard.jsx', similar[0])  # Most similar
    
    def test_integrate_imports(self):
        """Test smart import integration"""
        existing_code = '''
        import React from 'react';
        import { useState } from 'react';
        
        export const Component = () => {
            const [data, setData] = useState(null);
            return <div>{data}</div>;
        };
        '''
        
        new_imports = [
            "import { useEffect } from 'react';",
            "import axios from 'axios';",
            "import { useState } from 'react';"  # Duplicate
        ]
        
        result = self.integrator.integrate_imports(existing_code, new_imports)
        
        # Should add useEffect to existing React import
        self.assertIn('useState, useEffect', result)
        # Should add axios
        self.assertIn('axios', result)
        # Should not duplicate imports
        self.assertEqual(result.count("import { useState"), 1)
    
    def test_integrate_exports(self):
        """Test export statement integration"""
        existing_code = '''
        export { UserList } from './UserList';
        export { UserCard } from './UserCard';
        '''
        
        new_export = "export { UserProfile } from './UserProfile';"
        
        result = self.integrator.integrate_exports(existing_code, new_export)
        
        self.assertIn('UserProfile', result)
        self.assertIn('UserList', result)  # Preserves existing
    
    def test_integrate_into_file(self):
        """Test integrating code into existing file"""
        existing_content = '''
        class UserService:
            def get_user(self, user_id):
                return User.query.get(user_id)
        '''
        
        new_method = '''
            def create_user(self, user_data):
                user = User(**user_data)
                db.session.add(user)
                db.session.commit()
                return user
        '''
        
        with patch('builtins.open', mock_open(read_data=existing_content)) as mock_file:
            result = self.integrator.integrate_into_file(
                '/tmp/test/services/user_service.py',
                new_method,
                integration_point='class UserService'
            )
            
            self.assertTrue(result['success'])
            self.assertIn('integrated', result['action'])
            
            # Check file was written
            handle = mock_file()
            written_content = ''.join(call.args[0] for call in handle.write.call_args_list)
            self.assertIn('create_user', written_content)
    
    def test_detect_integration_points(self):
        """Test detecting where to integrate code"""
        file_content = '''
        import React from 'react';
        
        // Components
        export const Header = () => <header>Header</header>;
        
        // Utilities
        export const formatDate = (date) => {
            return new Date(date).toLocaleDateString();
        };
        
        // Main export
        export default { Header, formatDate };
        '''
        
        points = self.integrator.detect_integration_points(file_content)
        
        self.assertIn('components', points)
        self.assertIn('utilities', points)
        self.assertIn('exports', points)
    
    def test_validate_syntax_before_integration(self):
        """Test syntax validation before integration"""
        valid_code = '''
        def hello():
            return "Hello, World!"
        '''
        
        invalid_code = '''
        def hello()
            return "Missing colon"
        '''
        
        self.assertTrue(self.integrator.validate_syntax(valid_code, 'python'))
        self.assertFalse(self.integrator.validate_syntax(invalid_code, 'python'))
    
    def test_merge_similar_functions(self):
        """Test merging similar functions intelligently"""
        existing = '''
        def calculate_total(items):
            return sum(item.price for item in items)
        '''
        
        new = '''
        def calculate_total(items, include_tax=True):
            total = sum(item.price for item in items)
            if include_tax:
                total *= 1.1
            return total
        '''
        
        merged = self.integrator.merge_similar_code(existing, new, 'calculate_total')
        
        # Should use enhanced version
        self.assertIn('include_tax', merged)
        self.assertIn('1.1', merged)
    
    def test_preserve_formatting(self):
        """Test preserving code formatting style"""
        existing_code = '''
        const styles = {
            container: {
                padding: '20px',
                margin: '10px'
            }
        };
        '''
        
        new_code = '''
        header: {
            backgroundColor: '#333',
            color: 'white'
        }
        '''
        
        result = self.integrator.integrate_into_object(existing_code, new_code, 'styles')
        
        # Should maintain formatting
        self.assertIn('    header: {', result)  # Proper indentation
    
    def test_handle_circular_imports(self):
        """Test detection and handling of circular imports"""
        file_a = '''
        from .file_b import ComponentB
        
        export const ComponentA = () => {
            return <ComponentB />;
        };
        '''
        
        file_b = '''
        from .file_a import ComponentA  // Would create circular dependency
        '''
        
        has_circular = self.integrator.detect_circular_imports(file_a, file_b)
        self.assertTrue(has_circular)
    
    def test_integration_with_comments(self):
        """Test preserving and adding helpful comments"""
        existing = '''
        # User management functions
        def get_user(user_id):
            """Retrieve user by ID"""
            return User.query.get(user_id)
        '''
        
        new_code = '''
        def update_user(user_id, data):
            """Update user information"""
            user = get_user(user_id)
            for key, value in data.items():
                setattr(user, key, value)
            return user
        '''
        
        result = self.integrator.integrate_with_comments(existing, new_code)
        
        # Should preserve existing comments
        self.assertIn('# User management functions', result)
        # Should add integration comment
        self.assertIn('# Integrated by', result)
    
    def test_rollback_integration(self):
        """Test rollback capability for failed integrations"""
        original_content = "original code"
        
        with patch('builtins.open', mock_open(read_data=original_content)) as mock_file:
            # Simulate integration failure
            with patch.object(self.integrator, 'integrate_into_file') as mock_integrate:
                mock_integrate.side_effect = Exception("Integration failed")
                
                result = self.integrator.safe_integrate(
                    '/tmp/test/file.py',
                    'new code'
                )
                
                self.assertFalse(result['success'])
                self.assertIn('rolled back', result['message'])
    
    def test_integration_dry_run(self):
        """Test dry run mode without actual file changes"""
        with patch('builtins.open', mock_open()) as mock_file:
            result = self.integrator.integrate_into_file(
                '/tmp/test/file.py',
                'new code',
                dry_run=True
            )
            
            self.assertTrue(result['dry_run'])
            self.assertIn('would integrate', result['action'])
            mock_file().write.assert_not_called()
    
    def test_smart_section_detection(self):
        """Test detecting code sections for integration"""
        react_file = '''
        import React from 'react';
        
        // Types
        interface User {
            id: string;
            name: string;
        }
        
        // Hooks  
        const useUser = () => {
            return { user: null };
        };
        
        // Components
        export const UserProfile = () => {
            return <div>Profile</div>;
        };
        '''
        
        sections = self.integrator.detect_sections(react_file)
        
        self.assertIn('imports', sections)
        self.assertIn('types', sections)
        self.assertIn('hooks', sections)
        self.assertIn('components', sections)
    
    def test_merge_configurations(self):
        """Test merging configuration files"""
        existing_config = '''
        {
            "name": "my-app",
            "version": "1.0.0",
            "scripts": {
                "start": "node index.js",
                "test": "jest"
            }
        }
        '''
        
        new_config = '''
        {
            "scripts": {
                "build": "webpack",
                "lint": "eslint ."
            },
            "dependencies": {
                "express": "^4.18.0"
            }
        }
        '''
        
        merged = self.integrator.merge_json_configs(existing_config, new_config)
        merged_obj = json.loads(merged)
        
        # Should merge scripts
        self.assertEqual(len(merged_obj['scripts']), 4)
        self.assertIn('build', merged_obj['scripts'])
        # Should add dependencies
        self.assertIn('dependencies', merged_obj)
    
    def test_integration_history_tracking(self):
        """Test tracking integration history"""
        with patch('builtins.open', mock_open()):
            self.integrator.integrate_into_file(
                '/tmp/test/file.py',
                'new code'
            )
            
            history = self.integrator.get_integration_history()
            self.assertEqual(len(history), 1)
            self.assertIn('timestamp', history[0])
            self.assertIn('file_path', history[0])
    
    def test_smart_conflict_resolution(self):
        """Test intelligent conflict resolution strategies"""
        strategies = self.integrator.get_conflict_resolution_strategies()
        
        self.assertIn('merge', strategies)
        self.assertIn('replace', strategies)
        self.assertIn('append', strategies)
        self.assertIn('prepend', strategies)
        
        # Test applying strategy
        result = self.integrator.resolve_conflict(
            'old code',
            'new code',
            strategy='merge'
        )
        
        self.assertIsNotNone(result)


if __name__ == '__main__':
    import unittest
    unittest.main()