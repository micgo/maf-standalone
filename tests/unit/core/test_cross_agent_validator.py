#!/usr/bin/env python3
"""
Tests for CrossAgentValidator
"""
import os
from unittest import TestCase, mock
from unittest.mock import Mock, patch, MagicMock

from multi_agent_framework.core.cross_agent_validator import (
    CrossAgentValidator, ValidationResult, APIContract
)


class TestCrossAgentValidator(TestCase):
    """Test CrossAgentValidator functionality"""
    
    def setUp(self):
        """Set up test environment"""
        self.temp_dir = '/tmp/test_validator'
        os.makedirs(self.temp_dir, exist_ok=True)
        self.validator = CrossAgentValidator(self.temp_dir)
    
    def tearDown(self):
        """Clean up"""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_initialization(self):
        """Test validator initialization"""
        self.assertEqual(self.validator.project_root, self.temp_dir)
        self.assertEqual(self.validator.api_contracts, {})
        self.assertEqual(self.validator.component_dependencies, {})
        self.assertEqual(self.validator.database_schemas, {})
    
    def test_validate_frontend_backend_contract_matching(self):
        """Test validation when frontend and backend match"""
        frontend_code = '''
        // Frontend code
        fetch('/api/users', { method: 'GET' })
        fetch('/api/users', { method: 'POST', body: JSON.stringify({name: 'test'}) })
        '''
        
        backend_code = '''
        @app.route('/api/users', methods=['GET'])
        def get_users():
            return jsonify([])
        
        @app.route('/api/users', methods=['POST'])
        def create_user():
            return jsonify({'id': 1})
        '''
        
        result = self.validator.validate_frontend_backend_contract(frontend_code, backend_code)
        
        self.assertTrue(result.is_valid)
        self.assertEqual(len(result.errors), 0)
    
    def test_validate_frontend_backend_contract_mismatch(self):
        """Test validation when frontend calls non-existent endpoint"""
        frontend_code = '''
        fetch('/api/products', { method: 'GET' })
        fetch('/api/orders', { method: 'POST' })
        '''
        
        backend_code = '''
        @app.route('/api/users', methods=['GET'])
        def get_users():
            return jsonify([])
        '''
        
        result = self.validator.validate_frontend_backend_contract(frontend_code, backend_code)
        
        self.assertFalse(result.is_valid)
        self.assertGreater(len(result.errors), 0)
        self.assertIn('products', str(result.errors))
    
    def test_validate_database_schema_consistency(self):
        """Test database schema validation across different files"""
        migration_sql = '''
        CREATE TABLE users (
            id SERIAL PRIMARY KEY,
            email VARCHAR(255) UNIQUE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        '''
        
        backend_code = '''
        class User(Model):
            id = IntegerField(primary_key=True)
            email = CharField(unique=True)
            created_at = DateTimeField(auto_now_add=True)
        '''
        
        result = self.validator.validate_database_schema_consistency(migration_sql, backend_code)
        
        self.assertTrue(result.is_valid)
    
    def test_validate_database_schema_mismatch(self):
        """Test database schema validation with mismatches"""
        migration_sql = '''
        CREATE TABLE users (
            id SERIAL PRIMARY KEY,
            email VARCHAR(255) UNIQUE NOT NULL,
            username VARCHAR(100) NOT NULL
        );
        '''
        
        backend_code = '''
        class User(Model):
            id = IntegerField(primary_key=True)
            email = CharField(unique=True)
            # Missing username field
        '''
        
        result = self.validator.validate_database_schema_consistency(migration_sql, backend_code)
        
        self.assertFalse(result.is_valid)
        self.assertIn('username', str(result.errors))
    
    def test_validate_component_dependencies(self):
        """Test component dependency validation"""
        parent_component = '''
        export const UserList = ({ users }) => {
            return users.map(user => <UserCard key={user.id} user={user} />)
        }
        '''
        
        child_component = '''
        export const UserCard = ({ user }) => {
            return <div>{user.name}</div>
        }
        '''
        
        result = self.validator.validate_component_dependencies(parent_component, child_component)
        
        self.assertTrue(result.is_valid)
    
    def test_validate_security_constraints(self):
        """Test security validation across agents"""
        backend_code = '''
        @app.route('/api/admin/users')
        @require_admin
        def admin_users():
            return jsonify(User.query.all())
        '''
        
        frontend_code = '''
        // Admin only
        if (user.role === 'admin') {
            fetch('/api/admin/users')
        }
        '''
        
        result = self.validator.validate_security_constraints(backend_code, frontend_code)
        
        self.assertTrue(result.is_valid)
    
    def test_validate_data_types_consistency(self):
        """Test data type consistency between frontend and backend"""
        backend_response = '''
        return jsonify({
            'id': 123,
            'price': 99.99,
            'active': True,
            'tags': ['new', 'featured']
        })
        '''
        
        frontend_types = '''
        interface Product {
            id: number;
            price: number;
            active: boolean;
            tags: string[];
        }
        '''
        
        result = self.validator.validate_data_types_consistency(backend_response, frontend_types)
        
        self.assertTrue(result.is_valid)
    
    def test_extract_api_contract(self):
        """Test API contract extraction"""
        backend_code = '''
        @app.route('/api/users/<int:user_id>', methods=['GET', 'PUT'])
        @validate_json({
            'name': {'type': 'string', 'required': True},
            'email': {'type': 'string', 'format': 'email'}
        })
        def user_detail(user_id):
            """Get or update user details"""
            pass
        '''
        
        contracts = self.validator.extract_api_contracts(backend_code)
        
        self.assertGreater(len(contracts), 0)
        self.assertIn('/api/users/', contracts[0].endpoint)
    
    def test_validate_environment_variables(self):
        """Test environment variable usage validation"""
        backend_env = '''
        DATABASE_URL = os.getenv('DATABASE_URL')
        SECRET_KEY = os.getenv('SECRET_KEY')
        '''
        
        deployment_config = '''
        environment:
          - DATABASE_URL=postgresql://...
          - SECRET_KEY=mysecret
        '''
        
        result = self.validator.validate_environment_variables(backend_env, deployment_config)
        
        self.assertTrue(result.is_valid)
    
    def test_validate_error_handling_consistency(self):
        """Test error handling consistency across agents"""
        backend_errors = '''
        class UserNotFoundError(Exception):
            status_code = 404
            
        class ValidationError(Exception):
            status_code = 400
        '''
        
        frontend_handling = '''
        catch (error) {
            if (error.status === 404) {
                showError('User not found');
            } else if (error.status === 400) {
                showError('Invalid input');
            }
        }
        '''
        
        result = self.validator.validate_error_handling(backend_errors, frontend_handling)
        
        self.assertTrue(result.is_valid)
    
    def test_generate_validation_report(self):
        """Test validation report generation"""
        # Add some validation results
        self.validator.api_contracts = {
            '/api/users': APIContract(
                endpoint='/api/users',
                method='GET',
                request_schema={},
                response_schema={'type': 'array'},
                auth_required=False
            )
        }
        
        report = self.validator.generate_validation_report()
        
        self.assertIn('API Contracts', report)
        self.assertIn('/api/users', report)
    
    def test_suggest_fixes(self):
        """Test fix suggestions for validation errors"""
        errors = [
            "Frontend calls /api/products but endpoint not found in backend",
            "Database field 'username' missing in ORM model"
        ]
        
        suggestions = self.validator.suggest_fixes(errors)
        
        self.assertGreater(len(suggestions), 0)
        self.assertIn('endpoint', suggestions[0].lower())
    
    def test_validate_async_operations(self):
        """Test validation of async operations consistency"""
        frontend_async = '''
        const fetchUsers = async () => {
            setLoading(true);
            try {
                const users = await api.getUsers();
                setUsers(users);
            } finally {
                setLoading(false);
            }
        }
        '''
        
        backend_async = '''
        @app.route('/api/users')
        async def get_users():
            users = await User.query.all()
            return jsonify(users)
        '''
        
        result = self.validator.validate_async_operations(frontend_async, backend_async)
        
        self.assertTrue(result.is_valid)
    
    def test_validate_pagination_consistency(self):
        """Test pagination implementation consistency"""
        backend_pagination = '''
        @app.route('/api/items')
        def get_items():
            page = request.args.get('page', 1, type=int)
            per_page = request.args.get('limit', 20, type=int)
            
            items = Item.query.paginate(page=page, per_page=per_page)
            return jsonify({
                'items': items.items,
                'total': items.total,
                'page': page,
                'pages': items.pages
            })
        '''
        
        frontend_pagination = '''
        const [page, setPage] = useState(1);
        const [limit] = useState(20);
        
        const { data } = await fetch(`/api/items?page=${page}&limit=${limit}`);
        '''
        
        result = self.validator.validate_pagination(backend_pagination, frontend_pagination)
        
        self.assertTrue(result.is_valid)
    
    def test_validate_file_paths_consistency(self):
        """Test file path references consistency"""
        # Mock file system
        with patch('os.path.exists') as mock_exists:
            mock_exists.return_value = True
            
            imports = '''
            import UserList from './components/UserList';
            import { api } from '../services/api';
            '''
            
            result = self.validator.validate_file_paths(imports, self.temp_dir)
            
            self.assertTrue(result.is_valid)
    
    def test_validate_naming_conventions(self):
        """Test naming convention consistency"""
        code_samples = {
            'frontend': 'const getUserData = () => {}',
            'backend': 'def get_user_data():',
            'database': 'CREATE TABLE user_data'
        }
        
        result = self.validator.validate_naming_conventions(code_samples)
        
        # Should detect inconsistent naming (camelCase vs snake_case)
        self.assertGreater(len(result.warnings), 0)
    
    def test_batch_validation(self):
        """Test batch validation of multiple agent outputs"""
        agent_outputs = {
            'frontend': {'code': 'fetch("/api/users")', 'type': 'component'},
            'backend': {'code': '@app.route("/api/users")', 'type': 'endpoint'},
            'database': {'code': 'CREATE TABLE users', 'type': 'schema'}
        }
        
        results = self.validator.validate_all(agent_outputs)
        
        self.assertIn('frontend-backend', results)
        self.assertIn('backend-database', results)
    
    def test_validation_caching(self):
        """Test validation result caching for performance"""
        # First validation
        result1 = self.validator.validate_frontend_backend_contract("code1", "code2")
        
        # Second validation with same inputs should use cache
        with patch.object(self.validator, '_extract_frontend_api_calls') as mock_extract:
            result2 = self.validator.validate_frontend_backend_contract("code1", "code2")
            
            # Should not call extraction again if cached
            self.assertEqual(result1.is_valid, result2.is_valid)


if __name__ == '__main__':
    import unittest
    unittest.main()