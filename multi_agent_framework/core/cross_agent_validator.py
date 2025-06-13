import os
import re
import json
import ast
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass

@dataclass
class ValidationResult:
    """Result of cross-agent validation."""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    suggestions: List[str]

@dataclass
class APIContract:
    """Represents an API contract between frontend and backend."""
    endpoint: str
    method: str
    request_schema: Dict[str, Any]
    response_schema: Dict[str, Any]
    auth_required: bool

class CrossAgentValidator:
    """
    Validates outputs across different agents to ensure compatibility
    and consistency throughout the codebase.
    """
    
    def __init__(self, project_root: str):
        self.project_root = project_root
        self.api_contracts = {}
        self.component_dependencies = {}
        self.database_schemas = {}
        
    def validate_frontend_backend_contract(self, frontend_code: str, 
                                         backend_code: str) -> ValidationResult:
        """Validate that frontend API calls match backend endpoints."""
        errors = []
        warnings = []
        suggestions = []
        
        # Extract API calls from frontend
        frontend_apis = self._extract_frontend_api_calls(frontend_code)
        
        # Extract API endpoints from backend
        backend_endpoints = self._extract_backend_endpoints(backend_code)
        
        # Validate each frontend call has matching backend endpoint
        for api_call in frontend_apis:
            endpoint_match = False
            for endpoint in backend_endpoints:
                if self._endpoints_match(api_call, endpoint):
                    endpoint_match = True
                    # Validate request/response schemas
                    schema_errors = self._validate_schemas(api_call, endpoint)
                    errors.extend(schema_errors)
                    break
                    
            if not endpoint_match:
                errors.append(f"Frontend calls API '{api_call['endpoint']}' but no matching backend endpoint found")
                suggestions.append(f"Create backend endpoint: {api_call['method']} {api_call['endpoint']}")
        
        # Check for unused backend endpoints
        for endpoint in backend_endpoints:
            used = False
            for api_call in frontend_apis:
                if self._endpoints_match(api_call, endpoint):
                    used = True
                    break
            if not used:
                warnings.append(f"Backend endpoint '{endpoint['method']} {endpoint['endpoint']}' is not used by frontend")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            suggestions=suggestions
        )
    
    def validate_database_schema_usage(self, code: str, schema_type: str) -> ValidationResult:
        """Validate that code uses database schema correctly."""
        errors = []
        warnings = []
        suggestions = []
        
        # Load known database schemas
        self._load_database_schemas()
        
        # Extract database queries from code
        queries = self._extract_database_queries(code)
        
        for query in queries:
            table_name = query.get('table')
            if table_name in self.database_schemas:
                schema = self.database_schemas[table_name]
                
                # Validate field usage
                for field in query.get('fields', []):
                    if field not in schema['columns']:
                        errors.append(f"Field '{field}' does not exist in table '{table_name}'")
                        # Suggest similar fields
                        similar = self._find_similar_fields(field, schema['columns'])
                        if similar:
                            suggestions.append(f"Did you mean '{similar}'?")
                
                # Check for required fields in inserts
                if query.get('type') == 'insert':
                    missing_required = []
                    for col, info in schema['columns'].items():
                        if info.get('required') and col not in query.get('fields', []):
                            missing_required.append(col)
                    if missing_required:
                        errors.append(f"Missing required fields for {table_name}: {', '.join(missing_required)}")
            else:
                warnings.append(f"Unknown table '{table_name}' referenced in query")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            suggestions=suggestions
        )
    
    def validate_component_dependencies(self, component_code: str, 
                                      component_name: str) -> ValidationResult:
        """Validate that component dependencies are satisfied."""
        errors = []
        warnings = []
        suggestions = []
        
        # Extract imports and dependencies
        dependencies = self._extract_dependencies(component_code)
        
        for dep in dependencies:
            if dep['type'] == 'component':
                # Check if component exists
                if not self._component_exists(dep['name']):
                    errors.append(f"Component '{dep['name']}' imported but not found")
                    suggestions.append(f"Create component '{dep['name']}' or check import path")
                    
            elif dep['type'] == 'hook':
                # Validate hook usage
                if not self._hook_exists(dep['name']):
                    errors.append(f"Hook '{dep['name']}' imported but not found")
                    
            elif dep['type'] == 'util':
                # Validate utility function
                if not self._util_exists(dep['name']):
                    warnings.append(f"Utility '{dep['name']}' imported but not found")
        
        # Check for circular dependencies
        circular = self._check_circular_dependencies(component_name, dependencies)
        if circular:
            errors.append(f"Circular dependency detected: {' -> '.join(circular)}")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            suggestions=suggestions
        )
    
    def validate_test_coverage(self, component_code: str, test_code: str) -> ValidationResult:
        """Validate that tests cover component functionality."""
        errors = []
        warnings = []
        suggestions = []
        
        # Extract component functions/methods
        component_functions = self._extract_functions(component_code)
        
        # Extract tested functions
        tested_functions = self._extract_tested_functions(test_code)
        
        # Check coverage
        untested = []
        for func in component_functions:
            if func not in tested_functions:
                untested.append(func)
                
        if untested:
            warnings.append(f"Functions not covered by tests: {', '.join(untested)}")
            for func in untested:
                suggestions.append(f"Add test case for '{func}' function")
        
        # Validate test structure
        if not re.search(r'describe\s*\(', test_code):
            errors.append("Test file missing 'describe' block")
            
        if not re.search(r'(?:it|test)\s*\(', test_code):
            errors.append("Test file missing test cases")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            suggestions=suggestions
        )
    
    def validate_security_compliance(self, code: str, code_type: str) -> ValidationResult:
        """Validate security best practices."""
        errors = []
        warnings = []
        suggestions = []
        
        # Check for common security issues
        security_patterns = {
            'sql_injection': r'query\s*\(\s*[\'"`].*\$\{.*\}.*[\'"`]',
            'xss': r'dangerouslySetInnerHTML|innerHTML\s*=',
            'hardcoded_secrets': r'(api_key|secret|password|token)\s*=\s*[\'"`][^\'"`]+[\'"`]',
            'console_log': r'console\.(log|error|warn)',
            'eval_usage': r'\beval\s*\(',
        }
        
        for issue, pattern in security_patterns.items():
            if re.search(pattern, code, re.IGNORECASE):
                if issue == 'console_log':
                    warnings.append("Remove console.log statements before production")
                elif issue == 'hardcoded_secrets':
                    errors.append("Hardcoded secrets detected - use environment variables")
                    suggestions.append("Move secrets to .env file and use process.env")
                elif issue == 'sql_injection':
                    errors.append("Potential SQL injection vulnerability")
                    suggestions.append("Use parameterized queries or prepared statements")
                elif issue == 'xss':
                    warnings.append("Potential XSS vulnerability with innerHTML")
                    suggestions.append("Sanitize user input or use safe alternatives")
                elif issue == 'eval_usage':
                    errors.append("Avoid using eval() - it's a security risk")
        
        # Check authentication on API routes
        if code_type == 'api' and 'export' in code:
            if not re.search(r'(getUser|requireAuth|authenticate|getSession)', code):
                warnings.append("API route may be missing authentication check")
                suggestions.append("Add authentication middleware to protect this endpoint")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            suggestions=suggestions
        )
    
    def _extract_frontend_api_calls(self, code: str) -> List[Dict]:
        """Extract API calls from frontend code."""
        api_calls = []
        
        # Look for fetch calls
        fetch_pattern = r'fetch\s*\(\s*[\'"`]([^\'"`]+)[\'"`].*?method\s*:\s*[\'"`](\w+)[\'"`]'
        for match in re.finditer(fetch_pattern, code, re.DOTALL):
            api_calls.append({
                'endpoint': match.group(1),
                'method': match.group(2).upper()
            })
        
        # Look for axios calls
        axios_patterns = [
            r'axios\.(\w+)\s*\(\s*[\'"`]([^\'"`]+)[\'"`]',
            r'axios\s*\(\s*\{\s*url\s*:\s*[\'"`]([^\'"`]+)[\'"`].*?method\s*:\s*[\'"`](\w+)[\'"`]'
        ]
        
        for pattern in axios_patterns:
            for match in re.finditer(pattern, code, re.DOTALL):
                if len(match.groups()) == 2:
                    api_calls.append({
                        'endpoint': match.group(2) if pattern == axios_patterns[0] else match.group(1),
                        'method': match.group(1).upper() if pattern == axios_patterns[0] else match.group(2).upper()
                    })
        
        return api_calls
    
    def _extract_backend_endpoints(self, code: str) -> List[Dict]:
        """Extract API endpoints from backend code."""
        endpoints = []
        
        # Next.js API routes
        methods = ['GET', 'POST', 'PUT', 'DELETE', 'PATCH']
        for method in methods:
            if f'export async function {method}' in code or f'export function {method}' in code:
                # Extract route from file path or comments
                route_match = re.search(r'//\s*route:\s*([^\n]+)', code)
                if route_match:
                    endpoints.append({
                        'endpoint': route_match.group(1).strip(),
                        'method': method
                    })
        
        # Express-style routes
        express_pattern = r'router\.(\w+)\s*\(\s*[\'"`]([^\'"`]+)[\'"`]'
        for match in re.finditer(express_pattern, code):
            endpoints.append({
                'endpoint': match.group(2),
                'method': match.group(1).upper()
            })
        
        return endpoints
    
    def _endpoints_match(self, api_call: Dict, endpoint: Dict) -> bool:
        """Check if frontend API call matches backend endpoint."""
        # Normalize paths
        call_path = api_call['endpoint'].rstrip('/')
        endpoint_path = endpoint['endpoint'].rstrip('/')
        
        # Check method match
        if api_call['method'] != endpoint['method']:
            return False
        
        # Check path match (handle parameters)
        call_parts = call_path.split('/')
        endpoint_parts = endpoint_path.split('/')
        
        if len(call_parts) != len(endpoint_parts):
            return False
        
        for i, (call_part, endpoint_part) in enumerate(zip(call_parts, endpoint_parts)):
            # Handle path parameters
            if endpoint_part.startswith('[') and endpoint_part.endswith(']'):
                continue  # Parameter matches any value
            elif call_part != endpoint_part:
                return False
        
        return True
    
    def _validate_schemas(self, api_call: Dict, endpoint: Dict) -> List[str]:
        """Validate request/response schemas between frontend and backend."""
        errors = []
        # This would require more sophisticated parsing of request/response types
        # For now, return empty list
        return errors
    
    def _load_database_schemas(self):
        """Load database schemas from migrations."""
        migrations_dir = os.path.join(self.project_root, 'supabase', 'migrations')
        if not os.path.exists(migrations_dir):
            return
        
        for file in os.listdir(migrations_dir):
            if file.endswith('.sql'):
                filepath = os.path.join(migrations_dir, file)
                with open(filepath, 'r') as f:
                    content = f.read()
                    self._parse_sql_schema(content)
    
    def _parse_sql_schema(self, sql: str):
        """Parse SQL to extract table schemas."""
        # Simple regex-based parsing
        create_table_pattern = r'CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?["`]?(\w+)["`]?\s*\((.*?)\);'
        
        for match in re.finditer(create_table_pattern, sql, re.DOTALL | re.IGNORECASE):
            table_name = match.group(1)
            columns_str = match.group(2)
            
            columns = {}
            column_pattern = r'["`]?(\w+)["`]?\s+(\w+)(?:\([^)]+\))?([^,]*)'
            
            for col_match in re.finditer(column_pattern, columns_str):
                col_name = col_match.group(1)
                col_type = col_match.group(2)
                constraints = col_match.group(3) or ''
                
                columns[col_name] = {
                    'type': col_type,
                    'required': 'NOT NULL' in constraints.upper()
                }
            
            self.database_schemas[table_name] = {'columns': columns}
    
    def _extract_database_queries(self, code: str) -> List[Dict]:
        """Extract database queries from code."""
        queries = []
        
        # Supabase queries
        supabase_pattern = r'supabase\s*\.\s*from\s*\(\s*[\'"`](\w+)[\'"`]\s*\)'
        for match in re.finditer(supabase_pattern, code):
            table_name = match.group(1)
            
            # Look for select fields
            select_match = re.search(r'\.select\s*\(\s*[\'"`]([^\'"`]+)[\'"`]', code[match.end():match.end()+200])
            fields = []
            if select_match:
                fields = [f.strip() for f in select_match.group(1).split(',')]
            
            queries.append({
                'table': table_name,
                'fields': fields,
                'type': 'select'
            })
        
        return queries
    
    def _find_similar_fields(self, field: str, columns: Dict) -> Optional[str]:
        """Find similar field names using edit distance."""
        field_lower = field.lower()
        for col in columns:
            if field_lower == col.lower():
                return col
            # Simple similarity check
            if field_lower in col.lower() or col.lower() in field_lower:
                return col
        return None
    
    def _extract_dependencies(self, code: str) -> List[Dict]:
        """Extract component dependencies from imports."""
        dependencies = []
        
        # ES6 imports
        import_pattern = r'import\s+(?:\{([^}]+)\}|(\w+))\s+from\s+[\'"`]([^\'"`]+)[\'"`]'
        for match in re.finditer(import_pattern, code):
            imports = match.group(1) or match.group(2)
            path = match.group(3)
            
            # Determine dependency type
            dep_type = 'module'
            if path.startswith('./') or path.startswith('../'):
                if 'component' in path.lower():
                    dep_type = 'component'
                elif 'hook' in path.lower():
                    dep_type = 'hook'
                elif 'util' in path.lower() or 'helper' in path.lower():
                    dep_type = 'util'
            
            for imp in imports.split(','):
                dependencies.append({
                    'name': imp.strip(),
                    'type': dep_type,
                    'path': path
                })
        
        return dependencies
    
    def _component_exists(self, name: str) -> bool:
        """Check if component exists in project."""
        # Simple file existence check
        component_dirs = ['components', 'app']
        for dir in component_dirs:
            dir_path = os.path.join(self.project_root, dir)
            if os.path.exists(dir_path):
                for root, dirs, files in os.walk(dir_path):
                    for file in files:
                        if name in file:
                            return True
        return False
    
    def _hook_exists(self, name: str) -> bool:
        """Check if hook exists."""
        hooks_dir = os.path.join(self.project_root, 'hooks')
        if os.path.exists(hooks_dir):
            for file in os.listdir(hooks_dir):
                if name in file:
                    return True
        return False
    
    def _util_exists(self, name: str) -> bool:
        """Check if utility exists."""
        util_dirs = ['lib', 'utils', 'helpers']
        for dir in util_dirs:
            dir_path = os.path.join(self.project_root, dir)
            if os.path.exists(dir_path):
                for file in os.listdir(dir_path):
                    if name in file:
                        return True
        return False
    
    def _check_circular_dependencies(self, component: str, 
                                   dependencies: List[Dict]) -> Optional[List[str]]:
        """Check for circular dependencies."""
        # This would require building a full dependency graph
        # For now, return None
        return None
    
    def _extract_functions(self, code: str) -> List[str]:
        """Extract function names from code."""
        functions = []
        
        # Function declarations
        func_pattern = r'(?:export\s+)?(?:async\s+)?function\s+(\w+)'
        functions.extend(re.findall(func_pattern, code))
        
        # Arrow functions
        arrow_pattern = r'(?:export\s+)?const\s+(\w+)\s*='
        functions.extend(re.findall(arrow_pattern, code))
        
        return functions
    
    def _extract_tested_functions(self, test_code: str) -> List[str]:
        """Extract functions being tested."""
        tested = []
        
        # Look in describe/it blocks
        test_pattern = r'(?:describe|it|test)\s*\(\s*[\'"`]([^\'"`]+)[\'"`]'
        for match in re.finditer(test_pattern, test_code):
            desc = match.group(1)
            # Extract function names from descriptions
            words = desc.split()
            for word in words:
                if word[0].islower() and len(word) > 3:
                    tested.append(word)
        
        return tested