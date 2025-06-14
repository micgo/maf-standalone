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
        fetch('/api/users', { method: "GET" })
        fetch('/api/users', { method: "POST", body: JSON.stringify({name: 'test'}) })
        '''
        
        backend_code = '''
        router.get('/api/users', (req, res) => {
            res.json([]);
        });
        
        router.post('/api/users', (req, res) => {
            res.json({id: 1});
        });
        '''
        
        result = self.validator.validate_frontend_backend_contract(frontend_code, backend_code)
        
        # Debug output
        if not result.is_valid:
            print(f"Errors: {result.errors}")
            print(f"Warnings: {result.warnings}")
        
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
    
    def test_validate_database_schema_usage(self):
        """Test database schema usage validation"""
        # First load some schemas
        self.validator.database_schemas = {
            'users': {
                'columns': {
                    'id': {'type': 'SERIAL', 'required': True},
                    'email': {'type': 'VARCHAR', 'required': True},
                    'username': {'type': 'VARCHAR', 'required': True}
                }
            }
        }
        
        backend_code = '''
        const user = await supabase.from('users').select('id, email, username')
        '''
        
        result = self.validator.validate_database_schema_usage(backend_code, 'query')
        
        self.assertTrue(result.is_valid)
    
    def test_validate_database_schema_usage_missing_field(self):
        """Test database schema validation with missing field"""
        self.validator.database_schemas = {
            'users': {
                'columns': {
                    'id': {'type': 'SERIAL', 'required': True},
                    'email': {'type': 'VARCHAR', 'required': True},
                    'username': {'type': 'VARCHAR', 'required': True}
                }
            }
        }
        
        backend_code = '''
        const user = await supabase.from('users').select('id, email, invalid_field')
        '''
        
        result = self.validator.validate_database_schema_usage(backend_code, 'query')
        
        self.assertFalse(result.is_valid)
        self.assertIn('invalid_field', str(result.errors))
    
    def test_validate_component_dependencies(self):
        """Test component dependency validation"""
        component_code = '''
        import { UserCard } from './components/UserCard';
        import { useAuth } from './hooks/useAuth';
        import { formatDate } from './utils/date';
        
        export const UserList = ({ users }) => {
            const { currentUser } = useAuth();
            return users.map(user => <UserCard key={user.id} user={user} />)
        }
        '''
        
        # Mock that UserCard exists but useAuth doesn't
        with patch.object(self.validator, '_component_exists', side_effect=lambda name: name == 'UserCard'):
            with patch.object(self.validator, '_hook_exists', return_value=False):
                with patch.object(self.validator, '_util_exists', return_value=True):
                    result = self.validator.validate_component_dependencies(component_code, 'UserList')
        
        self.assertFalse(result.is_valid)
        self.assertIn('useAuth', str(result.errors))
    
    def test_validate_security_compliance(self):
        """Test security compliance validation"""
        backend_code = '''
        const apiKey = "sk-12345678901234567890";
        const password = "hardcoded_password";
        console.log("Debug:", apiKey);
        eval(userInput);
        '''
        
        result = self.validator.validate_security_compliance(backend_code, 'api')
        
        self.assertFalse(result.is_valid)
        self.assertGreater(len(result.errors), 0)
        self.assertTrue(any('secret' in err.lower() for err in result.errors))
        self.assertTrue(any('eval' in err.lower() for err in result.errors))
    
    def test_validate_test_coverage(self):
        """Test validation of test coverage"""
        component_code = '''
        export function calculateTotal(items) {
            return items.reduce((sum, item) => sum + item.price, 0);
        }
        
        export function formatCurrency(amount) {
            return `$${amount.toFixed(2)}`;
        }
        
        export const ShoppingCart = ({ items }) => {
            const total = calculateTotal(items);
            return <div>Total: {formatCurrency(total)}</div>;
        };
        '''
        
        test_code = '''
        describe('ShoppingCart', () => {
            it('calculates total correctly', () => {
                const items = [{price: 10}, {price: 20}];
                expect(calculateTotal(items)).toBe(30);
            });
        });
        '''
        
        result = self.validator.validate_test_coverage(component_code, test_code)
        
        # Test coverage validation expects describe and test blocks
        self.assertTrue(result.is_valid)  # Has describe and test blocks
        self.assertGreater(len(result.warnings), 0)  # Should warn about untested functions
        self.assertTrue(any('formatCurrency' in w for w in result.warnings))
    
    def test_extract_frontend_api_calls(self):
        """Test extraction of API calls from frontend code"""
        frontend_code = '''
        // Fetch call
        fetch('/api/users', { method: 'GET' });
        
        // Axios calls
        axios.post('/api/users', userData);
        axios.get('/api/products');
        
        // Axios with config
        axios({
            url: '/api/orders',
            method: 'DELETE'
        });
        '''
        
        api_calls = self.validator._extract_frontend_api_calls(frontend_code)
        
        self.assertEqual(len(api_calls), 4)
        endpoints = [call['endpoint'] for call in api_calls]
        self.assertIn('/api/users', endpoints)
        self.assertIn('/api/products', endpoints)
        self.assertIn('/api/orders', endpoints)
    
    def test_extract_backend_endpoints(self):
        """Test extraction of API endpoints from backend code"""
        backend_code = '''
        // Next.js API route
        export async function GET(request) {
            return Response.json({ users: [] });
        }
        
        export async function POST(request) {
            const data = await request.json();
            return Response.json({ id: 1 });
        }
        
        // Express routes
        router.get('/api/products', getProducts);
        router.post('/api/orders', createOrder);
        router.delete('/api/orders/:id', deleteOrder);
        '''
        
        endpoints = self.validator._extract_backend_endpoints(backend_code)
        
        self.assertGreater(len(endpoints), 0)
        methods = [ep['method'] for ep in endpoints]
        self.assertIn('GET', methods)
        self.assertIn('POST', methods)
    
    def test_endpoints_match(self):
        """Test endpoint matching logic"""
        # Exact match
        api_call = {'endpoint': '/api/users', 'method': 'GET'}
        endpoint = {'endpoint': '/api/users', 'method': 'GET'}
        self.assertTrue(self.validator._endpoints_match(api_call, endpoint))
        
        # Different methods
        api_call = {'endpoint': '/api/users', 'method': 'POST'}
        endpoint = {'endpoint': '/api/users', 'method': 'GET'}
        self.assertFalse(self.validator._endpoints_match(api_call, endpoint))
        
        # Path parameters
        api_call = {'endpoint': '/api/users/123', 'method': 'GET'}
        endpoint = {'endpoint': '/api/users/[id]', 'method': 'GET'}
        self.assertTrue(self.validator._endpoints_match(api_call, endpoint))
    
    def test_find_similar_fields(self):
        """Test finding similar field names"""
        columns = {
            'user_id': {'type': 'int'},
            'user_name': {'type': 'varchar'},
            'email_address': {'type': 'varchar'},
            'created_at': {'type': 'timestamp'}
        }
        
        # Case insensitive match
        similar = self.validator._find_similar_fields('USER_ID', columns)
        self.assertEqual(similar, 'user_id')
        
        # Partial match
        similar = self.validator._find_similar_fields('email', columns)
        self.assertEqual(similar, 'email_address')
        
        # No match
        similar = self.validator._find_similar_fields('phone', columns)
        self.assertIsNone(similar)
    
    def test_check_circular_dependencies(self):
        """Test circular dependency detection"""
        dependencies = [
            {'name': 'ComponentB', 'type': 'component', 'path': './ComponentB'},
            {'name': 'ComponentC', 'type': 'component', 'path': './ComponentC'}
        ]
        
        # Currently returns None as not implemented
        result = self.validator._check_circular_dependencies('ComponentA', dependencies)
        self.assertIsNone(result)
    
    def test_extract_functions(self):
        """Test function extraction from code"""
        code = '''
        export async function getUserById(id) {
            return await db.users.findById(id);
        }
        
        function calculateDiscount(price, percentage) {
            return price * (1 - percentage / 100);
        }
        
        export const formatPrice = (price) => {
            return `$${price.toFixed(2)}`;
        };
        
        const helper = function() { return true; };
        '''
        
        functions = self.validator._extract_functions(code)
        
        self.assertIn('getUserById', functions)
        self.assertIn('calculateDiscount', functions)
        self.assertIn('formatPrice', functions)
    
    def test_extract_tested_functions(self):
        """Test extraction of tested functions from test code"""
        test_code = '''
        describe('User utilities', () => {
            it('getUserById returns correct user', async () => {
                const user = await getUserById(1);
                expect(user.id).toBe(1);
            });
            
            test('calculateDiscount applies percentage correctly', () => {
                expect(calculateDiscount(100, 20)).toBe(80);
            });
            
            it('should format price with dollar sign', () => {
                expect(formatPrice(99.99)).toBe('$99.99');
            });
        });
        '''
        
        tested = self.validator._extract_tested_functions(test_code)
        
        # Function names are extracted from test descriptions
        self.assertTrue(any('returns' in t for t in tested))  # from 'returns correct user'
        self.assertTrue(any('applies' in t for t in tested))  # from 'applies percentage'
    
    def test_component_exists(self):
        """Test checking if component exists"""
        # Create a component file
        comp_dir = os.path.join(self.temp_dir, 'components')
        os.makedirs(comp_dir, exist_ok=True)
        
        with open(os.path.join(comp_dir, 'Button.tsx'), 'w') as f:
            f.write('export const Button = () => {}')
        
        # Should find Button component
        self.assertTrue(self.validator._component_exists('Button'))
        
        # Should not find non-existent component
        self.assertFalse(self.validator._component_exists('NonExistent'))
    
    def test_load_database_schemas(self):
        """Test loading database schemas from migrations"""
        # Create migrations directory
        migrations_dir = os.path.join(self.temp_dir, 'supabase', 'migrations')
        os.makedirs(migrations_dir, exist_ok=True)
        
        # Create a migration file
        with open(os.path.join(migrations_dir, '001_create_users.sql'), 'w') as f:
            f.write('''
            CREATE TABLE users (
                id SERIAL PRIMARY KEY,
                email VARCHAR(255) UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            ''')
        
        self.validator._load_database_schemas()
        
        self.assertIn('users', self.validator.database_schemas)
        self.assertIn('email', self.validator.database_schemas['users']['columns'])
        self.assertTrue(self.validator.database_schemas['users']['columns']['email']['required'])
    
    def test_extract_database_queries(self):
        """Test extraction of database queries from code"""
        code = '''
        // Get all users
        const users = await supabase.from('users').select('id, email, name');
        
        // Get specific fields
        const profiles = await supabase.from('profiles').select('avatar_url');
        
        // Insert data
        await supabase.from('posts').insert({ title: 'New Post' });
        '''
        
        queries = self.validator._extract_database_queries(code)
        
        self.assertGreaterEqual(len(queries), 2)  # At least 2 queries extracted
        self.assertEqual(queries[0]['table'], 'users')
        self.assertIn('email', queries[0]['fields'])
        self.assertEqual(queries[1]['table'], 'profiles')
    
    def test_parse_sql_schema(self):
        """Test SQL schema parsing"""
        sql = '''
        CREATE TABLE IF NOT EXISTS products (
            id SERIAL PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            price DECIMAL(10,2),
            active BOOLEAN DEFAULT true
        );
        
        CREATE TABLE orders (
            id INT PRIMARY KEY,
            product_id INT NOT NULL
        );
        '''
        
        self.validator._parse_sql_schema(sql)
        
        self.assertIn('products', self.validator.database_schemas)
        self.assertIn('orders', self.validator.database_schemas)
        
        # Check products schema
        products_cols = self.validator.database_schemas['products']['columns']
        self.assertIn('name', products_cols)
        self.assertTrue(products_cols['name']['required'])
        self.assertIn('price', products_cols)
        self.assertFalse(products_cols['price']['required'])  # No NOT NULL
    
    def test_validate_frontend_backend_contract_unused_endpoints(self):
        """Test detection of unused backend endpoints"""
        frontend_code = 'fetch("/api/users", { method: "GET" })'
        backend_code = '''
        router.get("/api/users", (req, res) => res.json([]));
        router.post("/api/products", (req, res) => res.json({}));
        '''
        
        result = self.validator.validate_frontend_backend_contract(frontend_code, backend_code)
        
        self.assertTrue(result.is_valid)
        self.assertGreater(len(result.warnings), 0)
        self.assertTrue(any('products' in w for w in result.warnings))
    
    def test_validate_database_schema_missing_required_insert_fields(self):
        """Test validation with missing required fields in insert"""
        self.validator.database_schemas = {
            'users': {
                'columns': {
                    'id': {'type': 'SERIAL', 'required': True},
                    'email': {'type': 'VARCHAR', 'required': True},
                    'name': {'type': 'VARCHAR', 'required': False}
                }
            }
        }
        
        with patch.object(self.validator, '_extract_database_queries') as mock_extract:
            mock_extract.return_value = [{
                'table': 'users',
                'fields': ['name'],  # Missing required 'email'
                'type': 'insert'
            }]
            
            result = self.validator.validate_database_schema_usage('code', 'insert')
        
        self.assertFalse(result.is_valid)
        self.assertTrue(any('Missing required fields' in error for error in result.errors))
    
    def test_validate_security_compliance_comprehensive(self):
        """Test comprehensive security validation"""
        code = '''
        const apiKey = "sk-12345";
        console.log("Debug:", apiKey);
        eval(userInput);
        element.innerHTML = userData;
        '''
        
        result = self.validator.validate_security_compliance(code, 'frontend')
        
        self.assertFalse(result.is_valid)
        self.assertGreater(len(result.errors), 0)
        self.assertGreater(len(result.warnings), 0)
    
    def test_hook_and_util_existence_checks(self):
        """Test hook and utility existence checks"""
        # Create hooks and utils directories
        hooks_dir = os.path.join(self.temp_dir, 'hooks')
        utils_dir = os.path.join(self.temp_dir, 'utils')
        os.makedirs(hooks_dir, exist_ok=True)
        os.makedirs(utils_dir, exist_ok=True)
        
        with open(os.path.join(hooks_dir, 'useAuth.ts'), 'w') as f:
            f.write('export const useAuth = () => {};')
        
        with open(os.path.join(utils_dir, 'dateUtils.js'), 'w') as f:
            f.write('export const formatDate = () => {};')
        
        self.assertTrue(self.validator._hook_exists('useAuth'))
        self.assertTrue(self.validator._util_exists('dateUtils'))
        self.assertFalse(self.validator._hook_exists('nonExistent'))
        self.assertFalse(self.validator._util_exists('nonExistent'))
    
    def test_endpoints_match_edge_cases(self):
        """Test endpoint matching edge cases"""
        # Trailing slashes
        api_call = {'endpoint': '/api/users/', 'method': 'GET'}
        endpoint = {'endpoint': '/api/users', 'method': 'GET'}
        self.assertTrue(self.validator._endpoints_match(api_call, endpoint))
        
        # Different path lengths
        api_call = {'endpoint': '/api/users', 'method': 'GET'}
        endpoint = {'endpoint': '/api/users/profile', 'method': 'GET'}
        self.assertFalse(self.validator._endpoints_match(api_call, endpoint))
        
        # Path parameters
        api_call = {'endpoint': '/api/users/123/posts/456', 'method': 'GET'}
        endpoint = {'endpoint': '/api/users/[id]/posts/[postId]', 'method': 'GET'}
        self.assertTrue(self.validator._endpoints_match(api_call, endpoint))
    
    def test_validate_test_coverage_edge_cases(self):
        """Test test coverage validation edge cases"""
        # Missing describe block
        component_code = 'export const add = (a, b) => a + b;'
        test_code = 'it("should work", () => {});'
        
        result = self.validator.validate_test_coverage(component_code, test_code)
        self.assertFalse(result.is_valid)
        self.assertTrue(any("describe" in error for error in result.errors))
        
        # Missing test cases
        test_code_no_tests = 'describe("Math", () => { /* no tests */ });'
        result = self.validator.validate_test_coverage(component_code, test_code_no_tests)
        self.assertFalse(result.is_valid)
        self.assertTrue(any("test cases" in error for error in result.errors))


if __name__ == '__main__':
    import unittest
    unittest.main()