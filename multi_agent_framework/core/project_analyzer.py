import os
import json
from typing import Dict, List, Optional, Tuple
from pathlib import Path

class ProjectAnalyzer:
    """Analyzes project structure to help agents integrate with existing files."""
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self._file_patterns = {
            'components': ['components/**/*.tsx', 'components/**/*.ts'],
            'pages': ['app/**/page.tsx', 'app/**/page.ts'],
            'api': ['app/api/**/*.ts'],
            'types': ['lib/types/**/*.ts', '**/*.d.ts'],
            'utils': ['lib/**/*.ts', 'utils/**/*.ts'],
            'docs': ['project-plan/**/*.md', 'docs/**/*.md'],
            'config': ['*.config.*', 'package.json', 'tsconfig.json']
        }
    
    def find_existing_files(self, category: str = None) -> Dict[str, List[str]]:
        """Find existing files by category."""
        patterns = self._file_patterns if not category else {category: self._file_patterns.get(category, [])}
        found_files = {}
        
        for cat, patterns_list in patterns.items():
            found_files[cat] = []
            for pattern in patterns_list:
                for file_path in self.project_root.glob(pattern):
                    if file_path.is_file():
                        found_files[cat].append(str(file_path.relative_to(self.project_root)))
        
        return found_files
    
    def suggest_target_file(self, task_description: str, file_type: str) -> Optional[str]:
        """Suggest where to place new code based on task description."""
        task_lower = task_description.lower()
        
        # Component placement logic
        if file_type == 'component':
            if 'rsvp' in task_lower:
                return 'components/rsvp'
            elif 'auth' in task_lower or 'login' in task_lower:
                return 'components/auth'
            elif 'admin' in task_lower:
                return 'components/admin'
            else:
                return 'components'
        
        # Page placement logic
        elif file_type == 'page':
            if 'event' in task_lower:
                return 'app/events'
            elif 'auth' in task_lower or 'login' in task_lower:
                return 'app/(auth)'
            elif 'admin' in task_lower:
                return 'app/(portal)/admin'
            else:
                return 'app'
        
        # API placement logic
        elif file_type == 'api':
            if 'event' in task_lower:
                return 'app/api/events'
            elif 'auth' in task_lower:
                return 'app/api/auth'
            else:
                return 'app/api'
        
        # Documentation placement
        elif file_type == 'docs':
            return 'project-plan'
        
        # Configuration placement
        elif file_type == 'config':
            return '.'
            
        return None
    
    def find_related_files(self, task_description: str) -> List[str]:
        """Find existing files related to the task."""
        task_lower = task_description.lower()
        keywords = self._extract_keywords(task_lower)
        
        related_files = []
        all_files = self.find_existing_files()
        
        for category, files in all_files.items():
            for file_path in files:
                file_lower = file_path.lower()
                if any(keyword in file_lower for keyword in keywords):
                    related_files.append(file_path)
        
        return related_files
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract relevant keywords from task description."""
        keywords = []
        
        # Feature-specific keywords
        feature_words = ['rsvp', 'event', 'auth', 'login', 'admin', 'calendar', 'user', 'profile']
        for word in feature_words:
            if word in text:
                keywords.append(word)
        
        # Component-specific keywords
        if any(word in text for word in ['component', 'form', 'button', 'modal']):
            keywords.extend(['component', 'tsx'])
        
        # API-specific keywords
        if any(word in text for word in ['api', 'endpoint', 'route']):
            keywords.extend(['api', 'route'])
        
        return keywords
    
    def should_modify_existing(self, task_description: str) -> Tuple[bool, Optional[str]]:
        """Determine if task should modify existing file vs create new one."""
        task_lower = task_description.lower()
        
        # Check for modification keywords
        modify_keywords = ['update', 'modify', 'add to', 'enhance', 'fix', 'refactor']
        is_modification = any(keyword in task_lower for keyword in modify_keywords)
        
        if is_modification:
            related_files = self.find_related_files(task_description)
            if related_files:
                # Return the most relevant file
                return True, related_files[0]
        
        return False, None
    
    def get_file_naming_convention(self, directory: str) -> Dict[str, str]:
        """Get naming conventions for the given directory."""
        conventions = {
            'components': 'PascalCase.tsx',
            'app': 'page.tsx or layout.tsx',
            'lib': 'camelCase.ts',
            'types': 'camelCase.ts or PascalCase.ts',
            'api': 'route.ts'
        }
        
        for pattern, convention in conventions.items():
            if pattern in directory:
                return {'pattern': convention, 'example': self._get_example_name(pattern)}
        
        return {'pattern': 'camelCase.ts', 'example': 'example.ts'}
    
    def _get_example_name(self, pattern: str) -> str:
        """Get example filename for pattern."""
        examples = {
            'components': 'EventCard.tsx',
            'app': 'page.tsx',
            'lib': 'utils.ts',
            'api': 'route.ts'
        }
        return examples.get(pattern, 'example.ts')