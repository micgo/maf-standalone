"""
Naming Convention System for Multi-Agent Framework
Ensures consistent file naming and placement across all agents
"""

import os
import re
from typing import Dict, Optional, Tuple


class NamingConventions:
    """Centralized naming conventions for all agents to follow"""
    
    # File extension mappings
    EXTENSIONS = {
        'api_route': '.ts',
        'component': '.tsx',
        'service': '.ts',
        'test': '.test.tsx',
        'migration': '.sql',
        'documentation': '.md',
        'config': '.json',
        'types': '.ts'
    }
    
    # Directory structure mappings
    DIRECTORIES = {
        'api_route': 'app/api/{resource}/route.ts',
        'component': 'components/{category}/{name}.tsx',
        'page': 'app/{path}/page.tsx',
        'service': 'lib/{name}Service.ts',
        'test': '{original_path}/{name}.test.tsx',
        'migration': 'supabase/migrations/{timestamp}_{name}.sql',
        'documentation': 'project-plan/{category}/{name}.md',
        'types': 'types/{name}.ts',
        'ui_component': 'components/ui/{name}.tsx'
    }
    
    @staticmethod
    def generate_api_route_path(resource: str) -> str:
        """Generate proper path for API routes"""
        resource = resource.lower().replace(' ', '-')
        return f"app/api/{resource}/route.ts"
    
    @staticmethod
    def generate_component_path(name: str, category: str = None) -> str:
        """Generate proper path for components"""
        name = NamingConventions._to_pascal_case(name)
        category = category or 'common'
        return f"components/{category}/{name}.tsx"
    
    @staticmethod
    def generate_service_path(name: str) -> str:
        """Generate proper path for service files"""
        name = NamingConventions._to_camel_case(name)
        return f"lib/{name}Service.ts"
    
    @staticmethod
    def generate_page_path(path: str) -> str:
        """Generate proper path for Next.js pages"""
        path = path.lower().strip('/').replace(' ', '-')
        return f"app/{path}/page.tsx"
    
    @staticmethod
    def generate_migration_name(description: str) -> str:
        """Generate proper migration filename"""
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        description = description.lower().replace(' ', '_')
        # Remove special characters
        description = re.sub(r'[^a-z0-9_]', '', description)
        return f"{timestamp}_{description}.sql"
    
    @staticmethod
    def validate_file_path(file_path: str, file_type: str) -> Tuple[bool, Optional[str]]:
        """Validate if a file path follows conventions"""
        if file_type == 'api_route':
            pattern = r'^app/api/[a-z-]+/route\.ts$'
            if not re.match(pattern, file_path):
                return False, "API routes must be at app/api/{resource}/route.ts"
        
        elif file_type == 'component':
            pattern = r'^components/[a-z-]+/[A-Z][a-zA-Z]+\.tsx$'
            if not re.match(pattern, file_path):
                return False, "Components must be at components/{category}/{PascalCaseName}.tsx"
        
        elif file_type == 'service':
            pattern = r'^lib/[a-z][a-zA-Z]+Service\.ts$'
            if not re.match(pattern, file_path):
                return False, "Services must be at lib/{camelCaseName}Service.ts"
        
        return True, None
    
    @staticmethod
    def extract_resource_from_task(task_description: str) -> Dict[str, str]:
        """Extract resource information from task description"""
        resources = {}
        
        # Extract resource names (e.g., "photos", "documents", "events")
        if 'photo' in task_description.lower():
            resources['resource'] = 'photos'
            resources['category'] = 'gallery'
        elif 'document' in task_description.lower():
            resources['resource'] = 'documents'
            resources['category'] = 'documents'
        elif 'event' in task_description.lower():
            resources['resource'] = 'events'
            resources['category'] = 'events'
        elif 'user' in task_description.lower():
            resources['resource'] = 'users'
            resources['category'] = 'auth'
        
        return resources
    
    @staticmethod
    def _to_pascal_case(text: str) -> str:
        """Convert text to PascalCase"""
        words = re.sub(r'[^a-zA-Z0-9\s]', '', text).split()
        return ''.join(word.capitalize() for word in words)
    
    @staticmethod
    def _to_camel_case(text: str) -> str:
        """Convert text to camelCase"""
        pascal = NamingConventions._to_pascal_case(text)
        return pascal[0].lower() + pascal[1:] if pascal else ''
    
    @staticmethod
    def _to_kebab_case(text: str) -> str:
        """Convert text to kebab-case"""
        words = re.sub(r'[^a-zA-Z0-9\s]', '', text).split()
        return '-'.join(word.lower() for word in words)
    
    @staticmethod
    def suggest_file_organization(files_created: list) -> Dict[str, list]:
        """Suggest how files should be organized"""
        organization = {
            'correct': [],
            'needs_moving': [],
            'needs_renaming': []
        }
        
        for file_path in files_created:
            # Check if it's a test file in components directory
            if file_path.startswith('components/') and ('test' in file_path.lower() or 'mock' in file_path.lower()):
                organization['needs_moving'].append({
                    'from': file_path,
                    'to': file_path.replace('components/', '__tests__/components/')
                })
            
            # Check for numbered files (like GET_1.tsx)
            elif re.search(r'_\d+\.(tsx?|js)$', file_path):
                organization['needs_renaming'].append({
                    'from': file_path,
                    'reason': 'Numbered files indicate duplicates or poor naming'
                })
            
            # Check for misplaced API files
            elif file_path.endswith('.tsx') and '/api/' in file_path:
                organization['needs_renaming'].append({
                    'from': file_path,
                    'to': file_path.replace('.tsx', '.ts'),
                    'reason': 'API routes should use .ts extension'
                })
            
            else:
                organization['correct'].append(file_path)
        
        return organization
    
    @staticmethod
    def generate_test_path(resource_name, component_type='component'):
        """Generate a standardized test file path"""
        if component_type == 'api':
            # API tests go next to the route file
            return f'app/api/{resource_name}/route.test.ts'
        elif component_type == 'service':
            return f'lib/{resource_name}Service.test.ts'
        elif component_type == 'page':
            return f'app/{resource_name}/page.test.tsx'
        else:
            # Component tests
            return f'components/{resource_name}/{resource_name}.test.tsx'
    
    @staticmethod
    def generate_docs_path(resource_name, doc_type='api'):
        """Generate a standardized documentation file path"""
        if doc_type == 'api':
            return f'project-plan/api-docs/{resource_name}-api.md'
        elif doc_type == 'feature':
            return f'project-plan/features/{resource_name}-feature.md'
        elif doc_type == 'component':
            return f'project-plan/components/{resource_name}-component.md'
        else:
            return f'project-plan/docs/{resource_name}.md'