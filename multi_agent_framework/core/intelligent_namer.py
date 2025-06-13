import re
import ast
from typing import Optional, Dict, List, Tuple

class IntelligentNamer:
    """
    Provides intelligent naming capabilities for generated code components.
    Extracts meaningful names from code content and handles naming conflicts.
    """
    
    def __init__(self, project_root: str):
        self.project_root = project_root
        self.reserved_keywords = {
            'class', 'function', 'const', 'let', 'var', 'export', 'import',
            'default', 'return', 'if', 'else', 'for', 'while', 'do', 'switch',
            'case', 'break', 'continue', 'try', 'catch', 'finally', 'throw'
        }
        
    def extract_component_name(self, content: str, file_type: str = 'component') -> Optional[str]:
        """
        Extract a meaningful component name from code content.
        Handles React components, API routes, database schemas, etc.
        """
        # Remove comments to avoid false matches
        content = self._remove_comments(content)
        
        # Try different extraction strategies based on file type
        if file_type in ['component', 'frontend']:
            name = self._extract_react_component_name(content)
        elif file_type in ['api', 'backend']:
            name = self._extract_api_endpoint_name(content)
        elif file_type in ['database', 'migration']:
            name = self._extract_database_entity_name(content)
        elif file_type == 'test':
            name = self._extract_test_suite_name(content)
        else:
            name = self._extract_generic_name(content)
            
        # Clean and validate the extracted name
        if name:
            name = self._clean_name(name)
            if self._is_valid_name(name):
                return name
                
        return None
    
    def _extract_react_component_name(self, content: str) -> Optional[str]:
        """Extract React component name from JSX/TSX content."""
        patterns = [
            # Function component: export default function ComponentName
            r'export\s+default\s+function\s+(\w+)',
            # Function component: function ComponentName
            r'function\s+(\w+)\s*\([^)]*\)\s*(?::\s*\w+)?\s*\{',
            # Arrow function: const ComponentName = 
            r'(?:export\s+)?const\s+(\w+)\s*=\s*\([^)]*\)\s*=>', 
            # Class component: class ComponentName extends
            r'class\s+(\w+)\s+extends\s+(?:React\.)?Component',
            # Component with explicit type
            r'const\s+(\w+)\s*:\s*(?:React\.)?(?:FC|FunctionComponent)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, content)
            if match:
                return match.group(1)
                
        # Try to extract from JSX usage
        jsx_match = re.search(r'<(\w+)[\s/>]', content)
        if jsx_match and jsx_match.group(1)[0].isupper():
            return jsx_match.group(1)
            
        return None
    
    def _extract_api_endpoint_name(self, content: str) -> Optional[str]:
        """Extract API endpoint name from route content."""
        # Look for route patterns
        patterns = [
            r'route\s*:\s*[\'"]([^\'"\s]+)[\'"]',
            r'path\s*:\s*[\'"]([^\'"\s]+)[\'"]',
            r'endpoint\s*:\s*[\'"]([^\'"\s]+)[\'"]',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, content)
            if match:
                # Convert route to PascalCase name
                route = match.group(1)
                parts = route.strip('/').split('/')
                return ''.join(part.capitalize() for part in parts) + 'Route'
                
        # Extract from function names
        func_patterns = [
            r'export\s+async\s+function\s+(GET|POST|PUT|DELETE|PATCH)',
            r'export\s+function\s+(\w+)Handler',
        ]
        
        for pattern in func_patterns:
            match = re.search(pattern, content)
            if match:
                return match.group(1).capitalize() + 'Handler'
                
        return None
    
    def _extract_database_entity_name(self, content: str) -> Optional[str]:
        """Extract database entity name from migration or schema content."""
        patterns = [
            r'CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?[`"]?(\w+)[`"]?',
            r'ALTER\s+TABLE\s+[`"]?(\w+)[`"]?',
            r'model\s+(\w+)\s*{',  # Prisma schema
            r'Table\([\'"](\w+)[\'"]\)',  # SQLAlchemy
        ]
        
        for pattern in patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                table_name = match.group(1)
                # Convert snake_case to PascalCase
                parts = table_name.split('_')
                return ''.join(part.capitalize() for part in parts) + 'Migration'
                
        return None
    
    def _extract_test_suite_name(self, content: str) -> Optional[str]:
        """Extract test suite name from test file content."""
        patterns = [
            r'describe\s*\([\'"]([^\'"\)]+)[\'"]',
            r'test\s*\([\'"]([^\'"\)]+)[\'"]',
            r'it\s*\([\'"]([^\'"\)]+)[\'"]',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, content)
            if match:
                desc = match.group(1)
                # Clean up the description
                words = re.findall(r'\w+', desc)
                if words:
                    return ''.join(word.capitalize() for word in words[:3]) + 'Test'
                    
        return None
    
    def _extract_generic_name(self, content: str) -> Optional[str]:
        """Generic name extraction for any code type."""
        # Look for class/function definitions
        patterns = [
            r'class\s+(\w+)',
            r'function\s+(\w+)',
            r'const\s+(\w+)\s*=',
            r'let\s+(\w+)\s*=',
            r'var\s+(\w+)\s*=',
            r'interface\s+(\w+)',
            r'type\s+(\w+)\s*=',
            r'enum\s+(\w+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, content)
            if match:
                name = match.group(1)
                if name[0].isupper() and len(name) > 3:
                    return name
                    
        return None
    
    def _remove_comments(self, content: str) -> str:
        """Remove comments from code to avoid false matches."""
        # Remove single-line comments
        content = re.sub(r'//.*$', '', content, flags=re.MULTILINE)
        # Remove multi-line comments
        content = re.sub(r'/\*.*?\*/', '', content, flags=re.DOTALL)
        # Remove Python-style comments
        content = re.sub(r'#.*$', '', content, flags=re.MULTILINE)
        return content
    
    def _clean_name(self, name: str) -> str:
        """Clean and normalize extracted name."""
        # Remove common prefixes/suffixes
        prefixes = ['get', 'set', 'use', 'with', 'handle']
        suffixes = ['Component', 'Handler', 'Route', 'Test', 'Spec']
        
        name_lower = name.lower()
        for prefix in prefixes:
            if name_lower.startswith(prefix.lower()) and len(name) > len(prefix):
                name = name[len(prefix):]
                break
                
        # Ensure first letter is uppercase for component names
        if name and not name[0].isupper():
            name = name[0].upper() + name[1:]
            
        return name
    
    def _is_valid_name(self, name: str) -> bool:
        """Check if the extracted name is valid."""
        if not name or len(name) < 3:
            return False
            
        if name.lower() in self.reserved_keywords:
            return False
            
        # Must start with letter and contain only alphanumeric
        if not re.match(r'^[A-Za-z]\w*$', name):
            return False
            
        # Avoid too generic names
        generic_names = {'Component', 'Function', 'Handler', 'Route', 'Test', 'App', 'Main'}
        if name in generic_names:
            return False
            
        return True
    
    def generate_unique_name(self, base_name: str, existing_names: List[str], 
                           task_context: str = '') -> str:
        """
        Generate a unique name based on the base name and context.
        Handles conflicts with existing names.
        """
        if not base_name:
            # Generate from task context if no base name
            base_name = self._generate_from_context(task_context)
            
        # Check if base name is unique
        if base_name not in existing_names:
            return base_name
            
        # Try adding descriptive suffixes based on context
        context_words = re.findall(r'\w+', task_context.lower())
        descriptive_suffixes = []
        
        for word in context_words:
            if word not in ['the', 'a', 'an', 'and', 'or', 'but', 'for', 'with']:
                descriptive_suffixes.append(word.capitalize())
                
        # Try descriptive suffixes first
        for suffix in descriptive_suffixes[:3]:
            candidate = f"{base_name}{suffix}"
            if candidate not in existing_names:
                return candidate
                
        # Fall back to numeric suffixes
        counter = 2
        while True:
            candidate = f"{base_name}{counter}"
            if candidate not in existing_names:
                return candidate
            counter += 1
    
    def _generate_from_context(self, task_context: str) -> str:
        """Generate a name from task context when no code name is found."""
        # Extract key words from context
        words = re.findall(r'\b[A-Za-z]{4,}\b', task_context)
        
        # Filter out common words
        stop_words = {
            'create', 'implement', 'build', 'make', 'develop', 'design',
            'component', 'function', 'feature', 'system', 'module',
            'that', 'this', 'with', 'from', 'into', 'about'
        }
        
        meaningful_words = [w for w in words if w.lower() not in stop_words]
        
        if meaningful_words:
            # Take first 2-3 meaningful words
            name_parts = meaningful_words[:min(3, len(meaningful_words))]
            return ''.join(word.capitalize() for word in name_parts)
            
        # Fallback to generic name
        return 'Generated'
    
    def suggest_filename(self, component_name: str, file_type: str) -> str:
        """
        Suggest an appropriate filename based on component name and type.
        """
        # Convert PascalCase to appropriate case for filename
        if file_type in ['component', 'frontend']:
            # Keep PascalCase for React components
            return f"{component_name}.tsx"
        elif file_type in ['api', 'backend']:
            # Use kebab-case for API routes
            kebab = re.sub(r'(?<!^)(?=[A-Z])', '-', component_name).lower()
            return f"{kebab}.ts"
        elif file_type in ['database', 'migration']:
            # Use snake_case for database files
            snake = re.sub(r'(?<!^)(?=[A-Z])', '_', component_name).lower()
            return f"{snake}.sql"
        elif file_type == 'test':
            # Use PascalCase with .test suffix
            return f"{component_name}.test.tsx"
        else:
            # Default to PascalCase with .ts extension
            return f"{component_name}.ts"